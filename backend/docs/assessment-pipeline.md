# Assessment Pipeline Architecture

> **Documentation for ResilienceAI** — Myanmar Youth AI Innovation Competition 2026

---

## 1. Pipeline Overview

```
[POST /api/assessment/process]
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 1. INITIALIZATION                                   │
│    • Parse AssessmentRequest (lat, lon, building)   │
│    • Build HazardInput + BuildingInput              │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 2. PARALLEL ANALYSIS (asyncio.gather)               │
│                                                     │
│   ┌─────────────────────┐   ┌─────────────────────┐ │
│   │ ML Resilience Model │   │ Hazard Engine       │ │
│   │                     │   │                     │ │
│   │ XGBoost → 0-100     │   │ USGS events         │ │
│   │ score               │   │ Fault proximity     │ │
│   │                     │   │ Soil classification │ │
│   │ BuildingLLMContext  │   │ Ground motion       │ │
│   │   • structural      │   │                     │ │
│   │   • material        │   │ EnvironmentalContext│ │
│   │   • substructure    │   │                     │ │
│   └─────────────────────┘   └─────────────────────┘ │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 3. KNOWLEDGE RETRIEVAL (optional, fail-safe)        │
│                                                     │
│   Retriever.retrieve(building_ctx, env_ctx)         │
│        │                                            │
│        ├── QueryBuilder → 3 channel queries         │
│        │   • building_vulnerability (k=2)           │
│        │   • environmental (k=2)                    │
│        │   • local_context (k=1)                    │
│        │                                            │
│        ├── ChromaDB semantic search                 │
│        │   • all-MiniLM-L6-v2 embeddings            │
│        │   • metadata category filtering            │
│        │   • tag-based score boosting               │
│        │                                            │
│        └── Up to 5 chunks returned                  │
│                                                     │
│   On failure → empty string, assessment continues   │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 4. LLM ANALYSIS                                     │
│                                                     │
│   Prompt Structure:                                 │
│   ┌─────────────────────────────────────────────┐   │
│   │ System Instructions                         │   │
│   ├─────────────────────────────────────────────┤   │
│   │ BUILDING CONTEXT                            │   │
│   │   (structural, material, substructure)      │   │
│   ├─────────────────────────────────────────────┤   │
│   │ ENVIRONMENTAL CONTEXT                       │   │
│   │   (hazard, soil, faults, ground motion)     │   │
│   ├─────────────────────────────────────────────┤   │
│   │ RETRIEVED KNOWLEDGE (if available)          │   │
│   │   Reference 1: Category, Source             │   │
│   │   Reference 2: Category, Source             │   │
│   ├─────────────────────────────────────────────┤   │
│   │ OUTPUT REQUIREMENTS + PRIORITY RULES        │   │
│   └─────────────────────────────────────────────┘   │
│                                                     │
│   GenAIClient.generate(prompt, schema)              │
│   • Gemini 2.5 Flash                                │
│   • 3-retry exponential backoff                     │
│   • JSON mode with schema validation                │
│                                                     │
│   Returns: LLMAnalysisOutput                        │
│   • summary: List[str] (6 items)                    │
│   • recommendations: List[LLMRecommendation] (5)    │
│   • risk_interpretation: RiskInterpretation         │
│   • confidence: float                               │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│ 5. PERSISTENCE                                      │
│    • Save to Neon Postgres (JSONB columns)          │
│    • Return assessment_id to frontend               │
└─────────────────────────────────────────────────────┘
```

---

## 2. Startup Initialization

```
FastAPI lifespan
        │
        ├── Load ML model (joblib)
        │   • seismic_resilience_xgb.pkl
        │   • model_features.json
        │   → app.state.model
        │   → app.state.expected_features
        │
        ├── Initialize retriever (optional)
        │   • build_default_retriever()
        │   • Loads ChromaDB + embedding model
        │   • Returns None if unavailable
        │   → app.state.retriever
        │
        └── Yield (app ready)
```

### Retriever Initialization (`_init_retriever`)

```python
def _init_retriever():
    try:
        from services.retrieval import build_default_retriever
        retriever = build_default_retriever()
        if retriever is None:
            logger.info("Retriever not available — RAG disabled")
        else:
            logger.info("Retriever initialized successfully")
        return retriever
    except Exception as e:
        logger.warning("Retriever init failed: %s", e)
        return None
```

---

## 3. Dependency Injection

```
LLMService(client, retriever=None)
              │          │
              │          └── Optional Retriever instance
              │              • Injected at construction time
              │              • Never created inside request handlers
              │
              └── GenAIClient (required)
                  • Wraps Gemini API
                  • Handles retries + schema cleaning
```

### Route-level wiring

**`routes/llm.py`** — standalone LLM endpoint:

```python
retriever = getattr(request.app.state, "retriever", None)
service = create_llm_service(retriever=retriever)
result = service.analyze(input_data)
```

**`routes/assessment.py`** — full assessment pipeline:

```python
retriever = getattr(request.app.state, "retriever", None)
llm_service = create_llm_service(retriever=retriever)
# ... later in the generator:
llm_data = await asyncio.to_thread(llm_service.analyze, llm_input)
```

---

## 4. Failure Handling Matrix

