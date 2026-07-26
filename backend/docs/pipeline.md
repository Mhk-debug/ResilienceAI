# Complete Assessment Pipeline

> **End-to-end flow from user input to persisted assessment with streaming progress**

---

## Pipeline Overview

The assessment pipeline orchestrates four major components in a staged, partially parallel execution:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASSESSMENT PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 1: INITIALIZATION (~50ms)                                            │
│  ├─ Validate input payload                                                   │
│  ├─ Build HazardInput & BuildingInput models                                 │
│  └─ Capture retriever from app.state                                         │
│                                                                              │
│  STAGE 2: PARALLEL EXECUTION (~3-8s)                                        │
│  ├─ RESILIENCE TRACK                    ├─ HAZARD TRACK                     │
│  │  services.pipeline.process_and_align   │  services.hazard_engine.engine  │
│  │    _inference_data                     │    .calculate_hazard            │
│  │  services.resilience_engine.         │  ├─ USGS earthquake catalog       │
│  │    calculate_resilience_score        │  ├─ SoilGrids soil properties     │
│  │                                       │  ├─ Fault proximity               │
│  │  Output: ResilienceAssessmentResponse │  ├─ Historical hazard scoring     │
│  │                                       │  ├─ Gutenberg-Richter recurrence  │
│  └─▶ BuildingLLMContext                   │  └─ ShakeMap integration        │
│                                           │                                   │
│                                           │  Output: HazardReport             │
│                                           │    └─ EnvironmentalContext       │
│                                                                              │
│  STAGE 3: LLM ANALYSIS (~3-8s)                                            │
│  ├─ Build LLMAnalysisInput from both contexts                             │
│  ├─ Retrieve knowledge chunks (if retriever available)                    │
│  ├─ Construct prompt with system/building/env/knowledge sections         │
│  ├─ Call Gemini 2.5 Flash with JSON schema                                │
│  ├─ Validate evidence IDs against retrieved chunks                        │
│  └─ Output: LLMAnalysisOutput + EvidenceCitation map                      │
│                                                                              │
│  STAGE 4: PERSISTENCE (~100ms)                                            │
│  ├─ Build SaveAssessmentRequest                                           │
│  ├─ Merge evidence into LLM JSONB                                         │
│  ├─ Geocode place name (Nominatim)                                        │
│  └─ INSERT into assessments table (JSONB columns)                         │
│                                                                              │
│  STAGE 5: COMPLETION                                                      │
│  ├─ Emit SSE 'complete' with assessment_id                                │
│  └─ Log structured metrics                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage Details

### Stage 1: Initialization

**Location:** `routes/assessment.py` → `process_assessment()` → `assessment_generator()`

```python
# Input validation & model building
hazard_input_payload = HazardInput(
    latitude=payload.latitude,
    longitude=payload.longitude,
    search_radius_km=100,
    historical_years=50,
    minimum_magnitude=4.5,
)

building_fields = payload.model_dump(exclude={"latitude", "longitude"})
building_input_payload = BuildingInput(**building_fields)

# Capture retriever from app state (set in main.py lifespan)
retriever = getattr(request.app.state, "retriever", None)
llm_service = create_llm_service(retriever=retriever)
```

**SSE Events:**
```json
{"type": "stage_started", "stage": "initializing", "status": "Preparing your assessment..."}
{"type": "stage_completed", "stage": "initializing"}
```

---

### Stage 2: Parallel Execution

Both tracks run concurrently via `asyncio.gather()`:

#### Track A: Resilience (ML Inference)

**Location:** `services/resilience_service.py` → `predict_resilience()`

```python
def predict_resilience(payload: BuildingInput, model, expected_features):
    # 1. Convert to dict
    raw_input = payload.model_dump()
    
    # 2. Feature engineering & alignment (services/pipeline.py)
    dataframe = process_and_align_inference_data(
        raw_input_dict=raw_input,
        trained_model=model,
        expected_features_list=expected_features
    )
    
    # 3. XGBoost prediction
    score = calculate_resilience_score(model, dataframe)
    
    # 4. Build LLM context
    context_data = {
        "structural": {...},
        "material": {...},
        "substructure": {...}
    }
    building_context = BuildingLLMContext.model_validate(context_data)
    
    return ResilienceAssessmentResponse(
        status="success",
        resilience_score=round(float(score), 2),
        building_llm_context=building_context
    )
```

