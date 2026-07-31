import logging
from fastapi import APIRouter, HTTPException
from services import calculate_hazard_pydantic
from project_schema import HazardInput, HazardReport

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/hazard",
    tags=["Hazard Engine"]
)

@router.post("/calculate", response_model=HazardReport, summary="Calculate environmental seismic hazard")
async def calculate_hazard_route(inputs: HazardInput):
    """
    Calculate environmental seismic hazard for a given location.

    The hazard engine degrades gracefully when external APIs (USGS, SoilGrids)
    fail — it returns a usable report with warnings rather than raising 500.
    """
    try:
        report = await calculate_hazard_pydantic(inputs)
        metadata = report.metadata or {}
        if metadata.get("degraded") or metadata.get("warnings"):
            logger.warning(
                "Hazard report completed with degradation flags: api_status=%s warnings=%s",
                metadata.get("api_status"),
                metadata.get("warnings"),
            )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Last-resort: engine is designed not to raise, but keep a safety net.
        logger.exception("Unexpected hazard engine failure after internal safeguards")
        raise HTTPException(
            status_code=500,
            detail=f"Seismic calculations failed: {e}",
        )
