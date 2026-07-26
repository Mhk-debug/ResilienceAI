# ResilienceAI Backend Documentation

> **Comprehensive backend documentation for the ResilienceAI Earthquake Risk Assessment Platform**

---

## Overview

ResilienceAI is an AI-powered earthquake hazard assessment system that analyzes building characteristics, seismic activity, fault proximity, and soil conditions to estimate earthquake risk for buildings. The backend combines:

- **Machine Learning Pipeline**: XGBoost model trained on the Richter Predictor dataset (Nepal 2015 Gorkha earthquake) predicting building damage grades
- **Hazard Engine**: Deterministic seismic hazard calculation using USGS earthquake catalogs, fault databases, SoilGrids soil data, and Gutenberg-Richter recurrence modeling
- **RAG System**: ChromaDB vector index with curated earthquake engineering knowledge base for LLM-enhanced explanations
- **LLM Integration**: Google Gemini 2.5 Flash with structured JSON output for risk interpretation and retrofit recommendations
- **Streaming Pipeline**: FastAPI SSE endpoints for real-time multi-stage assessment progress
- **PostgreSQL Storage**: Neon-hosted database with JSONB columns for full assessment persistence

---

## Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| PostgreSQL | 15+ (Neon) | Primary database |
| ChromaDB | Embedded | Vector index (local filesystem) |
| Google Gemini API | 2.5 Flash | LLM provider |
| USGS FDSNWS API | Public | Earthquake catalog |
| SoilGrids WCS | Public | Soil properties |

### Environment Setup

Create a `.env` file in the project root:

```bash
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
GEMINI_API_KEY=your-gemini-api-key
```

### Installation

```bash
# From project root
cd backend
pip install -r requirements.txt

# Install retrieval dependencies (optional but recommended)
pip install chromadb sentence-transformers
```

### Build Knowledge Base Index

```bash
python scripts/build_kb_index.py --verbose
```

### Run Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESILIENCEAI BACKEND                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │   FastAPI    │───▶│  Assessment  │───▶│   ML Model   │    │ Hazard   │  │
│  │   Router     │    │  Orchestrator │    │  (XGBoost)   │    │  Engine  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────┘  │
│         │                    │                    │                │       │
│         │                    │                    ▼                ▼       │
│         │                    │            ┌──────────────┐    ┌──────────┐  │
│         │                    │            │  Resilience  │    │  Hazard  │  │
│         │                    │            │   Score      │    │  Report  │  │
│         │                    │            └──────────────┘    └──────────┘  │
│         │                    │                    │                │       │
│         │                    ▼                    ▼                ▼       │
│         │           ┌──────────────────────────────────────────────────┐  │
│         │           │           LLM ANALYSIS PIPELINE                  │  │
│         │           │  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │  │
│         │           │  │ Retrieve │▶│  Build   │▶│  Generate    │   │  │
│         │           │  │ Knowledge│  │ Prompt   │  │  (Gemini)    │   │  │
│         │           │  └──────────┘  └──────────┘  └──────────────┘   │  │
│         │           └──────────────────────────────────────────────────┘  │
│         │                    │                    │                │       │
│         ▼                    ▼                    ▼                ▼       │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    POSTGRESQL (NEON) - JSONB STORAGE                  │ │
│  │  assessments table: id, location, scores, profile, building,        │ │
│  │  hazard, llm, evidence, metadata                                     │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    CHROMADB - VECTOR INDEX                           │ │
│  │  Collection: resilienceai_knowledge (cosine similarity)             │ │
│  │  Categories: building_vulnerability, mitigation, environmental_     │ │
│  │  hazards, local_context, earthquake_safety                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

| Module | File | Responsibility |
|--------|------|----------------|
| **API Entry** | `main.py` | FastAPI app, lifespan, CORS, router registration |
| **Schemas** | `project_schema.py` | All Pydantic models for requests/responses |
| **ML Pipeline** | `services/pipeline.py` | Feature engineering, preprocessing, alignment |
| **ML Model** | `services/resilience_engine.py` | XGBoost inference, resilience score calculation |
| **Resilience Service** | `services/resilience_service.py` | Orchestrates ML pipeline + LLM context building |
| **Hazard Engine** | `services/hazard_engine/engine.py` | Seismic hazard calculation pipeline |
| **LLM Service** | `services/llm_services.py` | Gemini integration, RAG, prompt engineering |
| **Retrieval** | `services/retrieval/` | ChromaDB index, embeddings, query building |
| **Database** | `database/` | SQLAlchemy models, session management |
| **Assessment Router** | `routes/assessment.py` | SSE streaming pipeline orchestration |
| **Routers** | `routes/*.py` | Individual endpoint handlers |

---

## Data Flow: User Input → Prediction → Retrieval → LLM → Response

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  Assessment  │────▶│  Parallel   │────▶│   Merge &   │
│  (Building  │     │   Router     │     │  Execution  │     │  LLM Input  │
│   Data +    │     │  (SSE Stream)│     │             │     │             │
│  Location)  │     └──────────────┘     └──────┬──────┘     └──────┬──────┘
└─────────────┘                                 │                   │
                                                ▼                   ▼
                                         ┌─────────────┐     ┌─────────────┐
                                         │  ML Pipeline│     │Hazard Engine│
                                         │ (XGBoost)   │     │ (USGS, Soil,│
                                         └──────┬──────┘     │  Faults)    │
                                                │            └──────┬──────┘
                                                ▼                   ▼
                                         ┌───────────────────────────────┐
                                         │     LLM Analysis Input        │
                                         │  (BuildingLLMContext +        │
                                         │   EnvironmentalContext)       │
                                         └───────────────┬───────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Knowledge      │
                                                │  Retrieval      │
                                                │  (ChromaDB)     │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Prompt Builder │
                                                │  (System +      │
                                                │   Building +    │
                                                │   Env + RAG)    │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Gemini 2.5     │
                                                │  Flash (JSON)   │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Validate &     │
                                                │  Build Evidence │
                                                │  Citations      │
                                                └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  SSE Complete   │
                                                │  + DB Persist   │
                                                └─────────────────┘
