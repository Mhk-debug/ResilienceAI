import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Query

from services.resilience_service import predict_resilience
from project_schema import BuildingInput, ResilienceAssessmentResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resilience",
    tags=["Resilience Score engine"]
)


@router.post("/assess", response_model=ResilienceAssessmentResponse, summary="Return a building resilience score based on building details")
def calculate_pure_resilience(
    payload: BuildingInput,
    request: Request,
    epi_distance_km: Optional[float] = Query(
        None,
        description="Epicentral distance in km to the governing event (the damage model's site term). "
                    "Omit to score without a site term — the pipeline supplies it from the hazard engine."
    ),
):
    """Calculate the building damage/resilience distribution.

    The damage model is an ordinal cumulative-link decomposition over grades 1-5; this route is the
    standalone entry point. The full assessment pipeline calls it with the hazard engine's governing
    event distance so the score is conditioned on the site's shaking.
    """

    damage_model = getattr(request.app.state, "damage_model", None)

    try:
        if damage_model is None:
            raise HTTPException(
                status_code=500,
                detail="Damage model is not initialized"
            )

        result = predict_resilience(
            payload=payload,
            damage_model=damage_model,
            epi_distance_km=epi_distance_km
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid resilience request: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Resilience assessment failed")
        raise HTTPException(status_code=500, detail="Resilience engine failed")
