# API Documentation

> **Complete reference for all ResilienceAI backend API endpoints**

---

## Base URL

```
http://localhost:8000
```

Interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Authentication

Currently no authentication required for local development. Production deployments should add API key or OAuth middleware.

---

## Common Headers

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `Accept` | `application/json` |
| `Accept` | `text/event-stream` (for SSE endpoints) |

---

## Error Response Format

All endpoints return standard HTTP status codes with JSON error bodies:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable (external API failure) |

**Important:** The `/api/hazard/calculate` endpoint **never returns 503** for external API failures. Instead, it returns 200 with a degraded report (`metadata.degraded: true`, `metadata.warnings` populated, `confidence` reduced). This ensures the assessment pipeline (`/api/assessment/process`) always completes.

---

## Endpoints

### 1. Resilience Assessment

#### `POST /api/resilience/assess`

Calculate building resilience score using the XGBoost model.

**Tags:** `Resilience Score engine`

**Request Body:**
```json
{
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
  "has_superstructure_timber": 0
}
```

**Field Reference:**

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `count_floors_pre_eq` | int | 1–10 | Stories before earthquake |
| `age` | int | 0–999 | Building age in years |
| `area_sq_ft` | int | 70–5000 | Floor area |
| `height_ft` | int | 6–305 | Building height |
| `foundation_type` | str | 1 char | `r`, `w`, `i`, `u`, `h` |
| `roof_type` | str | 1 char | `n`, `q`, `x` |
| `ground_floor_type` | str | 1 char | `f`, `v`, `x`, `m`, `z` |
| `has_superstructure_*` | int | 0/1 | Material indicator flags (exactly one should be 1) |

**Foundation Type Codes:**
| Code | Description |
|------|-------------|
| `r` | Mud mortar - Stone |
| `w` | Wooden / Timber |
| `i` | Reinforced Concrete / Cement |
| `u` | Cement - Stone masonry |
| `h` | Bamboo / Adobe / Mud pile |

**Roof Type Codes:**
| Code | Description |
|------|-------------|
| `n` | Bamboo / Timber / Mud |
| `q` | Corrugated Galvanized Iron (CGI) |
| `x` | Reinforced Concrete slab |

**Ground Floor Type Codes:**
| Code | Description |
|------|-------------|
| `f` | Mud / Soil |
| `v` | Brick / Stone with cement mortar |
| `x` | RC slab |
| `m` | Timber / Wood planking |
| `z` | Other composite |

**Response (200):**
```json
{
  "status": "success",
  "resilience_score": 72.5,
  "building_llm_context": {
    "structural": {
      "floors": 2,
      "age_years": 25,
      "floor_area_sq_feets": 1200,
      "height_feets": 24
    },
    "material": {
      "roof_type": "Corrugated Galvanized Iron (CGI) sheets",
      "foundation_type": "Reinforced Concrete (RC) / Cement",
      "ground_floor_type": "Reinforced Concrete (RC) slab floor"
    },
    "substructure": {
      "mud_mortar_stone": false,
      "cement_brick": false,
      "rc_engineered": true,
      "rc_non_engineered": false,
      "adobe_mud": false,
      "timber": false
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | str | Always `"success"` |
| `resilience_score` | float | 0–100 (higher = more resilient) |
| `building_llm_context` | object | Structured context for LLM prompts |

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/resilience/assess \
  -H "Content-Type: application/json" \
  -d '{
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
    "has_superstructure_timber": 0
  }'
```

---

### 2. Hazard Assessment

#### `POST /api/hazard/calculate`

Calculate environmental seismic hazard for a location.

**Tags:** `Hazard Engine`

**Request Body:**
```json
{
  "latitude": 23.8103,
  "longitude": 90.4125,
  "search_radius_km": 100.0,
  "historical_years": 50.0,
  "minimum_magnitude": 4.5
}
```

**Field Reference:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `latitude` | float | required | Latitude (WGS84) |
| `longitude` | float | required | Longitude (WGS84) |
| `search_radius_km` | float | 100.0 | Search radius for earthquakes |
| `historical_years` | float | 50.0 | Years of historical catalog |
| `minimum_magnitude` | float | 4.5 | Minimum magnitude to include |