```

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | System architecture, component relationships, data flow diagrams |
| [API Reference](api.md) | All endpoints, schemas, request/response examples |
| [Pipeline](pipeline.md) | Complete assessment pipeline stages and internal flow |
| [Machine Learning](machine_learning.md) | XGBoost model, features, prediction process, limitations |
| [Hazard Engine](hazard_engine.md) | Hazard calculation methodology, scoring, environmental factors |
| [Resilience Scoring](resilience_scoring.md) | How resilience scores are calculated from damage probabilities |
| [RAG System](rag_system.md) | Knowledge base, chunking, embeddings, ChromaDB, retrieval flow |
| [LLM Integration](llm_integration.md) | Gemini integration, prompt structure, output validation, failure handling |
| [Data Models](data_models.md) | Pydantic models, internal structures, transformations |
| [Development](development.md) | Local setup, dependencies, testing, debugging |
| [Future Improvements](future_improvements.md) | Known limitations, planned improvements, technical debt |

---

## Key Design Decisions

### Why XGBoost for Damage Prediction?
- Trained on Richter Predictor dataset (Nepal 2015) with 3 damage grades
- Ordinal nature handled naturally by tree-based ensemble (no ordinal regression needed)
- MAE ~0.60 with loose regularization outperforms constrained ordinal models

### Why Deterministic Hazard Engine?
- No ML model for hazard — uses physics-based formulas (exponential decay, Gutenberg-Richter)
- Reproducible, auditable, no training data drift
- External APIs (USGS, SoilGrids) provide ground truth inputs

### Why ChromaDB + Sentence Transformers?
- Local-first, no external vector DB dependency
- `all-MiniLM-L6-v2` (384-dim) fast on CPU, good semantic quality
- Metadata filtering by category + tag boosting for relevance

### Why SSE Streaming?
- Assessment takes 5-15 seconds (ML + Hazard + LLM)
- Real-time progress updates improve UX significantly
- Each stage yields structured events for frontend rendering

### Why JSONB in PostgreSQL?
- Full assessment payloads stored verbatim for audit/replay
- Relational columns (scores, location, timestamps) enable querying
- Neon serverless PostgreSQL scales to zero, low ops overhead

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string with `sslmode=require` |
| `GEMINI_API_KEY` | Yes | Google AI Studio API key for Gemini 2.5 Flash |
| `SSL_CERT_FILE` | Auto | Set to `certifi.where()` in `llm_services.py` for SSL |

---

## Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Specific test modules
pytest tests/test_resilience.py -v
pytest tests/test_hazard.py -v

# Validate full pipeline (requires API keys)
python scripts/validate_pipeline.py
```

---

## Project Structure

```
backend/
├── main.py                    # FastAPI app, lifespan, routers
├── project_schema.py          # All Pydantic models
├── richtor_mappings.py        # Richter dataset code → description mapping
├── requirements.txt           # Python dependencies
├── database/
│   ├── __init__.py
│   ├── session.py # SQLAlchemy engine, session, Base
│   └── models.py              # Assessment ORM model (JSONB columns)
├── models/
│   ├── seismic_resilience_xgb.pkl   # Trained XGBoost model
│   └── model_features.json          # Expected feature list (121 features)
├── routes/
│   ├── __init__.py
│   ├── assessment.py          # SSE orchestration endpoint
│   ├── resilience.py          # /api/resilience/assess
│   ├── hazard.py              # /api/hazard/calculate
│   └── llm.py                 # /api/llm/analysis
├── services/
│   ├── __init__.py
│   ├── pipeline.py            # Feature engineering, preprocessing
│   ├── resilience_engine.py   # XGBoost inference, score calc
│   ├── resilience_service.py  # High-level ML + context building
│   ├── llm_services.py        # Gemini client, RAG, prompt builder
│   ├── hazard_engine/         # Hazard calculation modules
│   │   ├── engine.py          # Main orchestrator
│   │   ├── usgs.py            # USGS FDSNWS catalog query
│   │   ├── soil.py            # SoilGrids WCS + liquefaction
│   │   ├── faults.py          # Fault proximity calculation
│   │   ├── scoring.py         # Historical event scoring
│   │   ├── calibration.py     # Score combination, classification
│   │   ├── recurrence.py      # Gutenberg-Richter modeling
│   │   ├── weights.py         # Distance/depth/magnitude/age weights
│   │   ├── statistics.py      # Catalog statistics
│   │   ├── constants.py       # Threshold constants
│   │   ├── shakemap.py        # USGS ShakeMap integration
│   │   └── utils.py           # Haversine, age calculation
│   └── retrieval/             # RAG system
│       ├── __init__.py
│       ├── retriever.py       # Main retrieval orchestrator
│       ├── indexer.py         # ChromaDB build/load
│       ├── embedder.py        # SentenceTransformer wrapper
│       ├── chunk_loader.py    # Markdown parsing, validation, chunking
│       └── query_builder.py   # Structured query construction
├── scripts/
│   ├── build_kb_index.py      # Build ChromaDB index
│   ├── validate_pipeline.py   # End-to-end validation
│   └── *.py                   # Calibration/debug scripts
├── tests/                     # Unit/integration tests
└── docs/                      # This documentation
```

---

## Version

**Backend Version**: 1.2.0 (see `main.py`)

**API Version**: `/api/` prefix on all routes

---

## Support

For issues, see [Future Improvements](future_improvements.md) for known limitations and planned work.