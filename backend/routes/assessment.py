import asyncio
import json
import logging
import time
import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import get_db, Assessment
from database.models import User
from services.auth import get_current_user_from_cookie
from project_schema import AssessmentIDResponse, AssessmentRequest, BuildingInput, HazardInput, SaveAssessmentRequest, LLMAnalysisInput

# Direct imports from other routers/services to avoid internal httpx calls
from routes.resilience import calculate_pure_resilience
from routes.hazard import calculate_hazard_route
from services.llm_services import create_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assessment",
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
async def save_assessment(
    request: SaveAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Persists the complete assessment into relational columns and JSONB documents."""
    try:
        building = request.building.model_dump(mode="json")
        hazard = request.hazard.model_dump(mode="json")
        llm = request.llm.model_dump(mode="json")
        profile = request.profile.model_dump(mode="json")
        evidence = {
            k: v.model_dump(mode="json") for k, v in request.evidence.items()
        } if request.evidence else {}

        # Merge evidence into the llm JSONB for storage
        llm["evidence"] = evidence

        location = hazard["location"]
        hazard_metrics = hazard["hazard"]
        metadata = hazard.get("metadata", {})
        execution_time = request.execution_time_seconds
        
        place_name = await get_place_name(
            location["latitude"],
            location["longitude"],
        )

        assessment = Assessment(
            user_id=current_user.id,
            latitude=location["latitude"],
            longitude=location["longitude"],
            place_name=place_name,
            resilience_score=building["resilience_score"],
            hazard_score=hazard_metrics["overall_score"],
            hazard_level=hazard_metrics["hazard_level"],
            model_version=metadata.get("model_version"),
            execution_time_seconds=execution_time,
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


@router.post(
    "/process",
    summary="Orchestrate full resilience evaluation and stream progress"
)
async def process_assessment(
    payload: AssessmentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):

    def sse_event(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    # Capture retriever from app state before entering the generator
    retriever = getattr(request.app.state, "retriever", None)
    llm_service = create_llm_service(retriever=retriever)

    async def assessment_generator():

        try:
            # ---------------------------------------------------------
            # INITIALIZATION
            # ---------------------------------------------------------
            yield sse_event({
                "type": "stage_started",
                "stage": "initializing",
                "status": "Preparing your assessment..."
            })

            hazard_input_payload = HazardInput(
                latitude=payload.latitude,
                longitude=payload.longitude,
                search_radius_km=100,
                historical_years=50,
                minimum_magnitude=4.5,
            )

            building_fields = payload.model_dump(
                exclude={"latitude", "longitude"}
            )

            building_input_payload = BuildingInput(
                **building_fields
            )

            yield sse_event({
                "type": "stage_completed",
                "stage": "initializing"
            })

            # ---------------------------------------------------------
            # START PARALLEL ANALYSIS
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_started",
                "stage": "resilience",
                "status": "Assessing building resilience..."
            })

            yield sse_event({
                "type": "stage_started",
                "stage": "hazard",
                "status": "Running environmental hazard engine..."
            })

            t0 = time.time()
            building_task = asyncio.to_thread(
                calculate_pure_resilience,
                payload=building_input_payload,
                request=request
            )

            hazard_task = asyncio.create_task(
                calculate_hazard_route(
                    inputs=hazard_input_payload
                )
            )

            building_data, hazard_data = await asyncio.gather(
                building_task,
                hazard_task
            )
            parallel_elapsed = time.time() - t0

            # ---------------------------------------------------------
            # BOTH PARALLEL TASKS COMPLETE
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_completed",
                "stage": "resilience"
            })

            yield sse_event({
                "type": "stage_completed",
                "stage": "hazard"
            })

            # ---------------------------------------------------------
            # LLM ANALYSIS
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_started",
                "stage": "llm",
                "status": "Generating AI feedback..."
            })

            building_json = building_data.model_dump(
                mode="json"
            )

            hazard_json = hazard_data.model_dump(
                mode="json"
            )

            llm_input = LLMAnalysisInput(
                building_context=building_json[
                    "building_llm_context"
                ],
                environmental_context=hazard_json[
                    "environmental_context"
                ]
            )

            t1 = time.time()
            llm_data, evidence_map = await asyncio.to_thread(
                llm_service.analyze,
                llm_input
            )
            llm_elapsed = time.time() - t1

            # Total core work: parallel (resilience + hazard) + LLM
            total_work_elapsed = parallel_elapsed + llm_elapsed

            yield sse_event({
                "type": "stage_completed",
                "stage": "llm"
            })

            # ---------------------------------------------------------
            # SAVE TO DATABASE
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_started",
                "stage": "saving",
                "status": "Saving your assessment..."
            })

            save_payload = SaveAssessmentRequest(
                profile=building_input_payload,
                building=building_data,
                hazard=hazard_data,
                llm=llm_data,
                evidence=evidence_map,
                execution_time_seconds=total_work_elapsed,
            )

            t2 = time.time()
            final_data = await save_assessment(
                request=save_payload,
                db=db,
                current_user=current_user,
            )
            save_elapsed = time.time() - t2

            yield sse_event({
                "type": "stage_completed",
                "stage": "saving"
            })

            # ---------------------------------------------------------
            # COMPLETE
            # ---------------------------------------------------------

            total_elapsed = time.time() - t0

            logger.info(
                "Assessment complete | "
                "parallel=%.2fs | "
                "llm=%.2fs | "
                "save=%.2fs | "
                "total=%.2fs | "
                "resilience=%.2f | "
                "hazard=%.2f | "
                "rag=%s",
                parallel_elapsed,
                llm_elapsed,
                save_elapsed,
                total_elapsed,
                building_data.resilience_score,
                hazard_data.hazard.get("overall_score", 0),
                "enabled" if retriever is not None else "disabled",
            )

            yield sse_event({
                "type": "complete",
                "assessment_id": final_data.get(
                    "assessment_id"
                )
            })

        except Exception as e:

            traceback.print_exc()

            yield sse_event({
                "type": "error",
                "detail": str(e)
            })

    return StreamingResponse(
        assessment_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List all assessments for the authenticated user",
    description="Returns lightweight assessment summaries (no JSONB blobs) ordered by creation date descending."
)
def list_user_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Returns a lightweight list of assessments belonging to the current user,
    ordered by created_at descending. Omits the bulky JSONB columns.
    """
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(a.id),
            "created_at": a.created_at.isoformat(),
            "place_name": a.place_name,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "resilience_score": a.resilience_score,
            "hazard_score": a.hazard_score,
            "hazard_level": a.hazard_level,
        }
        for a in assessments
    ]


