import logging
import os
import joblib
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from project_schema import BuildingInput, HazardInput, HazardReport, LLMAnalysisInput, ResilienceAssessmentResponse, BuildingLLMContext
from services import process_and_align_inference_data, calculate_resilience_score, calculate_hazard_pydantic
from richtor_mappings import decode_building_feature
from services.llm_services import create_llm_service

# Setup logger configuration gracefully
logger = logging.getLogger(__name__)

# Resolve model path roots dynamically 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'seismic_resilience_xgb.pkl')
SCHEMA_PATH = os.path.join(BASE_DIR, 'models', 'model_features.json')

# Persistent runtime storage variables
model = None
expected_features = None

# 1. Modern Lifespan Manager replacing deprecated on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles the boot initialization and resource cleanup cycles."""
    global model, expected_features
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCHEMA_PATH):
            raise FileNotFoundError(
                f"Required files missing in artifacts space. Check {MODEL_PATH} or {SCHEMA_PATH}"
            )
        
        # joblib loading is synchronous/blocking, perfect for startup phase
        model = joblib.load(MODEL_PATH)
        with open(SCHEMA_PATH, 'r') as f:
            expected_features = json.load(f)
            
        logger.info(f"Artifacts loaded successfully. Ready to parse {len(expected_features)} inputs.")
    except Exception as e:
        logger.critical(f"Critical Boot Failure: {str(e)}", exc_info=True)
        raise e
    
    yield
    # Cleanup logic can go here if required later (e.g., closing DB pools)

# Initialize application with lifespan
app = FastAPI(title="ResilienceAI - Complete Risk Engine Suite", version="1.2.0", lifespan=lifespan)
llm_service = create_llm_service()


# =========================================================
# API ROUTES
# =========================================================

@app.post("/api/llm/analysis")
def analyze(input_data: LLMAnalysisInput):
    try:
        result = llm_service.analyze(input_data)
        return result.model_dump()
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM analysis failed: {str(e)}"
        )


@app.post(
    "/api/hazard/calculate",
    response_model=HazardReport,
    tags=["Hazard Engine"],
    summary="Calculate environmental seismic hazard"
)
def calculate_hazard_route(inputs: HazardInput):  # CHANGED: Switched from 'async def' to 'def'
    """Calculate environmental seismic hazard for a given location."""
    try:
        return calculate_hazard_pydantic(inputs)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Error executing hazard engine")
        raise HTTPException(
            status_code=500,
            detail=f"Seismic calculations failed: {str(e)}"  # Kept string uniform with other 500s
        )


@app.post("/api/resilience/assess", response_model=ResilienceAssessmentResponse)
def calculate_pure_resilience(payload: BuildingInput):  # CHANGED: Switched from 'async def' to 'def'
    """Ingests structural attributes and outputs a ML-driven resilience score."""
    if model is None or expected_features is None:
        raise HTTPException(
            status_code=500,
            detail="Inference engine is uninitialized."
        )

    try:
        raw_input = payload.model_dump()

        # Heavy CPU data manipulation & model inference run safely inside a worker thread pool
        df_aligned = process_and_align_inference_data(
            raw_input_dict=raw_input,
            trained_model=model,
            expected_features_list=expected_features
        )

        resilience_score = calculate_resilience_score(model, df_aligned)

        # Convert encoded categorical values into human-readable descriptions
        building_llm_context_data = {
            "structural": {
                "floors": raw_input.get("count_floors_pre_eq"),
                "age_years": raw_input.get("age"),
                "floor_area_ratio": raw_input.get("area_percentage"),
                "height_ratio": raw_input.get("height_percentage")
            },
            "material": {
                "roof_type": decode_building_feature("roof_type", str(raw_input.get("roof_type") or "")),
                "foundation_type": decode_building_feature("foundation_type", str(raw_input.get("foundation_type") or "")),
                "ground_floor_type": decode_building_feature("ground_floor_type", str(raw_input.get("ground_floor_type") or ""))
            },
            "substructure": {
                "mud_mortar_stone": bool(raw_input.get("has_superstructure_mud_mortar_stone")),
                "cement_brick": bool(raw_input.get("has_superstructure_cement_mortar_brick")),
                "rc_engineered": bool(raw_input.get("has_superstructure_rc_engineered"))
            }
        }
        building_llm_context = BuildingLLMContext.model_validate(building_llm_context_data)

        return ResilienceAssessmentResponse(
            status="success",
            resilience_score=round(resilience_score, 2),
            building_llm_context=building_llm_context
        )

    except Exception as e:
        logger.exception("Internal mathematical processing exception")
        raise HTTPException(
            status_code=500,
            detail=f"Internal mathematical processing exception: {str(e)}"
        )