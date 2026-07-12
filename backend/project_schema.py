from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import List, Optional, Dict, Any

class BuildingInput(BaseModel):
    count_floors_pre_eq: int = Field(..., ge=1, le=10, description="Number of stories before the seismic event")
    age: int = Field(..., ge=0, le=999, description="Age of the building frame in years")
    area_sq_ft: int = Field(..., ge=70, le=5000, description="Floor area in square feets")
    height_ft: int = Field(..., ge=6, le=305, description="Height in feets")
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

class BuildingLLMContext(BaseModel):
    structural: Dict[str, Any]
    material: Dict[str, Any]
    substructure: Dict[str, Any]

class ResilienceAssessmentResponse(BaseModel):
    status: str
    resilience_score: float
    building_llm_context: BuildingLLMContext

class HazardInput(BaseModel):
    latitude: float
    longitude: float
    search_radius_km: Optional[float] = 100.0
    historical_years: Optional[float] = 50.0
    minimum_magnitude: Optional[float] = 4.5

class HazardReport(BaseModel):
    location: Dict[str, Any]
    hazard: Dict[str, Any]
    indicators: Dict[str, Any]
    statistics: Dict[str, Any]
    environmental_context: Dict[str, Any]
    events: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class LocationContext(BaseModel):
    latitude: float
    longitude: float
    place_name: str


class HazardLevelMetric(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="0-100 overall environmental seismic hazard score")
    hazard_level: str = Field(..., description="Classification: Very Low, Low, Moderate, High, Very High")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Quality indicator of input data density")


class IndicatorItem(BaseModel):
    value: Any = Field(..., description="The calculated value for the indicator")
    classification: str = Field(..., description="Risk or proximity classification")
    color: str = Field(..., description="Color code: green | yellow | red")


class Indicators(BaseModel):
    seismic_zone: IndicatorItem
    historical_activity: IndicatorItem
    soil_liquefaction: IndicatorItem
    fault_proximity: IndicatorItem


class ProcessedEvent(BaseModel):
    id: str
    magnitude: float
    distance_km: float
    depth_km: float
    date: str
    place: str
    individual_contribution: float
    distance_weight: float
    depth_weight: float
    age_weight: float
    magnitude_weight: float


# --- LLM-Friendly Environmental Context ---
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


class EnvironmentalContext(BaseModel):
    hazard_score: float
    hazard_level: str
    historical_activity: LLMHistoricalActivity
    faults: LLMFaultContext
    soil: LLMSoilContext
    ground_motion: LLMGroundMotionContext
    summary: List[str] = Field(..., description="Compact descriptive sentences suitable for direct prompt injection")

class LLMAnalysisInput(BaseModel):
    building_context: BuildingLLMContext
    environmental_context: EnvironmentalContext


class LLMRecommendation(BaseModel):
    priority: str  # "red" | "yellow" | "blue"
    title: str
    description: str


class LLMAnalysisOutput(BaseModel):
    summary: List[str]
    recommendations: List[LLMRecommendation]
    risk_interpretation: Dict[str, Any]
    confidence: float

class AssessmentRequest(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate for hazard calculation")
    longitude: float = Field(..., description="Longitude coordinate for hazard calculation")

    count_floors_pre_eq: int = Field(..., ge=1, le=10, description="Number of stories before the seismic event")
    age: int = Field(..., ge=0, le=999, description="Age of the building frame in years")
    area_sq_ft: int = Field(..., ge=70, le=5000, description="Floor area in square feets")
    height_ft: int = Field(..., ge=6, le=305, description="Height in feets")
    foundation_type: str = Field(..., min_length=1, max_length=1)
    roof_type: str = Field(..., min_length=1, max_length=1)
    ground_floor_type: str = Field(..., min_length=1, max_length=1)
    has_superstructure_mud_mortar_stone: int = Field(..., ge=0, le=1)
    has_superstructure_rc_engineered: int = Field(..., ge=0, le=1)
    has_superstructure_cement_mortar_brick: int = Field(..., ge=0, le=1)
    has_superstructure_rc_non_engineered: int = Field(..., ge=0, le=1)
    has_superstructure_adobe_mud: int = Field(..., ge=0, le=1)
    has_superstructure_timber: int = Field(..., ge=0, le=1)

class SaveAssessmentRequest(BaseModel):
    profile: BuildingInput
    building: ResilienceAssessmentResponse
    hazard: HazardReport
    llm: LLMAnalysisOutput

class AssessmentIDResponse(BaseModel):
    """Pydantic model representing the complete Assessment output."""
    id: UUID
    created_at: datetime
    place_name: str
    latitude: float
    longitude: float
    resilience_score: float
    hazard_score: float
    hazard_level: str
    
    # JSONB dictionaries
    profile: Dict[str, Any]
    building: Dict[str, Any]
    hazard: Dict[str, Any]
    llm: Dict[str, Any]
    
    model_version: Optional[str] = None
    execution_time_seconds: Optional[float] = None

    # This config tells Pydantic to read data directly from the SQLAlchemy ORM model properties
    model_config = ConfigDict(from_attributes=True)