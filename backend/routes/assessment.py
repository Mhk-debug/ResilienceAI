import asyncio
import json
import logging
import time
import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
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
    """Reverse-geocode a coordinate. Returns None on any failure so the
    assessment can still be saved (place_name is stored nullable).

    The wait is hard-bounded: geopy's own ``timeout`` only covers the socket read, so on a host
    that blackholes DNS/connect requests (nominatim.openstreetmap.org is unreachable from this
    network) a bare call stalls the whole save step for a minute or more. The thread is abandoned
    rather than cancelled — it cannot be cancelled — but the request no longer waits on it.
    """
    try:
        location = await asyncio.wait_for(
            asyncio.to_thread(
                geolocator.reverse,
                (latitude, longitude),
                timeout=3,
            ),
            timeout=5.0,
        )
        return getattr(location, "address", None) if location else None
    except Exception:
        logger.warning(
            "Reverse geocoding failed or timed out for (%s, %s); storing without a place name.",
            latitude,
            longitude,
        )
        return None


def extract_governing_distance(hazard_data) -> float | None:
    """Epicentral distance (km) to the event that governs the site's ground motion.

    The damage model's only site term was trained as the distance to the event that shook the
    building (the 2015 Gorkha event for every training row), so at inference it takes the same
    quantity: the distance to the dominant event the hazard engine used for `estimated_mmi` and
    `estimated_pga_g`. When the catalogue holds no significant event inside the search radius the
    closest catalogued event is used; None is returned only when there is nothing to measure to.
    """
    try:
        env = hazard_data.environmental_context
        if not isinstance(env, dict):
            env = env.model_dump(mode="json")
        event = (env.get("ground_motion") or {}).get("governing_event")
        if event and event.get("distance_km") is not None:
            return float(event["distance_km"])

        stats = hazard_data.statistics
        if not isinstance(stats, dict):
            stats = stats.model_dump(mode="json")
        closest = stats.get("closest_earthquake_km")
        if closest is not None:
            return float(closest)
    except Exception:
        logger.warning(
            "Could not derive the governing-event distance from the hazard report; "
            "the damage model will run without a site term.",
            exc_info=True,
        )
    return None

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
            model_version=building.get("model_version") or metadata.get("model_version"),
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
            # HAZARD FIRST, THEN BUILDING
            # The damage model conditions on the site's governing event distance, so the hazard
            # engine has to resolve before the building can be scored. The two used to run in
            # parallel; the dependency is one-directional and cheap (the call is network-bound).
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_started",
                "stage": "hazard",
                "status": "Running environmental hazard engine..."
            })

            t0 = time.time()
            hazard_data = await calculate_hazard_route(
                inputs=hazard_input_payload
            )

            yield sse_event({
                "type": "stage_completed",
                "stage": "hazard"
            })

            yield sse_event({
                "type": "stage_started",
                "stage": "resilience",
                "status": "Assessing building resilience..."
            })

            epi_distance_km = extract_governing_distance(hazard_data)

            building_data = await asyncio.to_thread(
                calculate_pure_resilience,
                payload=building_input_payload,
                request=request,
                epi_distance_km=epi_distance_km
            )

            parallel_elapsed = time.time() - t0

            # ---------------------------------------------------------
            # BOTH TASKS COMPLETE
            # ---------------------------------------------------------

            yield sse_event({
                "type": "stage_completed",
                "stage": "resilience"
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


# ---------------------------------------------------------------------------
# Assessment history endpoint
# ---------------------------------------------------------------------------
#
# Dedicated, paginated history view for the assessment history page.
# Returns a stable response shape ({ items, total, limit, offset }) that the
# frontend can render with proper "Showing X of Y" labels, ordering controls,
# and infinite-scroll / "load more" pagination in the future.
#
# The bare-array response from `list_user_assessments` (above) is preserved
# for backward compatibility with the home page redirect logic that still
# reads `assessments[0]?.id`.
# ---------------------------------------------------------------------------


class AssessmentSummaryItem(BaseModel):
    """A single lightweight row in the assessment history list."""

    id: str
    created_at: str
    place_name: str | None = None
    latitude: float
    longitude: float
    resilience_score: float
    hazard_score: float
    hazard_level: str


class AssessmentHistoryResponse(BaseModel):
    """Paginated response wrapper for the assessment history page."""

    items: List[AssessmentSummaryItem]
    total: int
    limit: int
    offset: int


@router.get(
    "/history",
    response_model=AssessmentHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Paginated assessment history for the authenticated user",
    description=(
        "Returns the current user's assessments as a paginated list ordered by "
        "creation date descending. The response includes the total count so the "
        "UI can render 'Showing X of Y' labels and 'Load more' pagination."
    ),
)
def list_assessment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    limit: int = Query(20, ge=1, le=100, description="Page size (1-100)"),
    offset: int = Query(0, ge=0, description="Number of rows to skip"),
) -> AssessmentHistoryResponse:
    """
    Paginated history of assessments belonging to the current user.

    Lightweight payload — JSONB columns (profile, building, hazard, llm) are
    intentionally excluded; the detail page fetches them on demand.
    """
    base_query = db.query(Assessment).filter(
        Assessment.user_id == current_user.id
    )

    total = base_query.count()

    rows = (
        base_query.order_by(Assessment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        AssessmentSummaryItem(
            id=str(a.id),
            created_at=a.created_at.isoformat(),
            place_name=a.place_name,
            latitude=a.latitude,
            longitude=a.longitude,
            resilience_score=a.resilience_score,
            hazard_score=a.hazard_score,
            hazard_level=a.hazard_level,
        )
        for a in rows
    ]

    return AssessmentHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


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