**Key Functions:**

| Function | File | Purpose |
|----------|------|---------|
| `process_and_align_inference_data` | `services/pipeline.py` | Feature engineering, scaling, one-hot encoding, schema alignment |
| `calculate_resilience_score` | `services/resilience_engine.py` | Convert XGBoost probabilities to 0-100 resilience score |
| `StructuralFeatureExtractor` | `services/pipeline.py` | Sklearn transformer for feature engineering |

**Feature Engineering Details (`pipeline.py`):**

```python
# 1. Scale physical dimensions to Richter dataset quantiles
area_percentage, height_percentage = scale_user_inputs(plinth_area_sqft, height_ft)

# 2. StructuralFeatureExtractor transforms:
#    - Compute height_to_floor_ratio, area_to_height_ratio
#    - Flag highly vulnerable materials (mud_mortar_stone, adobe_mud)
#    - Flag engineered materials (rc_engineered, cement_mortar_brick)
#    - Compute structural_age_stress = age * floors
#    - Drop non-structural columns (geo_level_*, legal_ownership_status, etc.)

# 3. One-hot encode categorical: foundation_type, roof_type, ground_floor_type

# 4. Align to training schema (expected_features_list) - add missing as 0
```

#### Track B: Hazard Engine

**Location:** `services/hazard_engine/engine.py` → `calculate_hazard()`

```python
async def calculate_hazard(latitude, longitude, search_radius_km, historical_years, minimum_magnitude):
    # 1. Query USGS earthquake catalog
    events, usgs_status, usgs_warnings = query_usgs_catalog(...)
    
    # 2. Fetch soil properties (SoilGrids WCS)
    soil_props = await fetch_soilgrids_data(latitude, longitude)
    soil_risk = evaluate_liquefaction_risk(soil_props)
    
    # 3. Find nearest fault
    fault_proximity = find_nearest_fault(latitude, longitude)
    
    # 4. Calculate historical seismic hazard score
    event_score, processed_events = calculate_historical_seismic_hazard(events, minimum_magnitude)
    
    # 5. Calculate component scores
    fault_score = calculate_fault_score(fault_proximity["distance_km"])
    soil_score = calculate_soil_score(soil_risk["lsi_score"])
    
    # 6. Calibrate combined score
    overall_score, hazard_level, confidence = calibrate_hazard_score(event_score, fault_score, soil_score)
    
    # 7. Gutenberg-Richter recurrence
    recurrence_data = calculate_gutenberg_richter(all_mags, historical_years, minimum_magnitude)
    
    # 8. ShakeMap integration
    shakemap_data = integrate_shakemap_data(events, latitude, longitude)
    
    # 9. Build indicators & summary
    indicators = build_indicators(...)
    environmental_context = build_environmental_context(...)
    
    return HazardReport(...)
```

**Hazard Sub-Modules:**

| Module | File | Responsibility |
|--------|------|----------------|
| `usgs.py` | `query_usgs_catalog` | FDSNWS event query, haversine distance, timeout handling |
| `soil.py` | `fetch_soilgrids_data`, `evaluate_liquefaction_risk` | WCS multi-layer fetch, LSI calculation, fallback soils |
| `faults.py` | `find_nearest_fault` | Distance to polyline faults, proximity classification |
| `scoring.py` | `calculate_historical_seismic_hazard` | Event weighting (distance, depth, magnitude, age) |
| `recurrence.py` | `calculate_gutenberg_richter` | b-value, a-value, M6 recurrence interval |
| `calibration.py` | `calibrate_hazard_score` | Exponential saturation, hazard level classification |
| `weights.py` | `compute_event_contribution` | Exponential decay weights |
| `shakemap.py` | `integrate_shakemap_data` | Peak MMI/PGA estimation from events |
| `statistics.py` | `compute_catalog_statistics` | Summary stats for response |

**SSE Events:**
```json
{"type": "stage_started", "stage": "resilience", "status": "Assessing building resilience..."}
{"type": "stage_started", "stage": "hazard", "status": "Running environmental hazard engine..."}
{"type": "stage_completed", "stage": "resilience"}
{"type": "stage_completed", "stage": "hazard"}
```

---

### Stage 3: LLM Analysis

