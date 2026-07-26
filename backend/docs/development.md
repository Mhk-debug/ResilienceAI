# Development Guide

> **Local setup, dependencies, running, testing, and debugging for the ResilienceAI backend**

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| pip | 23+ | Package management |
| virtualenv/venv | Built-in | Isolated environment |
| PostgreSQL | 15+ (Neon) | Primary database |
| Git | 2.40+ | Version control |
| Node.js | 20+ (LTS) | Frontend (separate) |

---

## Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd ResilienceAI
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt

# Optional: retrieval dependencies (ChromaDB + Sentence Transformers)
pip install chromadb sentence-transformers
```

### 4. Configure Environment Variables
Create `.env` in project root (`ResilienceAI/.env`):
```env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
GEMINI_API_KEY=your-gemini-api-key
```

**Required Variables:**
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:***@ep-xxx.neon.tech/neondb?sslmode=require` |
| `GEMINI_API_KEY` | Google AI Studio API key | `AIzaSy...` |

### 5. Initialize Database
```bash
# Tables created automatically on first run via SQLAlchemy
# Or manually:
python -c "from database.session import engine, Base; Base.metadata.create_all(engine)"
```

### 6. Build Knowledge Base Index (for RAG)
```bash
python scripts/build_kb_index.py --verbose
```

---

## Running the Backend

### Development Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Access:**
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Production Server
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Running Tests

### All Tests
```bash
cd backend
pytest tests/ -v
```

### Specific Test Modules
```bash
# ML pipeline
pytest tests/test_resilience.py -v

# Hazard engine
pytest tests/test_hazard.py -v

# Retrieval system
pytest tests/test_retrieval.py -v

# LLM service
pytest tests/test_llm_service.py -v

# LLM + Retrieval integration
pytest tests/test_llm_retrieval_integration.py -v
```

### With Coverage
```bash
pytest tests/ --cov=services --cov=routes --cov=database -v
```

---

## Project Structure Reference

```
backend/
├── main.py                    # FastAPI app, lifespan, routers
├── project_schema.py          # All Pydantic models
├── richtor_mappings.py        # Feature code → description
├── requirements.txt           # Python dependencies
├── database/
│   ├── session.py            # SQLAlchemy engine, session
│   └── models.py             # Assessment ORM model
├── models/
│   ├── seismic_resilience_xgb.pkl
│   └── model_features.json
├── routes/
│   ├── assessment.py         # SSE pipeline orchestration
│   ├── resilience.py         # ML prediction endpoint
│   ├── hazard.py             # Hazard calculation endpoint
│   └── llm.py                # LLM analysis endpoint
├── services/
│   ├── pipeline.py           # Feature engineering
│   ├── resilience_engine.py  # Score calculation
│   ├── resilience_service.py # ML orchestration
│   ├── llm_services.py       # Gemini + RAG
│   ├── hazard_engine/        # Hazard modules
│   │   ├── engine.py
│   │   ├── usgs.py
│   │   ├── soil.py
│   │   ├── faults.py
│   │   ├── scoring.py
│   │   ├── recurrence.py
│   │   ├── calibration.py
│   │   ├── weights.py
│   │   ├── statistics.py
│   │   ├── shakemap.py
│   │   ├── utils.py
│   │   └── constants.py
│   └── retrieval/            # RAG modules
│       ├── retriever.py
│       ├── indexer.py
│       ├── embedder.py
│       ├── chunk_loader.py
│       └── query_builder.py
├── scripts/
│   ├── build_kb_index.py
│   ├── validate_pipeline.py
│   └── *.py                  # Calibration/debug
├── tests/
│   ├── test_resilience.py
│   ├── test_hazard.py
│   ├── test_retrieval.py
│   ├── test_llm_service.py
│   ├── test_llm_retrieval_integration.py
│   └── test_cities.py
└── docs/                     # This documentation
```

---

## Dependencies (`requirements.txt`)

