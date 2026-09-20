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
from routes.auth import router as auth_router

# Ensure the schema exists on a fresh database (idempotent, no-op when
# tables already exist). The database must exist before boot.
from database.session import Base, engine

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAMAGE_BUNDLE_DIR = os.path.join(BASE_DIR, 'models', 'seismic_damage_v3')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles the boot initialization and resource cleanup cycles."""
    try:
        # Create any missing tables (users, assessments) so a fresh database
        # works without running an explicit migration/reset step first.
        Base.metadata.create_all(bind=engine)

        # Damage model: an ordinal grades-1-5 bundle (four boosters + metadata), not a bare
        # pickle. Loading is synchronous/blocking, which is fine for the startup phase.
        from services.damage_model import load_damage_model
        damage_model = load_damage_model(DAMAGE_BUNDLE_DIR)
        if damage_model is None:
            raise FileNotFoundError(
                f"Damage model bundle missing or unreadable at {DAMAGE_BUNDLE_DIR}"
            )

        logger.info(
            "Damage model loaded: %s with %d inputs.",
            damage_model.model_version,
            len(damage_model.features),
        )

        # Initialize the retriever (may be None — graceful degradation)
        retriever = _init_retriever()

        # Inject the model and retriever into app state for router access
        app.state.damage_model = damage_model
        app.state.retriever = retriever

        yield

    except Exception as e:
        logger.critical(f"Critical Boot Failure: {str(e)}", exc_info=True)
        raise e


def _init_retriever():
    """
    Initialize the knowledge retriever at startup.
    
    Returns a Retriever instance if the ChromaDB index exists,
    or None if retrieval dependencies are unavailable.
    
    Uses build_default_retriever() which handles all failure modes.
    """
    try:
        from services.retrieval import build_default_retriever
        retriever = build_default_retriever()
        if retriever is None:
            logger.info(
                "Knowledge retriever not available — "
                "assessments will proceed without RAG context. "
                "Run `python scripts/build_kb_index.py` to enable."
            )
        else:
            logger.info("Knowledge retriever initialized successfully.")
        return retriever
    except Exception as e:
        logger.warning(
            "Knowledge retriever initialization failed: %s. "
            "Assessments will proceed without RAG context.",
            e,
        )
        return None


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
app.include_router(auth_router)