**Location:** `services/llm_services.py` → `LLMService.analyze()`

```python
def analyze(self, input_data: LLMAnalysisInput) -> Tuple[LLMAnalysisOutput, Dict[str, EvidenceCitation]]:
    # 1. Knowledge Retrieval
    retrieved_knowledge, retrieved_results = self._retrieve_knowledge(
        building=input_data.building_context,
        env=input_data.environmental_context
    )
    
    # 2. Build Prompt
    prompt = self._build_prompt(
        building=input_data.building_context,
        env=input_data.environmental_context,
        retrieved_knowledge=retrieved_knowledge
    )
    
    # 3. Call Gemini with JSON schema
    schema = LLMAnalysisOutput.model_json_schema()
    result = self.client.generate(prompt, schema=schema)
    
    # 4. Build Evidence Citations
    evidence_map = self._build_evidence_map(retrieved_results, result)
    
    return LLMAnalysisOutput(**result), evidence_map
```

#### 3.1 Knowledge Retrieval

**Location:** `services/retrieval/retriever.py` → `Retriever.retrieve()`

```python
def retrieve(self, building: BuildingLLMContext, env: EnvironmentalContext) -> List[RetrievalResult]:
    # 1. Build channel queries
    channels = self.query_builder.build(building, env)
    # Returns 3 channels:
    #   - building_vulnerability (categories: building_vulnerability, mitigation)
    #   - environmental (category: environmental_hazards)
    #   - local_context (category: local_context)
    
    # 2. Execute per-channel search
    for channel in channels:
        query_vector = self.embedder.embed_single(channel.query)
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=channel.k * 10,  # Over-fetch for re-ranking
            where={"category": {"$in": channel.category_filter}},
            include=["documents", "metadatas", "distances"]
        )
        
        # 3. Score boosting for matching tags
        for doc, meta, distance in zip(...):
            base_score = 1.0 - distance  # Cosine similarity
            final_score = self._apply_tag_boost(base_score, meta, channel.tags_filter)
            
    # 4. Deduplicate by chunk_id, keep highest score
    # 5. Return top-k per channel combined
```

**Query Builder Channels (`services/retrieval/query_builder.py`):**

| Channel | Categories | Tags Filter | k |
|---------|------------|-------------|---|
| `building_vulnerability` | `building_vulnerability`, `mitigation` | Active material tags (e.g., `rc_engineered`, `mud_mortar_stone`) | 2 |
| `environmental` | `environmental_hazards` | Soil class, hazard level, fault proximity | 2 |
| `local_context` | `local_context` | Hazard level + first summary sentence | 1 |

#### 3.2 Prompt Construction

**Location:** `services/llm_services.py` → `LLMService._build_prompt()`

```
SYSTEM INSTRUCTIONS
-------------------
You are a seismic risk engineering AI assistant.
Your task is to analyze building structural vulnerability and environmental seismic hazard,
then return a structured JSON response.
You MUST follow the output format exactly and return ONLY valid JSON.

BUILDING CONTEXT
----------------
{building.model_dump()}

ENVIRONMENTAL CONTEXT
---------------------
{env.model_dump()}

RETRIEVED KNOWLEDGE (if available)
----------------------------------
Reference 1 [chunk_id: vuln-rc-engineered__chunk_0]
Category: mitigation
Title: RC Engineered Seismic Detailing
Source: FEMA P-750
...chunk text...

OUTPUT REQUIREMENTS
-------------------
Return ONLY valid JSON matching the schema.
```

#### 3.3 Gemini Call with Structured Output

**Location:** `services/llm_services.py` → `GenAIClient.generate()`

```python
def generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    schema = clean_schema(schema)  # Remove additionalProperties
    
    response = self.client.models.generate_content(
        model=self.model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.1,
        ),
    )
    
    # Robust extraction
    raw_text = response.text or extract_from_candidates(response)
    return safe_json_load(raw_text)
```

**Schema Cleaning:** Removes `additionalProperties` (not supported by Gemini) recursively.

#### 3.4 Evidence Citation Building

**Location:** `services/llm_services.py` → `LLMService._build_evidence_map()`

