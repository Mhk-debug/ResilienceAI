# Data Models Documentation

> **Pydantic models, internal data structures, and data transformations in the ResilienceAI backend**

---

## Overview

The codebase uses **Pydantic v2** for all request/response validation and internal data structures. Models are defined in `project_schema.py` with additional internal dataclasses in service modules.

---

## Core Request/Response Models (`project_schema.py`)

### 1. BuildingInput
**User-facing building parameters for ML inference.**

```python
class BuildingInput(BaseModel):
    count_floors_pre_eq: int = Field(..., ge=1, le=10)
    age: int = Field(..., ge=0, le=999)
    area_sq_ft: int = Field(..., ge=70, le=5000)
    height_ft: int = Field(..., ge=6, le=305)
    foundation_type: str = Field(..., min_length=1, max_length=1)
    roof_type: str = Field(..., min_length=1, max_length=1)
    ground_floor_type: str = Field(..., min_length=1, max_length=1)
    has_superstructure_mud_mortar_stone: int = Field(..., ge=0, le=1)
    has_superstructure_rc_engineered: int = Field(..., ge=0, le=1)
    has_superstructure_cement_mortar_brick: int = Field(..., ge=0, le=1)
    has_superstructure_rc_non_engineered: int = Field(..., ge=0, le=1)
    has_superstructure_adobe_mud: int = Field(..., ge=0, le=1)
    has_superstructure_timber: int = Field(..., ge=0, le=1)

    @field_validator('foundation_type', 'roof_type', 'ground_floor_type')
    @classmethod
    def validate_categorical_codes(cls, v: str) -> str:
        return v.lower()
```

**Validation:**
- All numeric fields have explicit bounds
- Categorical codes lowercased
- Material flags are 0/1 (exactly one should be 1 in practice)

> **Note:** The above shows the original 13 fields. The full 22-field contract (including `land_surface_condition`, `position`, `plan_configuration`, `other_floor_type`, and 5 additional superstructure flags) is defined in `backend/docs/model_v3_contract.md`.

---

### 2. HazardInput
**Parameters for hazard engine query.**

```python
class HazardInput(BaseModel):
    latitude: float
    longitude: float
    search_radius_km: Optional[float] = 100.0
    historical_years: Optional[float] = 50.0
    minimum_magnitude: Optional[float] = 4.5
```

---

### 3. BuildingLLMContext
**LLM-friendly building summary (from ML pipeline).**

```python
class BuildingLLMContext(BaseModel):
    structural: Dict[str, Any]
    material: Dict[str, Any]
    substructure: Dict[str, Any]
```

**Typical Content:**
```json
{
  "structural": {
    "floors": 2,
    "age_years": 25,
    "floor_area_sq_feets": 1200,
    "height_feets": 24
  },
  "material": {
    "roof_type": "Bamboo / Timber - light roof",
    "foundation_type": "Reinforced Concrete (RC) / Cement",
    "ground_floor_type": "Reinforced Concrete (RC) floor"
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
```

---

### 4. EnvironmentalContext
**LLM-friendly hazard summary (from hazard engine).**

```python
class EnvironmentalContext(BaseModel):
    hazard_score: float
    hazard_level: str
    historical_activity: LLMHistoricalActivity
    faults: LLMFaultContext
    soil: LLMSoilContext
    ground_motion: LLMGroundMotionContext
    summary: List[str]
```

**Sub-models:**
```python
class LLMHistoricalActivity(BaseModel):
    classification: str
    events_within_radius: int
    largest_magnitude: Optional[float] = None

class LLMFaultContext(BaseModel):
    distance_km: float
    classification: str

class LLMSoilContext(BaseModel):
    classification: str
    dominant_soil: str

class LLMGroundMotionContext(BaseModel):
    estimated_mmi: float
    estimated_pga_g: float
    confidence: float
```

---

### 5. ResilienceAssessmentResponse
**ML pipeline output + LLM context + damage distribution.**

```python
class ResilienceAssessmentResponse(BaseModel):
    status: str
    resilience_score: float
    building_llm_context: BuildingLLMContext
    model_version: Optional[str] = None
    expected_grade: Optional[float] = None
    grade_class: Optional[int] = None
    probabilities: Optional[Dict[str, float]] = None
    p_severe_grade45: Optional[float] = None
    used_fallback_model: bool = False
    flags: List[str] = []
```

