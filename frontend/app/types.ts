export interface AssessmentPayload {
  latitude: number;
  longitude: number;
  count_floors_pre_eq: number;
  age: number;
  foundation_type: "i" | "u" | "w" | "r" | "h";
  roof_type: "q" | "x" | "n";
  ground_floor_type: "x" | "v" | "m" | "f" | "z";
  has_superstructure_mud_mortar_stone: 0 | 1;
  has_superstructure_rc_engineered: 0 | 1;
  has_superstructure_cement_mortar_brick: 0 | 1;
  has_superstructure_rc_non_engineered: 0 | 1;
  has_superstructure_adobe_mud: 0 | 1;
  has_superstructure_timber: 0 | 1;
  area_sq_ft: number;
  height_ft: number;
}

export interface SelectionOption {
  value: string;
  label: string;
  encodedValue: string;
  description?: string;
}

export const FOUNDATION_OPTIONS: SelectionOption[] = [
  { value: "reinforced_concrete", label: "Reinforced Concrete Foundation", encodedValue: "i", description: "Rigid footing suitable for high lateral seismic loads." },
  { value: "cement_stone_masonry", label: "Cement-Stone Masonry Foundation", encodedValue: "u", description: "Stone units laid in cement mortar; semi-rigid." },
  { value: "timber", label: "Timber Foundation", encodedValue: "w", description: "Wooden posts or piles; susceptible to rot or shifting unless anchored." },
  { value: "mud_stone_masonry", label: "Mud-Stone Foundation", encodedValue: "r", description: "Unreinforced stone in mud mortar; high seismic vulnerability." },
  { value: "bamboo_adobe", label: "Bamboo / Adobe Foundation", encodedValue: "h", description: "Lightweight or natural materials; highly deformable." },
];

export const ROOF_OPTIONS: SelectionOption[] = [
  { value: "corrugated_metal", label: "Corrugated Metal Roof", encodedValue: "q", description: "Lightweight steel sheet cladding on timber or metal trusses." },
  { value: "reinforced_concrete_roof", label: "Reinforced Concrete Roof", encodedValue: "x", description: "Heavy cast slab providing robust diaphragm but increasing building weight." },
  { value: "traditional_bamboo_timber", label: "Traditional Bamboo / Timber Roof", encodedValue: "n", description: "Thatch or light wood tiling; flexible but can collapse if poorly connected." },
];

export const GROUND_FLOOR_OPTIONS: SelectionOption[] = [
  { value: "reinforced_concrete_floor", label: "Reinforced Concrete Floor", encodedValue: "x", description: "Slab-on-grade; provides strong lower-level rigidity." },
  { value: "brick_stone", label: "Brick / Stone Floor", encodedValue: "v", description: "Masonry tiles or cobblestone; susceptible to shifting under dynamic loading." },
  { value: "timber_floor", label: "Timber Floor", encodedValue: "m", description: "Suspended wooden floor; flexible." },
  { value: "mud_floor", label: "Mud Floor", encodedValue: "f", description: "Compacted soil; no structural shear transmission." },
  { value: "other_floor", label: "Other", encodedValue: "z", description: "Alternative floor compositions." },
];

export interface BuildingLLMContext {
  structural: Record<string, any>;
  material: Record<string, any>;
  substructure: Record<string, any>;
}

export interface ResilienceAssessmentResponse {
  status: string;
  resilience_score: number;
  building_llm_context: BuildingLLMContext;
}

export interface IndicatorItem {
  value: any;
  classification: string;
  color: 'green' | 'yellow' | 'red' | string;
}

export interface Indicators {
  seismic_zone: IndicatorItem;
  historical_activity: IndicatorItem;
  soil_liquefaction: IndicatorItem;
  fault_proximity: IndicatorItem;
}

export interface ProcessedEvent {
  id: string;
  magnitude: number;
  distance_km: number;
  depth_km: number;
  date: string;
  place: string;
  individual_contribution: number;
  distance_weight: number;
  depth_weight: number;
  age_weight: number;
  magnitude_weight: number;
}

export interface LLMHistoricalActivity {
  classification: string;
  events_within_radius: number;
  largest_magnitude?: number | null;
}

export interface LLMFaultContext {
  distance_km: number;
  classification: string;
}

export interface LLMSoilContext {
  classification: string;
  dominant_soil: string;
}

export interface LLMGroundMotionContext {
  estimated_mmi: number;
  estimated_pga_g: number;
  confidence: number;
}

export interface EnvironmentalContext {
  hazard_score: number;
  hazard_level: string;
  historical_activity: LLMHistoricalActivity;
  faults: LLMFaultContext;
  soil: LLMSoilContext;
  ground_motion: LLMGroundMotionContext;
  summary: string[];
}

export interface HazardReport {
  location: Record<string, any>;
  hazard: Record<string, any>;
  indicators: Indicators;
  statistics: Record<string, any>;
  environmental_context: EnvironmentalContext;
  events: ProcessedEvent[];
  metadata: Record<string, any>;
}

export interface LLMRecommendation {
  priority: 'red' | 'yellow' | 'blue';
  title: string;
  description: string;
}

export interface LLMAnalysisOutput {
  summary: string[];
  recommendations: LLMRecommendation[];
  risk_interpretation: Record<string, any>;
  confidence: number;
}

export interface AssessmentRequest {
  latitude: number;
  longitude: number;
  count_floors_pre_eq: number;
  age: number;
  area_sq_ft: number;
  height_ft: number;
  foundation_type: string;
  roof_type: string;
  ground_floor_type: string;
  has_superstructure_mud_mortar_stone: number;
  has_superstructure_rc_engineered: number;
  has_superstructure_cement_mortar_brick: number;
  has_superstructure_rc_non_engineered: number;
  has_superstructure_adobe_mud: number;
  has_superstructure_timber: number;
}

export interface BuildingInput {
    count_floors_pre_eq: number;
    age: number;
    area_sq_ft: number;
    height_ft: number;
    foundation_type: string;
    roof_type: string;
    ground_floor_type: string;
    has_superstructure_mud_mortar_stone: number;
    has_superstructure_rc_engineered: number;
    has_superstructure_cement_mortar_brick: number;
    has_superstructure_rc_non_engineered: number;
    has_superstructure_adobe_mud: number;
    has_superstructure_timber: number;
}

export interface AssessmentIDResponse {
  id: string;
  created_at: string;
  place_name?: string;
  latitude: number;
  longitude: number;
  resilience_score: number;
  hazard_score: number;
  hazard_level: string;
  profile: BuildingInput;
  building: ResilienceAssessmentResponse;
  hazard: HazardReport;
  llm: LLMAnalysisOutput;
  model_version?: string | null;
  execution_time_seconds?: number | null;
}