```python
def _build_evidence_map(self, retrieved_results, llm_result):
    # 1. Collect all evidence_ids from LLM output (summary + recommendations)
    cited_ids = set()
    for item in llm_result.get("summary", []):
        cited_ids.update(item.get("evidence_ids", []))
    for rec in llm_result.get("recommendations", []):
        cited_ids.update(rec.get("evidence_ids", []))
    
    # 2. Validate against actually retrieved chunks
    valid_ids = {r.chunk_id for r in retrieved_results}
    validated_ids = [eid for eid in cited_ids if eid in valid_ids]
    
    # 3. Build citation objects
    for chunk_id in validated_ids:
        result = result_map[chunk_id]
        evidence_map[chunk_id] = EvidenceCitation(
            chunk_id=chunk_id,
            source_title=result.metadata.get("title", ""),
            source_org=result.metadata.get("source_org", ""),
            source_url=result.metadata.get("source_url", ""),
            category=result.metadata.get("category", ""),
            excerpt=result.text[:300] + "...",
            relevance_score=result.score
        )
    
    return evidence_map
```

**SSE Events:**
```json
{"type": "stage_started", "stage": "llm", "status": "Generating AI feedback..."}
{"type": "stage_completed", "stage": "llm"}
```

---

### Stage 4: Persistence

**Location:** `routes/assessment.py` → `save_assessment()`

```python
async def save_assessment(request: SaveAssessmentRequest, db: Session):
    # 1. Serialize models to JSON
    building = request.building.model_dump(mode="json")
    hazard = request.hazard.model_dump(mode="json")
    llm = request.llm.model_dump(mode="json")
    profile = request.profile.model_dump(mode="json")
    evidence = {k: v.model_dump(mode="json") for k, v in request.evidence.items()}
    
    # 2. Merge evidence into LLM JSONB
    llm["evidence"] = evidence
    
    # 3. Extract metadata
    location = hazard["location"]
    hazard_metrics = hazard["hazard"]
    metadata = hazard.get("metadata", {})
    
    # 4. Geocode place name
    place_name = await get_place_name(location["latitude"], location["longitude"])
    
    # 5. Create ORM object
    assessment = Assessment(
        latitude=location["latitude"],
        longitude=location["longitude"],
        place_name=place_name,
        resilience_score=building["resilience_score"],
        hazard_score=hazard_metrics["overall_score"],
        hazard_level=hazard_metrics["hazard_level"],
        model_version=metadata.get("model_version"),
        execution_time_seconds=metadata.get("execution_time_seconds"),
        profile=profile,
        building=building,
        hazard=hazard,
        llm=llm,
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {"assessment_id": str(assessment.id), "created_at": assessment.created_at.isoformat()}
```

**Database Schema (`database/models.py`):**

| Column | Type | Index |
|--------|------|-------|
| `id` | UUID | PK |
| `created_at` | DateTime (TZ) | Yes |
| `place_name` | String | No |
| `latitude` | Float | No |
| `longitude` | Float | No |
| `resilience_score` | Float | Yes |
| `hazard_score` | Float | Yes |
| `hazard_level` | String(20) | Yes |
| `profile` | JSONB | No |
| `building` | JSONB | No |
| `hazard` | JSONB | No |
| `llm` | JSONB | No |
| `model_version` | String(50) | No |
| `execution_time_seconds` | Float | No |

**SSE Events:**
```json
{"type": "stage_started", "stage": "saving", "status": "Saving your assessment..."}
{"type": "stage_completed", "stage": "saving"}
```

---

### Stage 5: Completion

**Location:** `routes/assessment.py` → end of `assessment_generator()`

```python
total_elapsed = time.time() - t0

logger.info(
    "Assessment complete | "
    "parallel=%.2fs | llm=%.2fs | save=%.2fs | total=%.2fs | "
    "resilience=%.2f | hazard=%.2f | rag=%s",
    parallel_elapsed, llm_elapsed, save_elapsed, total_elapsed,
    building_data.resilience_score,
    hazard_data.hazard.get("overall_score", 0),
    "enabled" if retriever is not None else "disabled",
)

yield sse_event({
    "type": "complete",
    "assessment_id": final_data.get("assessment_id")
})
```

**Final SSE Event:**
```json
{"type": "complete", "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
```

---

## Error Handling