---

### 6. HazardReport
**Full hazard engine output.**

```python
class HazardReport(BaseModel):
    location: Dict[str, Any]
    hazard: Dict[str, Any]
    indicators: Dict[str, Any]
    statistics: Dict[str, Any]
    environmental_context: Dict[str, Any]
    events: List[Dict[str, Any]]
    metadata: Dict[str, Any]
```

**Key nested structures:**

```python
# hazard
{
    "overall_score": 45.2,
    "hazard_level": "Moderate",
    "confidence": 0.95
}

# indicators
{
    "seismic_zone": {"value": "Zone Moderate", "classification": "...", "color": "yellow"},
    "historical_activity": {"value": "12 events", "classification": "...", "color": "yellow"},
    "soil_liquefaction": {"value": "Silty Loam", "classification": "...", "color": "yellow"},
    "fault_proximity": {"value": "45.2 km", "classification": "...", "color": "yellow"}
}
```

---

### 7. LLM Analysis Models

```python
class LLMAnalysisInput(BaseModel):
    building_context: BuildingLLMContext
    environmental_context: EnvironmentalContext

class SummaryItem(BaseModel):
    text: str
    evidence_ids: List[str] = []

class LLMRecommendation(BaseModel):
    priority: str
    title: str
    description: str
    evidence_ids: List[str] = []

class RiskInterpretation(BaseModel):
    structural_assessment: str
    environmental_assessment: str
    overall_reasoning: str

class LLMAnalysisOutput(BaseModel):
    summary: List[SummaryItem]
    recommendations: List[LLMRecommendation]
    risk_interpretation: RiskInterpretation
    confidence: float
```

---

### 8. Evidence Citation

```python
class EvidenceCitation(BaseModel):
    chunk_id: str
    source_title: str = ""
    source_org: str = ""
    source_url: str = ""
    category: str = ""
    excerpt: str = ""
    relevance_score: float = Field(0.0, ge=0.0, le=1.0)
```

---

### 9. Assessment Persistence Models

```python
class AssessmentRequest(BaseModel):
    latitude: float
    longitude: float
    count_floors_pre_eq: int
    age: int
    area_sq_ft: int
    height_ft: int
    foundation_type: str
    roof_type: str
    ground_floor_type: str
    has_superstructure_mud_mortar_stone: int
    has_superstructure_rc_engineered: int
    has_superstructure_cement_mortar_brick: int
    has_superstructure_rc_non_engineered: int
    has_superstructure_adobe_mud: int
    has_superstructure_timber: int

class SaveAssessmentRequest(BaseModel):
    profile: BuildingInput
    building: ResilienceAssessmentResponse
    hazard: HazardReport
    llm: LLMAnalysisOutput
    evidence: Dict[str, EvidenceCitation] = {}

class AssessmentIDResponse(BaseModel):
    id: UUID
    created_at: datetime
    place_name: str
    latitude: float
    longitude: float
    resilience_score: float
    hazard_score: float
    hazard_level: str
    profile: Dict[str, Any]
    building: Dict[str, Any]
    hazard: Dict[str, Any]
    llm: Dict[str, Any]
    model_version: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)
```

---

## Internal Data Structures (Dataclasses)

### RetrievalResult (`services/retrieval/retriever.py`)

```python
@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    channel: str = ""
```

### ChannelQuery (`services/retrieval/query_builder.py`)

```python
@dataclass
class ChannelQuery:
    query: str
    category_filter: List[str]
    tags_filter: Optional[List[str]] = None
    k: int = 2
    channel_name: str = ""
```

### KnowledgeChunk (`services/retrieval/chunk_loader.py`)

```python
@dataclass
class KnowledgeChunk:
    chunk_id: str
    doc_id: str
    category: str
    tags: List[str]
    title: str
    text: str
    source_title: str
    source_org: str
    source_url: str
    source_license: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Database ORM Model (`database/models.py`)

```python
class Assessment(Base):
    __tablename__ = "assessments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    place_name: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    resilience_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    hazard_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    hazard_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    profile: Mapped[dict] = mapped_column(JSONB, nullable=False)
    building: Mapped[dict] = mapped_column(JSONB, nullable=False)
    hazard: Mapped[dict] = mapped_column(JSONB, nullable=False)
    llm: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