```text
fastapi==0.115.0
uvicorn[standard]==0.34.0
pydantic==2.9.2
pydantic-settings==2.6.1
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
python-dotenv==1.0.1
joblib==1.4.2
numpy==2.1.3
pandas==2.2.3
scikit-learn==1.5.2
xgboost==2.1.3
google-genai==1.5.0
geopy==2.4.1
certifi==2024.12.14
httpx==0.28.1
PyYAML==6.0.2
owslib==0.30.0
rasterio==1.4.3
```

**Optional (RAG):**
```text
chromadb==0.5.5
sentence-transformers==3.1.1
```

---

## Debugging Tips

### 1. Enable Debug Logging
```bash
# Set log level
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

### 2. Inspect App State
```python
# In any route, access loaded resources:
model = request.app.state.model
features = request.app.state.expected_features
retriever = request.app.state.retriever

print(f"Model: {type(model)}")
print(f"Features: {len(features)}")
print(f"Retriever available: {retriever is not None}")
```

### 3. Test ML Pipeline In Isolation
```python
# scripts/debug_ml.py
import joblib
import json
from services.pipeline import process_and_align_inference_data
from services.resilience_engine import calculate_resilience_score

model = joblib.load("models/seismic_resilience_xgb.pkl")
with open("models/model_features.json") as f:
    features = json.load(f)

test_input = {
    "count_floors_pre_eq": 2,
    "age": 25,
    "area_sq_ft": 1200,
    "height_ft": 24,
    "foundation_type": "i",
    "roof_type": "q",
    "ground_floor_type": "x",
    "has_superstructure_mud_mortar_stone": 0,
    "has_superstructure_rc_engineered": 1,
    "has_superstructure_cement_mortar_brick": 0,
    "has_superstructure_rc_non_engineered": 0,
    "has_superstructure_adobe_mud": 0,
    "has_superstructure_timber": 0,
}

df = process_and_align_inference_data(test_input, model, features)
score = calculate_resilience_score(model, df)
print(f"Resilience Score: {score}")
```

### 4. Test Hazard Engine In Isolation
```python
# scripts/debug_hazard.py
import asyncio
from services.hazard_engine import calculate_hazard_pydantic
from project_schema import HazardInput

async def test():
    input_data = HazardInput(
        latitude=23.8103,
        longitude=90.4125,
        search_radius_km=100,
        historical_years=50,
        minimum_magnitude=4.5
    )
    result = await calculate_hazard_pydantic(input_data)
    print(f"Hazard Score: {result.hazard.overall_score}")
    print(f"Level: {result.hazard.hazard_level}")

asyncio.run(test())
```

### 5. Test Retrieval In Isolation
```python
# scripts/debug_retrieval.py
from services.retrieval import build_default_retriever
from project_schema import BuildingLLMContext, EnvironmentalContext

retriever = build_default_retriever()
if retriever:
    building = BuildingLLMContext(
        structural={"floors": 2, "age_years": 25, "floor_area_sq_feets": 1200, "height_feets": 24},
        material={"roof_type": "CGI", "foundation_type": "RC", "ground_floor_type": "RC"},
        substructure={"rc_engineered": True}
    )
    env = EnvironmentalContext(
        hazard_score=45.2, hazard_level="Moderate",
        historical_activity={"classification": "Moderate", "events_within_radius": 12},
        faults={"distance_km": 45.2, "classification": "Moderate Proximity"},
        soil={"classification": "Moderate Liquefaction Risk", "dominant_soil": "Silty Loam"},
        ground_motion={"estimated_mmi": 7.5, "estimated_pga_g": 0.18, "confidence": 0.95},
        summary=["Moderate hazard..."]
    )
    results = retriever.retrieve(building, env)
    for r in results:
        print(f"[{r.channel}] {r.chunk_id} (score={r.score:.3f})")
else:
    print("Retriever not available - run build_kb_index.py")
```

### 6. Test LLM Service In Isolation
```python
# scripts/debug_llm.py
from services.llm_services import create_llm_service
from services.retrieval import build_default_retriever
from project_schema import BuildingLLMContext, EnvironmentalContext, LLMAnalysisInput

retriever = build_default_retriever()
service = create_llm_service(retriever=retriever)

building = BuildingLLMContext(...)
env = EnvironmentalContext(...)
input_data = LLMAnalysisInput(building_context=building, environmental_context=env)