| Failure Mode                | Detection                                  | Behavior                      | User Impact                |
| --------------------------- | ------------------------------------------ | ----------------------------- | -------------------------- |
| ChromaDB missing at startup | `build_default_retriever()` returns `None` | `app.state.retriever = None`  | None — RAG disabled        |
| Embedding model fails       | Exception in `SentenceTransformer()`       | Log warning, retriever = None | None                       |
| Retrieval returns empty     | `retriever.retrieve()` → `[]`              | Empty string in prompt        | None                       |
| Retrieval raises exception  | `try/except` in `_retrieve_knowledge()`    | Log warning, return `""`      | None                       |
| LLM API failure             | `GenAIClient.generate()`                   | 3 retries, then HTTP 500      | Error returned to frontend |
| ML model missing at startup | `FileNotFoundError` in lifespan            | Critical boot failure         | App won't start            |
| Invalid building input      | Pydantic validation                        | HTTP 400                      | Error returned to frontend |

**Golden rule**: The entire retrieval subsystem can fail or be absent, and the assessment pipeline continues to work exactly as it did before RAG was added.

---

## 5. Performance Characteristics

| Stage               | Typical Time | Notes                              |
| ------------------- | ------------ | ---------------------------------- |
| ML Prediction       | 0.1–0.3s     | XGBoost inference on CPU           |
| Hazard Engine       | 1–5s         | USGS API calls, fault calculations |
| Knowledge Retrieval | 0.1–0.5s     | Embedding + ChromaDB query         |
| LLM Generation      | 2–8s         | Gemini 2.5 Flash API call          |
| Database Save       | 0.5–1.5s     | Neon Postgres insert               |
| **Total**           | **4–15s**    | Depends on network + API latency   |

### Logged metrics (added in Phase F)

```
LLM analysis complete | retrieval=215ms | llm=3.45s | total=3.78s | prompt_words=850 | rag=enabled

Assessment complete | parallel=2.10s | llm=3.45s | save=0.80s | total=6.35s | resilience=42.50 | hazard=78.00 | rag=enabled

Retrieved 4 knowledge chunks in 215 ms | building_vulnerability: mud_mortar_stone,high_vulnerability | environmental: soil_amplification,liquefaction
```

---

## 6. Knowledge Base Structure

```
backend/data/knowledge/
├── building_vulnerability/     (6 files)
│   ├── cement_mortar_brick.md
│   ├── foundation_types.md
│   ├── materials_overview.md
│   ├── mud_mortar_stone.md
│   ├── rc_engineered.md
│   ├── roof_types.md
│   └── soft_story.md
├── earthquake_safety/          (3 files)
│   ├── after_earthquake.md
│   ├── before_earthquake.md
│   └── during_earthquake.md
├── environmental_hazards/      (3 files)
│   ├── fault_proximity.md
│   ├── historical_seismicity.md
│   └── soil_amplification.md
├── local_context/              (3 files)
│   ├── myanmar_building_code.md
│   ├── sagaing_fault.md
│   └── yangon_soft_soil.md
└── mitigation/                 (3 files)
    ├── maintenance.md
    ├── retrofitting_overview.md
    └── wall_anchoring.md
```

**Total: 19 files** across 5 categories.

### Adding new knowledge

1. Create a `.md` file in the appropriate category directory
2. Include required YAML frontmatter:
    ```yaml
    ---
    id: "unique-doc-id"
    category: "building_vulnerability" # must match directory name
    tags: ["tag1", "tag2"]
    source:
        title: "Document Title"
        organization: "Source Org"
        url: "https://..."
    ---
    ```
3. Run `python scripts/build_kb_index.py` to rebuild the ChromaDB index

---

## 7. Retrieval Query Strategy

Three independent channels, each targeting a different knowledge category:

| Channel                  | Query Source                               | Categories                             | k   | Purpose                                         |
| ------------------------ | ------------------------------------------ | -------------------------------------- | --- | ----------------------------------------------- |
| `building_vulnerability` | Building material + structural fields      | `building_vulnerability`, `mitigation` | 2   | Match building-specific vulnerability knowledge |
| `environmental`          | Hazard score, soil, fault, historical data | `environmental_hazards`                | 2   | Match environmental hazard knowledge            |
| `local_context`          | Hazard level + summary                     | `local_context`                        | 1   | Match Myanmar-specific context                  |

**Total budget**: 5 chunks maximum.

**Score boosting**: Chunks whose tags match the building's active materials get a +0.05 boost per matching tag (internal only — scores never exposed to the LLM).

---

## 8. LLM Prompt Structure

```
You are a seismic risk engineering AI assistant.
...
-----------------------------
BUILDING CONTEXT:
{structural, material, substructure dicts}
-----------------------------
ENVIRONMENTAL CONTEXT:
{hazard, soil, faults, ground motion}
-----------------------------
RETRIEVED KNOWLEDGE:           ← only if chunks available
Reference 1
Category: building_vulnerability
Source: FEMA
...
-----------------------------
OUTPUT REQUIREMENTS:
...
PRIORITY OF INFORMATION:
1. Assessment results
2. Retrieved knowledge
3. General reasoning
...
```

---

## 9. Key Design Decisions

1. **Retriever is optional** — injected via constructor, never required
2. **Scores never exposed to LLM** — only source/category metadata
3. **Single retrieval call per assessment** — no duplicate queries
4. **Retriever initialized once at startup** — not per request
5. **Response schema unchanged** — frontend needs no modifications
6. **Clean prompt sections** — each section clearly separated
7. **Priority of information** — LLM knows assessment > knowledge > reasoning