**Response (200):**
```json
{
  "location": {
    "latitude": 23.8103,
    "longitude": 90.4125,
    "place_name": "Grid Reference [23.8103, 90.4125]"
  },
  "hazard": {
    "overall_score": 45.2,
    "hazard_level": "Moderate",
    "confidence": 0.95
  },
  "indicators": {
    "seismic_zone": {
      "value": "Zone Moderate",
      "classification": "Moderate regional seismic energy buildup",
      "color": "yellow"
    },
    "historical_activity": {
      "value": "12 events analyzed",
      "classification": "Moderate historical activity density",
      "color": "yellow"
    },
    "soil_liquefaction": {
      "value": "Silty Loam",
      "classification": "Moderate Liquefaction Risk",
      "color": "yellow"
    },
    "fault_proximity": {
      "value": "45.2 km",
      "classification": "Proximity to Himalayan Main Frontal Thrust (Moderate Proximity)",
      "color": "yellow"
    }
  },
  "statistics": {
    "total_events_analyzed": 12,
    "catalog_span_years": 50,
    "nearest_event_km": 15.3,
    "largest_historical_earthquake": 7.2,
    "closest_earthquake_km": 15.3,
    "events_per_year": 0.24,
    "mean_magnitude": 5.1,
    "max_magnitude": 7.2,
    "mean_distance_km": 62.1,
    "mean_depth_km": 18.5,
    "recurrence_m6_years": 28.5
  },
  "environmental_context": {
    "hazard_score": 45.2,
    "hazard_level": "Moderate",
    "historical_activity": {
      "classification": "Moderate",
      "events_within_radius": 12,
      "largest_magnitude": 7.2
    },
    "faults": {
      "distance_km": 45.2,
      "classification": "Moderate Proximity"
    },
    "soil": {
      "classification": "Moderate Liquefaction Risk",
      "dominant_soil": "Silty Loam"
    },
    "ground_motion": {
      "estimated_mmi": 7.5,
      "estimated_pga_g": 0.18,
      "confidence": 0.95
    },
    "summary": [
      "The geographic query location has a calibrated overall Seismic Hazard Score of 45.2/100, resulting in a 'Moderate' classification.",
      "Proximity risk is dominated by the Himalayan Main Frontal Thrust fault system located 45.2 km away, representing a 'Moderate Proximity' rating.",
      "Local surface soil texture consists of Silty Loam with a loose bulk density of 1.32 g/cm³, causing a 'Moderate Liquefaction Risk' profile with a seismic wave amplification factor of 1.15x.",
      "Historical earthquake record shows 12 analyzed events of M4.5+ within a 100km radius over the past 50 years. The largest event registered magnitude M7.2 located 15.3km away."
    ]
  },
  "events": [
    {
      "id": "us12345",
      "magnitude": 6.8,
      "distance_km": 15.3,
      "depth_km": 12.0,
      "date": "2015-04-25T06:11:26Z",
      "place": "25km NE of Kathmandu, Nepal",
      "individual_contribution": 0.045,
      "distance_weight": 0.72,
      "depth_weight": 0.85,
      "age_weight": 0.92,
      "magnitude_weight": 3.32
    }
  ],
  "metadata": {
      "warnings": [],
      "execution_time_seconds": 3.42,
      "api_status": {
        "USGS_Catalog": "success",
        "SoilGrids": "success"
      },
      "model_version": "v1.1.2-deterministic",
      "degraded": false
    }
  }
  ```

  **Degraded Mode Response Example** (when SoilGrids times out):
  ```json
  {
    "location": {
      "latitude": 16.84,
      "longitude": 96.17,
      "place_name": "Grid Reference [16.8400, 96.1700]"
    },
    "hazard": {
      "overall_score": 49.9,
      "hazard_level": "Moderate",
      "confidence": 0.85
    },
    "indicators": {
      "seismic_zone": {
        "value": "Zone Moderate",
        "classification": "Moderate regional seismic energy buildup",
        "color": "yellow"
      },
      "historical_activity": {
        "value": "8 events analyzed",
        "classification": "Moderate historical activity density",
        "color": "yellow"
      },
      "soil_liquefaction": {
        "value": "Clay Loam",
        "classification": "Moderate Liquefaction Risk",
        "color": "yellow"
      },
      "fault_proximity": {
        "value": "65.2 km",
        "classification": "Proximity to Sagaing Fault (Moderate Proximity)",
        "color": "yellow"
      }
    },
    "statistics": {
      "largest_historical_earthquake": 6.8,
      "closest_earthquake_km": 42.1,
      "average_depth_km": 15.2,
      "average_magnitude": 5.1,
      "median_magnitude": 5.0,
      "events_analyzed": 8,
      "catalog_span_years": 50,
      "nearest_fault_distance_km": 65.2,
      "estimated_recurrence_interval_years": 142.3,
      "soil_classification": "Clay Loam"
    },
    "environmental_context": {
      "hazard_score": 49.9,
      "hazard_level": "Moderate",
      "historical_activity": {
        "classification": "Moderate",
        "events_within_radius": 8,
        "largest_magnitude": 6.8
      },
      "faults": {
        "distance_km": 65.2,
        "classification": "Moderate Proximity"
      },
      "soil": {
        "classification": "Moderate Liquefaction Risk",
        "dominant_soil": "Clay Loam"
      },
      "ground_motion": {
        "estimated_mmi": 6.2,
        "estimated_pga_g": 0.08,
        "confidence": 0.85
      },
      "summary": [
        "The geographic query location has a calibrated overall Seismic Hazard Score of 49.9/100, resulting in a 'Moderate' classification.",
        "Proximity risk is dominated by the Sagaing Fault fault system located 65.2 km away, representing a 'Moderate Proximity' rating.",
        "Local surface soil texture consists of Clay Loam (source: Deterministic Coastal/Alluvial Heuristic (Fallback) — Irrawaddy Delta / Yangon), causing a 'Moderate Liquefaction Risk' profile with a seismic wave amplification factor of 1.15x.",
        "Historical earthquake record shows 8 analyzed events of M4.5+ within a 100km radius over the past 50 years. The largest event registered magnitude M6.8 located 42.1km away."
      ]
    },
    "events": [...],
    "metadata": {
      "warnings": [
        "SoilGrids API query failed or timed out. Deterministic Coastal/Alluvial Heuristic (Fallback) — Irrawaddy Delta / Yangon utilized."
      ],
      "execution_time_seconds": 12.04,
      "api_status": {
        "USGS_Catalog": "success",
        "SoilGrids": "fallback",
        "engine": "normal"
      },
      "model_version": "v1.1.2-deterministic",
      "degraded": true
    }
  }
  ```

  **Response Fields:**