```

---

## Data Transformations

### 1. BuildingInput → Damage Model Features
**Location:** `services/damage_model.py:DamageModel.build_features()`

```
BuildingInput (22 fields)
    → model_dump() → dict
    → app code → survey vocabulary mapping (foundation_type, roof_type, ground_floor_type)
    → one-hot categoricals (survey categories)
    → superstructure flags (11 binary fields)
    → derived features (storey_height_ft, slenderness, age_floors)
    → site term (epi_distance_km from hazard engine)
    → reindex(model_metadata.json["features"]) → 54-column DataFrame
```

### 2. Damage Model Output → ResilienceAssessmentResponse
**Location:** `services/resilience_service.py:predict_resilience()`

```
DamageModel.predict(payload, epi_distance_km)
    → 4 ordinal boosters → P(grade > k) for k=1..4
    → grade probabilities (5 grades, cumulative monotonicity enforced)
    → expected_grade = 1 + sum(P(grade > k))
    → resilience_score = 100 × (5 - expected_grade) / 4
    → BuildingLLMContext from raw_input + decode_building_feature + damage distribution
    → ResilienceAssessmentResponse
```

### 3. Hazard Engine → HazardReport + EnvironmentalContext
**Location:** `services/hazard_engine/engine.py:calculate_hazard()`

```
USGS events + SoilGrids + Faults + Scoring
    → calibrate_hazard_score → overall_score, level, confidence
    → build_indicators → 4 indicator objects
    → build_environmental_context → LLM-friendly summary
    → HazardReport (full) + EnvironmentalContext (LLM)
```

### 4. AssessmentRequest → Parallel Inputs
**Location:** `routes/assessment.py:process_assessment()`

```
AssessmentRequest (combined)
    → exclude lat/lon → BuildingInput
    → HazardInput(lat, lon, defaults)
    → hazard first: calculate_hazard_route
    → then building: calculate_pure_resilience (conditioned on site term)
    → merge → LLMAnalysisInput
```

### 5. LLM Output → Evidence Citations
**Location:** `services/llm_services.py:LLMService._build_evidence_map()`

```
LLMAnalysisOutput (with evidence_ids)
    + RetrievalResult[] (from retriever)
    → validate cited IDs against retrieved
    → build EvidenceCitation dict
    → merge into llm JSONB for storage
```

### 6. SaveAssessmentRequest → Database ORM
**Location:** `routes/assessment.py:save_assessment()`

```
SaveAssessmentRequest
    → model_dump(mode="json") each component
    → merge evidence into llm dict
    → geocode place_name
    → Assessment ORM with JSONB columns
    → db.add/commit/refresh
```

---

## Serialization Patterns

### Pydantic model_dump(mode="json")
Used for database storage to ensure JSON-serializable types:
- `datetime` → ISO string
- `UUID` → string
- `Enum` → value

```python
building = request.building.model_dump(mode="json")
hazard = request.hazard.model_dump(mode="json")
llm = request.llm.model_dump(mode="json")
```

### ORM → Response Model
`AssessmentIDResponse` uses `ConfigDict(from_attributes=True)` to read directly from SQLAlchemy ORM:

```python
assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
return assessment  # FastAPI auto-converts via from_attributes
```

---

## Validation Rules Summary

| Model | Key Validations |
|-------|-----------------|
| `BuildingInput` | All numeric bounds, categorical codes length=1, material flags 0/1 |
| `HazardInput` | Lat/lon required, optional params with defaults |
| `ResilienceAssessmentResponse` | Score 0-100, context structure |
| `HazardReport` | Nested dict structure matching engine output |
| `LLMAnalysisOutput` | Evidence IDs as string lists, confidence 0-1 |
| `AssessmentRequest` | Combines BuildingInput + lat/lon |
| `SaveAssessmentRequest` | All sub-models required, evidence optional |

---

## Adding New Fields

1. **Add to Pydantic model** in `project_schema.py`
2. **Update feature engineering** if ML input (`pipeline.py`)
3. **Update hazard engine** if environmental (`engine.py` + submodules)
4. **Update LLM schemas** if needed (`LLMAnalysisInput`, `EnvironmentalContext`)
5. **Update database** if persistence needed (add to `Assessment` ORM)
6. **Update validation script** (`scripts/validate_pipeline.py`)
7. **Test end-to-end**