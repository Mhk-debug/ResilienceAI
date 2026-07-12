import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import calculate_hazard_pydantic
from project_schema import HazardInput, HazardReport

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/hazard",
    tags=["Hazard Engine"]
)

@router.post("/calculate", response_model=HazardReport, summary="Calculate environmental seismic hazard")
async def calculate_hazard_route(inputs: HazardInput):
    """Calculate environmental seismic hazard for a given location."""
    try:
        return await calculate_hazard_pydantic(inputs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error executing hazard engine")
        raise HTTPException(status_code=500, detail=f"Seismic calculations failed: {str(e)}")