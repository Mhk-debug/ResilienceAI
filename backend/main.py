import asyncio
import logging
import os
from re import A
import traceback
from typing import Any, Dict
from pydantic import BaseModel
import httpx
import joblib
import json
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from services.resilience_service import predict_resilience
from schema import AssessmentRequest, BuildingInput, HazardInput, HazardReport, LLMAnalysisInput, LLMAnalysisOutput, ResilienceAssessmentResponse, SaveAssessmentRequest
from services import calculate_hazard_pydantic
from services.llm_services import create_llm_service
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import engine
from database import Base, get_db

from database import *

# Setup logger configuration gracefully
logger = logging.getLogger(__name__)

BASE_API_URL = "http://127.0.0.1:8000"

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

# Define allowed origins
origins = [
    "http://localhost:3000",      # React/Next.js default
    "http://127.0.0.1:5500",     # Live Server default
    "https://yourdomain.com",    # Production domain
]

# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Allow specific origins
    allow_credentials=True,         # Allow cookies and credentials
    allow_methods=["*"],             # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],             # Allow all HTTP headers
)

llm_service = create_llm_service()


# =========================================================
# API ROUTES
# =========================================================

# ----------------------------------------------------------------
# Unified Orchestration Route
# ----------------------------------------------------------------
@app.post(
    "/api/assessment/process",
    status_code=status.HTTP_201_CREATED,
    summary="Orchestrate full resilience evaluation and save to database"
)
async def process_assessment(
    payload: AssessmentRequest,
    request: Request
):

    try:
        # -----------------------------
        # Create inputs
        # -----------------------------

        hazard_input_payload = HazardInput(
            latitude=payload.latitude,
            longitude=payload.longitude,
            search_radius_km=100,
            historical_years=50,
            minimum_magnitude=4.5,
        )


        building_fields = payload.model_dump(
            exclude={
                "latitude",
                "longitude"
            }
        )


        building_input_payload = BuildingInput(
            **building_fields
        )


        # -----------------------------
        # Run engines concurrently
        # -----------------------------

        building_task = asyncio.to_thread(
            predict_resilience,
            payload=building_input_payload,
            model=model,
            expected_features=expected_features
        )


        hazard_task = asyncio.create_task(
            calculate_hazard_pydantic(
                inputs=hazard_input_payload
            )
        )


        building_data, hazard_data = await asyncio.gather(
            building_task,
            hazard_task
        )


        # -----------------------------
        # Convert Pydantic models
        # -----------------------------

        building_json = building_data.model_dump(mode="json")
        hazard_json = hazard_data.model_dump(mode="json")


        # -----------------------------
        # LLM analysis
        # -----------------------------

        async with httpx.AsyncClient() as client:


            llm_res = await client.post(

                f"{BASE_API_URL}/api/llm/analysis",

                json={

                    "building_context":
                        building_json[
                            "building_llm_context"
                        ],

                    "environmental_context":
                        hazard_json[
                            "environmental_context"
                        ]

                },

                timeout=30
            )


            llm_res.raise_for_status()


            llm_data = llm_res.json()



            # -----------------------------
            # Save database
            # -----------------------------

            db_save_res = await client.post(

                f"{BASE_API_URL}/api/assessment/save",

                json={

                    "building":
                        building_json,

                    "hazard":
                        hazard_json,

                    "llm":
                        llm_data

                },

                timeout=30

            )


            db_save_res.raise_for_status()


            final_data = db_save_res.json()


        return {

            "success": True,

            "assessment_id":
                final_data.get(
                    "assessment_id"
                )

        }


    except httpx.HTTPError as e:

        raise HTTPException(
            status_code=502,
            detail=f"Internal service communication failed: {str(e)}"
        )


    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post(
    "/api/assessment/save",
    tags=["Database"],
    status_code=status.HTTP_201_CREATED,
    summary="Persist a complete earthquake risk assessment",
    description=(
        "Stores a completed earthquake risk assessment in the database. "
        "Frequently queried metadata such as location and scores are stored "
        "as relational columns for efficient searching, while the complete "
        "Building, Hazard and LLM outputs are preserved as JSONB documents."
    ),
) 
async def save_assessment(
    request: SaveAssessmentRequest,
    db: Session = Depends(get_db),
):
    """
    Persists the complete assessment.

    Stored relational fields
    ------------------------
    • Place name
    • Latitude
    • Longitude
    • Resilience Score
    • Hazard Score
    • Hazard Level
    • Model Version
    • Execution Time

    Stored JSONB blobs
    ------------------
    • Complete Building response
    • Complete Hazard response
    • Complete LLM response
    """

    try:

        building = request.building.model_dump(mode="json")
        hazard = request.hazard.model_dump(mode="json")
        llm = request.llm.model_dump(mode="json")

        location = hazard["location"]
        hazard_metrics = hazard["hazard"]
        metadata = hazard.get("metadata", {})

        assessment = Assessment(
            # -------------------------
            # Searchable metadata
            # -------------------------

            latitude=location["latitude"],
            longitude=location["longitude"],

            resilience_score=building["resilience_score"],

            hazard_score=hazard_metrics["overall_score"],
            hazard_level=hazard_metrics["hazard_level"],

            model_version=metadata.get("model_version"),

            execution_time_seconds=metadata.get(
                "execution_time_seconds"
            ),

            # -------------------------
            # Complete responses
            # -------------------------

            building=building,
            hazard=hazard,
            llm=llm,
        )

        db.add(assessment)

        db.commit()

        db.refresh(assessment)

        logger.info(
            "Assessment %s successfully persisted.",
            assessment.id,
        )

        return {
            "status": "success",
            "message": "Assessment successfully saved.",
            "assessment_id": str(assessment.id),
            "created_at": assessment.created_at.isoformat(),
        }

    except SQLAlchemyError:

        db.rollback()

        logger.exception("Database transaction failed.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist assessment.",
        )

    except Exception:

        db.rollback()

        logger.exception("Unexpected server exception.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected internal server error.",
        )

@app.post(
    "/api/llm/analysis",
    response_model=LLMAnalysisOutput,
    tags=["LLM Service"],
    summary="Get explanations, recommendations and summary"
)
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
async def calculate_hazard_route(inputs: HazardInput):  # CHANGED: Switched from 'async def' to 'def'
    """Calculate environmental seismic hazard for a given location."""
    try:
        return await calculate_hazard_pydantic(inputs)
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


@app.post(
    "/api/resilience/assess", 
    response_model=ResilienceAssessmentResponse,
    tags=["Resilience Score engine"],
    summary="Return a building resilience score based on building details"
)
def calculate_pure_resilience(payload: BuildingInput, request: Request): 
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

        logger.warning(
            "Invalid resilience request: %s",
            str(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


    except Exception as e:

        logger.exception(
            "Resilience assessment failed"
        )

        raise HTTPException(
            status_code=500,
            detail="Resilience engine failed"
        )