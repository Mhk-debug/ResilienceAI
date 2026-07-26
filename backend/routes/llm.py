import logging
from fastapi import APIRouter, HTTPException, Request
from services.llm_services import create_llm_service
from project_schema import LLMAnalysisInput, LLMAnalysisOutput

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/llm",
    tags=["LLM Service"]
)

# Module-level service without retriever (backward compatible for direct imports)
llm_service = create_llm_service()


def _get_llm_service_with_retriever(request: Request):
    """
    Create an LLM service with the retriever from application state.
    
    Falls back to the module-level service if no retriever is configured.
    """
    retriever = getattr(request.app.state, "retriever", None)
    if retriever is not None:
        return create_llm_service(retriever=retriever)
    return llm_service


@router.post("/analysis", response_model=LLMAnalysisOutput, summary="Get explanations, recommendations and summary")
def analyze(input_data: LLMAnalysisInput, request: Request):
    try:
        service = _get_llm_service_with_retriever(request)
        result = service.analyze(input_data)
        return result.model_dump()
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")