```bash
curl -X POST http://localhost:8000/api/hazard/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 23.8103,
    "longitude": 90.4125,
    "search_radius_km": 100,
    "historical_years": 50,
    "minimum_magnitude": 4.5
  }'
```

---

### 3. LLM Analysis

#### `POST /api/llm/analysis`

Generate AI-powered risk interpretation and recommendations.

**Tags:** `LLM Service`

**Request Body:**
```json
{
  "building_context": {
    "structural": {
      "floors": 2,
      "age_years": 25,
      "floor_area_sq_feets": 1200,
      "height_feets": 24
    },
    "material": {
      "roof_type": "Corrugated Galvanized Iron (CGI) sheets",
      "foundation_type": "Reinforced Concrete (RC) / Cement",
      "ground_floor_type": "Reinforced Concrete (RC) slab floor"
    },
    "substructure": {
      "mud_mortar_stone": false,
      "cement_brick": false,
      "rc_engineered": true,
      "rc_non_engineered": false,
      "adobe_mud": false,
      "timber": false
    }
  },
  "environmental_context": {
    "hazard_score": 45.2,
    "hazard_level": "Moderate",
    "historical_activity": {
      "classification": "Moderate",
      "events_within_radius": 12,
      "largest_magnitude": 7.2
    },
    "faults": {
      "distance_km": 45.2,
      "classification": "Moderate Proximity"
    },
    "soil": {
      "classification": "Moderate Liquefaction Risk",
      "dominant_soil": "Silty Loam"
    },
    "ground_motion": {
      "estimated_mmi": 7.5,
      "estimated_pga_g": 0.18,
      "confidence": 0.95
    },
    "summary": [
      "The geographic query location has a calibrated overall Seismic Hazard Score of 45.2/100..."
    ]
  }
}
```