| Stage | Failure Mode | Behavior |
|-------|--------------|----------|
| Initialization | Invalid payload | `400` via Pydantic validation |
| Resilience | Model not loaded | `500` "Resilience model is not initialized" |
| Resilience | Feature mismatch | `400` with missing field details |
| Hazard | USGS timeout | Warning logged, continues with empty events |
| Hazard | SoilGrids failure | Falls back to deterministic regional soil |
| LLM | Retrieval failure | Logged warning, continues without RAG |
| LLM | Gemini API error | Retry 3x with exponential backoff, then `500` |
| LLM | Invalid JSON | `safe_json_load` fallback extraction, then `500` |
| Persistence | DB error | Rollback, `500` "Failed to persist assessment" |

**SSE Error Event:**
```json
{"type": "error", "detail": "LLM analysis failed: Gemini API timeout"}
```

---

## Performance Characteristics

| Stage | Typical Duration | Bottleneck |
|-------|------------------|------------|
| Initialization | ~50ms | Pydantic validation |
| Resilience (ML) | ~200ms | XGBoost inference (CPU) |
| Hazard | 3-8s | USGS API (6s timeout), SoilGrids WCS |
| LLM | 3-8s | Gemini API latency |
| Persistence | ~100ms | Neon round-trip + geocoding |
| **Total** | **6-17s** | External APIs |

**Optimization Opportunities:**
- Cache hazard results by location (24h TTL)
- Parallelize USGS + SoilGrids (already async)
- Connection pooling for ChromaDB
- Batch LLM calls if multiple assessments

---

## Internal Function Flow Diagram

```
process_assessment()
├─ assessment_generator()
│  ├─ INITIALIZING
│  ├─ PARALLEL:
│  │  ├─ asyncio.to_thread(calculate_pure_resilience)
│  │  │   └─ predict_resilience()
│  │  │       ├─ process_and_align_inference_data()
│  │  │       │   ├─ scale_user_inputs()
│  │  │       │   ├─ StructuralFeatureExtractor.fit_transform()
│  │  │       │   ├─ pd.get_dummies()
│  │  │       │   └─ reindex to expected_features
│  │  │       ├─ calculate_resilience_score()
│  │  │       │   └─ model.predict_proba() → weighted score
│  │  │       └─ BuildingLLMContext construction
│  │  │
│  │  └─ asyncio.create_task(calculate_hazard_route)
│  │      └─ calculate_hazard_pydantic()
│  │          └─ calculate_hazard()
│  │              ├─ query_usgs_catalog()
│  │              ├─ fetch_soilgrids_data() (async)
│  │              ├─ find_nearest_fault()
│  │              ├─ calculate_historical_seismic_hazard()
│  │              ├─ calculate_fault_score()
│  │              ├─ calculate_soil_score()
│  │              ├─ calibrate_hazard_score()
│  │              ├─ calculate_gutenberg_richter()
│  │              ├─ integrate_shakemap_data()
│  │              └─ build response objects
│  │
│  ├─ LLM ANALYSIS
│  │  ├─ LLMAnalysisInput construction
│  │  ├─ llm_service.analyze()
│  │  │   ├─ _retrieve_knowledge()
│  │  │   │   ├─ query_builder.build()
│  │  │   │   ├─ embedder.embed_single()
│  │  │   │   ├─ chromadb query per channel
│  │  │   │   ├─ _apply_tag_boost()
│  │  │   │   └─ deduplicate + sort
│  │  │   ├─ _build_prompt()
│  │  │   ├─ client.generate() → Gemini
│  │  │   ├─ _build_evidence_map()
│  │  │   └─ return (LLMAnalysisOutput, evidence_map)
│  │  └─ SaveAssessmentRequest assembly
│  │
│  ├─ SAVING
│  │  └─ save_assessment()
│  │      ├─ model_dump(mode="json") all payloads
│  │      ├─ merge evidence into llm JSONB
│  │      ├─ get_place_name() (Nominatim)
│  │      └─ db.add/commit/refresh
│  │
│  └─ COMPLETE → yield assessment_id
```

---

## Testing the Pipeline

```bash
# Full pipeline validation (requires API keys)
python scripts/validate_pipeline.py

# Individual component tests
pytest tests/test_resilience.py -v
pytest tests/test_hazard.py -v
pytest tests/test_retrieval.py -v
pytest tests/test_llm_service.py -v
pytest tests/test_llm_retrieval_integration.py -v
```