result, evidence = service.analyze(input_data)
print(f"Confidence: {result.confidence}")
print(f"Summary: {result.summary}")
print(f"Recommendations: {result.recommendations}")
print(f"Evidence: {list(evidence.keys())}")
```

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'services'`
**Cause:** Running from wrong directory.
**Fix:** Run from `backend/` directory or add to PYTHONPATH:
```bash
cd backend
python -m pytest tests/
# or
export PYTHONPATH=/path/to/ResilienceAI/backend:$PYTHONPATH
```

### Issue: `FileNotFoundError: models/seismic_resilience_xgb.pkl`
**Cause:** Model files missing or wrong working directory.
**Fix:** Ensure you're in `backend/` directory when running uvicorn.

### Issue: `DATABASE_URL environment variable is missing`
**Cause:** `.env` not loaded or missing.
**Fix:** 
```bash
# Check .env exists in project root
ls -la ../.env
# Verify content
cat ../.env
```

### Issue: `chromadb.errors.NotFoundError: Collection not found`
**Cause:** Index not built.
**Fix:**
```bash
python scripts/build_kb_index.py --force
```

### Issue: `Gemini API error: 429 Rate Limit`
**Cause:** API quota exceeded.
**Fix:** Wait and retry; implement caching for production.

### Issue: `USGS API timeout`
**Cause:** Network latency or USGS service slow.
**Fix:** Engine has 6s timeout and graceful degradation (continues with empty events).

### Issue: `SoilGrids WCS error`
**Cause:** Service unavailable or network issue.
**Fix:** Falls back to deterministic regional soil properties.

### Issue: `event loop blocked` / slow SSE
**Cause:** Sync calls in async context (e.g., `geopy` geocoding).
**Fix:** Use `asyncio.to_thread()` for blocking calls (already done for ML).

---

## Profiling & Performance

### Time Stage Execution
```python
# In routes/assessment.py, stages are timed:
t0 = time.time()
# ... stage ...
elapsed = time.time() - t0
logger.info(f"Stage took {elapsed:.2f}s")
```

### Memory Profiling
```bash
pip install memory-profiler
python -m memory_profiler scripts/validate_pipeline.py
```

### SQL Query Logging
```python
# In database/session.py, set echo=True for debugging:
engine = create_engine(DATABASE_URL, echo=True, ...)
```

---

## Adding New Features

### 1. New API Endpoint
```python
# routes/new_feature.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/new", tags=["New Feature"])

@router.get("/endpoint")
def new_endpoint():
    return {"message": "Hello"}

# In main.py:
from routes.new_feature import router as new_router
app.include_router(new_router)
```

### 2. New Pydantic Model
```python
# project_schema.py
class NewModel(BaseModel):
    field: str
    value: float = Field(..., ge=0)
```

### 3. New Hazard Component
1. Add module in `services/hazard_engine/`
2. Import in `engine.py`
3. Add to `calculate_hazard()` flow
4. Update `calibration.py` for score combination

### 4. New Knowledge Category
1. Add to `VALID_CATEGORIES` in `chunk_loader.py`
2. Create markdown files in `data/knowledge/new_category/`
3. Add channel in `query_builder.py`
4. Rebuild index: `python scripts/build_kb_index.py --force`

---

## Git Workflow

```bash
# Feature branch
git checkout -b feature/new-feature

# Make changes, test
pytest tests/ -v

# Commit
git add .
git commit -m "feat: add new feature"

# Push
git push origin feature/new-feature

# Create PR
```

---

## Useful Commands Reference

| Task | Command |
|------|---------|
| Start dev server | `uvicorn main:app --reload` |
| Run all tests | `pytest tests/ -v` |
| Build KB index | `python scripts/build_kb_index.py --verbose` |
| Validate pipeline | `python scripts/validate_pipeline.py` |
| Check DB connection | `python -c "from database.session import engine; print(engine.execute('SELECT 1').scalar())"` |
| View model features | `cat models/model_features.json \| jq` |
| Format code | `black .` (if configured) |
| Lint | `ruff check .` (if configured) |