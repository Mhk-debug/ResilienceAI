import asyncio
import logging
import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import get_db, Assessment
from project_schema import AssessmentIDResponse, AssessmentRequest, BuildingInput, HazardInput, SaveAssessmentRequest, LLMAnalysisInput

# Direct imports from other routers/services to avoid internal httpx calls
from routes.resilience import calculate_pure_resilience
from routes.hazard import calculate_hazard_route
from routes.llm import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/assessment",
    tags=["Orchestration", "Database"]
)

from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="resilience-ai")

async def get_place_name(
    latitude: float,
    longitude: float,
) -> str | None:
    location = await asyncio.to_thread(
        geolocator.reverse,
        (latitude, longitude),
    )

    return getattr(location, "address", None) if location else None

@router.post("/save", status_code=status.HTTP_201_CREATED, summary="Persist a complete earthquake risk assessment")
async def save_assessment(request: SaveAssessmentRequest, db: Session = Depends(get_db)):
    """Persists the complete assessment into relational columns and JSONB documents."""
    try:
        building = request.building.model_dump(mode="json")
        hazard = request.hazard.model_dump(mode="json")
        llm = request.llm.model_dump(mode="json")
        profile = request.profile.model_dump(mode="json")

        location = hazard["location"]
        hazard_metrics = hazard["hazard"]
        metadata = hazard.get("metadata", {})
        
        place_name = await get_place_name(
            location["latitude"],
            location["longitude"],
        )

        assessment = Assessment(
            latitude=location["latitude"],
            longitude=location["longitude"],
            place_name=place_name,
            resilience_score=building["resilience_score"],
            hazard_score=hazard_metrics["overall_score"],
            hazard_level=hazard_metrics["hazard_level"],
            model_version=metadata.get("model_version"),
            execution_time_seconds=metadata.get("execution_time_seconds"),
            profile=profile,
            building=building,
            hazard=hazard,
            llm=llm,
        )

        db.add(assessment)
        db.commit()
        db.refresh(assessment)

        logger.info("Assessment %s successfully persisted.", assessment.id)

        return {
            "status": "success",
            "message": "Assessment successfully saved.",
            "assessment_id": str(assessment.id),
            "created_at": assessment.created_at.isoformat(),
        }

    except SQLAlchemyError:
        print(traceback.format_exc())
        db.rollback()
        logger.exception("Database transaction failed.")
        raise HTTPException(status_code=500, detail="Failed to persist assessment.")
    except Exception:
        print(traceback.format_exc())
        db.rollback()
        logger.exception("Unexpected server exception.")
        raise HTTPException(status_code=500, detail="Unexpected internal server error.")


@router.post("/process", status_code=status.HTTP_201_CREATED, summary="Orchestrate full resilience evaluation and save to database")
async def process_assessment(payload: AssessmentRequest, request: Request, db: Session = Depends(get_db)):
    try:
        # 1. Create Inputs
        hazard_input_payload = HazardInput(
            latitude=payload.latitude,
            longitude=payload.longitude,
            search_radius_km=100,
            historical_years=50,
            minimum_magnitude=4.5,
        )

        building_fields = payload.model_dump(exclude={"latitude", "longitude"})
        building_input_payload = BuildingInput(**building_fields)

        # 2. Run engines concurrently via internal Python execution (No HTTP overhead)
        building_task = asyncio.to_thread(
            calculate_pure_resilience, 
            payload=building_input_payload, 
            request=request
        )
        
        hazard_task = asyncio.create_task(
            calculate_hazard_route(inputs=hazard_input_payload)
        )

        building_data, hazard_data = await asyncio.gather(building_task, hazard_task)

        building_json = building_data.model_dump(mode="json")
        hazard_json = hazard_data.model_dump(mode="json")

        # 3. LLM analysis via direct service invocation
        llm_input = LLMAnalysisInput(
            building_context=building_json["building_llm_context"],
            environmental_context=hazard_json["environmental_context"]
        )
        
        # Assuming analyze is synchronous, wrap in to_thread
        llm_data = await asyncio.to_thread(llm_service.analyze, llm_input)

        # 4. Save to database via internal function call
        save_payload = SaveAssessmentRequest(
            profile=building_input_payload,
            building=building_data,
            hazard=hazard_data,
            llm=llm_data
        )
        
        final_data = await save_assessment(request=save_payload, db=db)

        return {
            "success": True,
            "assessment_id": final_data.get("assessment_id")
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{assessment_id}",
    response_model=AssessmentIDResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific assessment by its UUID",
    description="Fetches a complete assessment record from the database including all metadata and JSONB payloads."
)
def get_assessment_by_id(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> Assessment:
    """
    Fetch an individual assessment row based on its ID.
    
    Args:
        assessment_id (uuid.UUID): The unique identifier of the assessment.
        db (Session): The SQLAlchemy database session.
        
    Returns:
        Assessment: The SQLAlchemy model instance (FastAPI auto-converts this to AssessmentResponse).
    """
    try:
        # Query the database for the specific ID
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

        # Handle case where ID does not exist
        if assessment is None:
            logger.warning(f"Assessment fetch failed: UUID {assessment_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment with ID {assessment_id} not found."
            )

        return assessment

    except SQLAlchemyError as e:
        # Catch database transaction/connection issues
        logger.exception(f"Database error while fetching assessment {assessment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal database error occurred while fetching the assessment."
        )