@router.get(
    "/{assessment_id}",
    response_model=AssessmentIDResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a specific assessment by its UUID",
    description="Fetches a complete assessment record from the database including all metadata and JSONB payloads."
)
def get_assessment_by_id(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
) -> Assessment:
    """
    Fetch an individual assessment row based on its ID.
    Verifies the assessment belongs to the authenticated user.
    
    Args:
        assessment_id (uuid.UUID): The unique identifier of the assessment.
        db (Session): The SQLAlchemy database session.
        current_user (User): The authenticated user from the session cookie.
        
    Returns:
        Assessment: The SQLAlchemy model instance (FastAPI auto-converts this to AssessmentResponse).
    """
    try:
        # Query the database for the specific ID
        print("id", assessment_id)
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()

        # Handle case where ID does not exist
        if assessment is None:
            logger.warning(f"Assessment fetch failed: UUID {assessment_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment with ID {assessment_id} not found."
            )

        # Enforce ownership: only the user who created the assessment may view it
        if assessment.user_id != current_user.id:
            logger.warning(
                f"User {current_user.id} attempted to access assessment {assessment_id} "
                f"owned by user {assessment.user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this assessment."
            )

        return assessment

    except SQLAlchemyError as e:
        # Catch database transaction/connection issues
        logger.exception(f"Database error while fetching assessment {assessment_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal database error occurred while fetching the assessment."
        )