**Response (200):**
```json
{
  "summary": [
    {
      "text": "The building uses RC engineered construction which provides good ductility and seismic performance.",
      "evidence_ids": ["vuln-rc-engineered__chunk_0"]
    },
    {
      "text": "Moderate hazard level combined with engineered structure suggests manageable risk with proper maintenance.",
      "evidence_ids": ["env-hazard-moderate__chunk_1"]
    }
  ],
  "recommendations": [
    {
      "priority": "High",
      "title": "Verify Seismic Detailing Compliance",
      "description": "Confirm the RC frame meets MNBC 2016 ductile detailing requirements for beam-column joints and column confinement.",
      "evidence_ids": ["mitigation-rc-detailing__chunk_0"]
    },
    {
      "priority": "Medium",
      "title": "Soil-Structure Interaction Assessment",
      "description": "Given moderate liquefaction risk, evaluate foundation design for potential soil amplification effects.",
      "evidence_ids": ["env-soil-liquefaction__chunk_0"]
    }
  ],
  "risk_interpretation": {
    "structural_assessment": "The building employs RC engineered superstructure with CGI roof and RC foundation/floor system. This combination provides good lateral force resistance and ductility. The primary concern is verification of seismic detailing compliance.",
    "environmental_assessment": "The site experiences Moderate seismic hazard (45.2/100) driven by proximity to the Himalayan thrust system and moderate historical seismicity. Soil conditions indicate moderate liquefaction potential which could amplify ground motions.",
    "overall_reasoning": "An engineered RC structure in a moderate hazard zone with liquefaction-susceptible soils. The building's structural system is fundamentally sound, but the soil hazard introduces uncertainty in ground motion amplification. Risk is manageable with verification of detailing and foundation assessment."
  },
  "confidence": 0.87
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `summary` | array | Key findings with `evidence_ids` linking to knowledge base |
| `recommendations` | array | Prioritized actions with `priority` (High/Medium/Low), `title`, `description`, `evidence_ids` |
| `risk_interpretation` | object | `structural_assessment`, `environmental_assessment`, `overall_reasoning` |
| `confidence` | float | 0.0–1.0 confidence in the analysis |

---

### 4. Complete Assessment Pipeline (SSE)

#### `POST /api/assessment/process`

Orchestrate the full assessment pipeline with Server-Sent Events streaming.

**Tags:** `Orchestration`, `Database`

**Request Body:**
```json
{
  "latitude": 23.8103,
  "longitude": 90.4125,
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
  "has_superstructure_timber": 0
}
```

**Response: `text/event-stream`**

**SSE Event Format:**
```
data: {"type": "stage_started", "stage": "initializing", "status": "Preparing your assessment..."}

data: {"type": "stage_completed", "stage": "initializing"}

data: {"type": "stage_started", "stage": "resilience", "status": "Assessing building resilience..."}
data: {"type": "stage_started", "stage": "hazard", "status": "Running environmental hazard engine..."}

data: {"type": "stage_completed", "stage": "resilience"}
data: {"type": "stage_completed", "stage": "hazard"}

data: {"type": "stage_started", "stage": "llm", "status": "Generating AI feedback..."}
data: {"type": "stage_completed", "stage": "llm"}

data: {"type": "stage_started", "stage": "saving", "status": "Saving your assessment..."}
data: {"type": "stage_completed", "stage": "saving"}

data: {"type": "complete", "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
```

**Event Types:**

| Event | Fields | Description |
|-------|--------|-------------|
| `stage_started` | `stage`, `status` | Stage beginning |
| `stage_completed` | `stage` | Stage finished successfully |
| `complete` | `assessment_id` | Full pipeline done, ID for retrieval |
| `error` | `detail` | Pipeline failed |

**Stages & Typical Duration:**

| Stage | Duration | Parallel? |
|-------|----------|-----------|
| `initializing` | ~50ms | No |
| `resilience` | ~200ms | Yes (with hazard) |
| `hazard` | 3–8s | Yes (with resilience) |
| `llm` | 3–8s | No |
| `saving` | ~100ms | No |

**Example Client Consumption (JavaScript):**
```javascript
const response = await fetch('http://localhost:8000/api/assessment/process', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6));
      console.log(`[${event.type}]`, event);
      
      if (event.type === 'complete') {
        // Fetch full result from /api/assessment/{id}
      }
    }
  }
}
```

**Example cURL (shows raw SSE):**
```bash
curl -N -X POST http://localhost:8000/api/assessment/process \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 23.8103,
    "longitude": 90.4125,
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
    "has_superstructure_timber": 0
  }'
