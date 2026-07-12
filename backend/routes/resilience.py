import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from services.resilience_service import predict_resilience
# Import specific schema dependencies if needed, or define them here as requested.
from project_schema import BuildingInput, ResilienceAssessmentResponse 

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resilience",
    tags=["Resilience Score engine"]
)

@router.post("/assess", response_model=ResilienceAssessmentResponse, summary="Return a building resilience score based on building details")
def calculate_pure_resilience(payload: BuildingInput, request: Request): 
    """Calculate building resilience score."""
    
    # Safely retrieve ML models from app state initialized in main.py
    model = request.state.model
    expected_features = request.state.expected_features

    try:
        if model is None or expected_features is None:
            raise HTTPException(
                status_code=500,
                detail="Resilience model is not initialized"
            )

        result = predict_resilience(
            payload=payload,
            model=model,
            expected_features=expected_features
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("Invalid resilience request: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Resilience assessment failed")
        raise HTTPException(status_code=500, detail="Resilience engine failed")