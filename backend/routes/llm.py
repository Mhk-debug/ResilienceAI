import logging
from fastapi import APIRouter, HTTPException
from services.llm_services import create_llm_service
from schema import LLMAnalysisInput, LLMAnalysisOutput

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/llm",
    tags=["LLM Service"]
)

# Instantiate LLM service strictly for this module
llm_service = create_llm_service()

@router.post("/analysis", response_model=LLMAnalysisOutput, summary="Get explanations, recommendations and summary")
def analyze(input_data: LLMAnalysisInput):
    try:
        result = llm_service.analyze(input_data)
        return result.model_dump()
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")