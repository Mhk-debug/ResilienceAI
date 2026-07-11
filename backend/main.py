import logging
import os
import joblib
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routes.resilience import router as resilience_router
from routes.hazard import router as hazard_router
from routes.llm import router as llm_router
from routes.assessment import router as assessment_router

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'seismic_resilience_xgb.pkl')
SCHEMA_PATH = os.path.join(BASE_DIR, 'models', 'model_features.json')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles the boot initialization and resource cleanup cycles."""
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
        
        # Inject models into app state to be accessed by routers safely
        yield {
            "model": model, 
            "expected_features": expected_features
        }
    except Exception as e:
        logger.critical(f"Critical Boot Failure: {str(e)}", exc_info=True)
        raise e

# Initialize application
app = FastAPI(
    title="ResilienceAI - Complete Risk Engine Suite", 
    version="1.2.0", 
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:3000",      # React/Next.js default
    "http://127.0.0.1:5500",      # Live Server default
    "https://yourdomain.com",     # Production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(resilience_router)
app.include_router(hazard_router)
app.include_router(llm_router)
app.include_router(assessment_router)