```

---

### 5. Save Assessment

#### `POST /api/assessment/save`

Persist a complete assessment to the database.

**Tags:** `Orchestration`, `Database`

**Request Body:**
```json
{
  "profile": { /* BuildingInput */ },
  "building": { /* ResilienceAssessmentResponse */ },
  "hazard": { /* HazardReport */ },
  "llm": { /* LLMAnalysisOutput */ },
  "evidence": {
    "chunk_id_1": { /* EvidenceCitation */ }
  }
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Assessment successfully saved.",
  "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-07-26T12:34:56.789Z"
}
```

---

### 6. Retrieve Assessment

#### `GET /api/assessment/{assessment_id}`

Fetch a saved assessment by UUID.

**Tags:** `Orchestration`, `Database`

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `assessment_id` | UUID | Assessment identifier |

**Response (200):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-07-26T12:34:56.789Z",
  "place_name": "Dhaka, Bangladesh",
  "latitude": 23.8103,
  "longitude": 90.4125,
  "resilience_score": 72.5,
  "hazard_score": 45.2,
  "hazard_level": "Moderate",
  "profile": { /* BuildingInput */ },
  "building": { /* ResilienceAssessmentResponse */ },
  "hazard": { /* HazardReport */ },
  "llm": { /* LLMAnalysisOutput + evidence */ },
  "model_version": "v1.1.2-deterministic",
  "execution_time_seconds": 12.34
}
```

**Response (404):**
```json
{
  "detail": "Assessment with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890 not found."
}
```

---

## Data Models Reference

### BuildingInput
See `/api/resilience/assess` request body.

### HazardInput
See `/api/hazard/calculate` request body.

### ResilienceAssessmentResponse
See `/api/resilience/assess` response.

### HazardReport
See `/api/hazard/calculate` response.

### LLMAnalysisInput
```json
{
  "building_context": { /* BuildingLLMContext */ },
  "environmental_context": { /* EnvironmentalContext */ }
}
```

### LLMAnalysisOutput
```json
{
  "summary": [
    { "text": "string", "evidence_ids": ["string"] }
  ],
  "recommendations": [
    { "priority": "High|Medium|Low", "title": "string", "description": "string", "evidence_ids": ["string"] }
  ],
  "risk_interpretation": {
    "structural_assessment": "string",
    "environmental_assessment": "string",
    "overall_reasoning": "string"
  },
  "confidence": 0.87
}
```

### AssessmentRequest
Combines `BuildingInput` + `HazardInput` (latitude, longitude).

### SaveAssessmentRequest
```json
{
  "profile": "BuildingInput",
  "building": "ResilienceAssessmentResponse",
  "hazard": "HazardReport",
  "llm": "LLMAnalysisOutput",
  "evidence": { "chunk_id": "EvidenceCitation" }
}
```

### EvidenceCitation
```json
{
  "chunk_id": "string",
  "source_title": "string",
  "source_org": "string",
  "source_url": "string",
  "category": "string",
  "excerpt": "string",
  "relevance_score": 0.85
}
```

---

## Rate Limits & Performance

| Endpoint | Typical Latency | External Calls |
|----------|-----------------|----------------|
| `/api/resilience/assess` | ~200ms | None (in-process ML) |
| `/api/hazard/calculate` | 3–8s | USGS, SoilGrids, ShakeMap |
| `/api/llm/analysis` | 3–8s | Gemini API (+ retrieval) |
| `/api/assessment/process` | 6–17s | All of above |

**Recommendations:**
- Cache hazard results for repeated locations (TTL: 24h)
- Use SSE endpoint for UX; poll `/api/assessment/{id}` for completion
- Production: Run multiple uvicorn workers for ML concurrency

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2026-07-26 | Added SSE streaming, evidence citations, Neon PG |
| 1.1.0 | 2026-07-15 | Hazard engine v1.1, RAG retrieval |
| 1.0.0 | 2026-06-29 | Initial ML + hazard + basic LLM |