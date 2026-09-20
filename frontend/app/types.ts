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
  has_superstructure_stone_flag: 0 | 1;
  has_superstructure_cement_mortar_stone: 0 | 1;
  has_superstructure_mud_mortar_brick: 0 | 1;
  has_superstructure_bamboo: 0 | 1;
  has_superstructure_other: 0 | 1;
  land_surface_condition: "Flat" | "Moderate slope" | "Steep slope";
  position: "Not attached" | "Attached-1 side" | "Attached-2 side" | "Attached-3 side";
  plan_configuration: string;
  other_floor_type: string;
  area_sq_ft: number;
  height_ft: number;
}

export interface SelectionOption {
  value: string;
  label: string;
  encodedValue: string;
  description?: string;
}

// Codes and their meanings were verified against the training data on 2026-09-16 (joint
// distribution + prevalence + measured damage rank, all three agreeing). `encodedValue` is the code
// actually sent to the API and consumed by the model — never change it, only the labels.
export const FOUNDATION_OPTIONS: SelectionOption[] = [
  { value: "reinforced_concrete", label: "Reinforced Concrete Foundation", encodedValue: "i", description: "Rigid footing suitable for high lateral seismic loads." },
  { value: "cement_stone_masonry", label: "Cement-Stone Masonry Foundation", encodedValue: "u", description: "Stone units laid in cement mortar; semi-rigid." },
  { value: "bamboo_timber", label: "Bamboo / Timber Foundation", encodedValue: "w", description: "Wooden posts or piles; susceptible to rot or shifting unless anchored." },
  { value: "mud_stone_masonry", label: "Mud-Stone Foundation", encodedValue: "r", description: "Unreinforced stone in mud mortar; high seismic vulnerability." },
  { value: "other_foundation", label: "Other / Unclassified Foundation", encodedValue: "h", description: "None of the four named foundations; treat as non-engineered." },
];

export const ROOF_OPTIONS: SelectionOption[] = [
  { value: "reinforced_concrete_roof", label: "Reinforced Concrete Slab Roof (RCC)", encodedValue: "x", description: "Heavy cast slab providing robust diaphragm; safest when anchored to RC columns." },
  { value: "light_bamboo_timber_roof", label: "Bamboo / Timber — Light Roof (thatch, light tile, CGI/tin)", encodedValue: "n", description: "Light cladding class; low mass, so low inertial demand on the walls. Enter corrugated metal (CGI) roofs here." },
  { value: "heavy_bamboo_timber_roof", label: "Bamboo / Timber — Heavy Roof (thick mud-covered timber)", encodedValue: "q", description: "Heavy traditional roof; raises the centre of mass and shows the worst damage of the three roof types in the 2015 Nepal data." },
];

export const GROUND_FLOOR_OPTIONS: SelectionOption[] = [
  { value: "reinforced_concrete_floor", label: "Reinforced Concrete Floor", encodedValue: "v", description: "Concrete slab floor; provides strong lower-level rigidity." },
  { value: "other_floor", label: "Other / Unclassified Floor", encodedValue: "m", description: "Alternative floor compositions." },
  { value: "timber_floor", label: "Timber Floor", encodedValue: "z", description: "Suspended wooden floor; flexible." },
  { value: "brick_stone", label: "Brick / Stone Floor", encodedValue: "x", description: "Masonry tiles or cobblestone; susceptible to shifting under dynamic loading." },
  { value: "mud_floor", label: "Mud Floor", encodedValue: "f", description: "Compacted soil; no structural shear transmission." },
];

export interface BuildingLLMContext {
  structural: Record<string, any>;
  material: Record<string, any>;
  substructure: Record<string, any>;
  /** Damage-model output: expected grade, grade distribution, severe-damage probability. */
  damage?: Record<string, any>;
}

export interface ResilienceAssessmentResponse {
  status: string;
  resilience_score: number;
  building_llm_context: BuildingLLMContext;
  /** Damage model v3 outputs. Absent on assessments saved before the model change. */
  model_version?: string | null;
  expected_grade?: number | null;
  grade_class?: number | null;
  probabilities?: Record<string, number> | null;
  p_severe_grade45?: number | null;
  used_fallback_model?: boolean | null;
  flags?: string[] | null;
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
  /** The catalogued event that governs the reported ground motion (absent when none in radius). */
  governing_event?: {
    id?: string;
    magnitude: number;
    distance_km: number;
    depth_km: number;
    date?: string;
    place?: string;
  } | null;
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
  priority: 'red' | 'orange' | 'yellow' | 'green';
  title: string;
  description: string;
  evidence_ids?: string[];
}

export interface SummaryItem {
  text: string;
  evidence_ids?: string[];
}

export interface RiskInterpretation {
  structural_assessment: string;
  environmental_assessment: string;
  overall_reasoning: string;
}

export interface EvidenceCitation {
  chunk_id: string;
  source_title: string;
  source_org: string;
  source_url: string;
  category: string;
  excerpt: string;
  relevance_score: number;
}

export interface LLMAnalysisOutput {
  summary: SummaryItem[];
  recommendations: LLMRecommendation[];
  risk_interpretation: RiskInterpretation | Record<string, any>;
  confidence: number;
  evidence?: Record<string, EvidenceCitation>;
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
  has_superstructure_stone_flag: number;
  has_superstructure_cement_mortar_stone: number;
  has_superstructure_mud_mortar_brick: number;
  has_superstructure_bamboo: number;
  has_superstructure_other: number;
  land_surface_condition: string;
  position: string;
  plan_configuration: string;
  other_floor_type: string;
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
    has_superstructure_stone_flag: number;
    has_superstructure_cement_mortar_stone: number;
    has_superstructure_mud_mortar_brick: number;
    has_superstructure_bamboo: number;
    has_superstructure_other: number;
    land_surface_condition: string;
    position: string;
    plan_configuration: string;
    other_floor_type: string;
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
  llm: LLMAnalysisOutput & { evidence?: Record<string, EvidenceCitation> };
  model_version?: string | null;
  execution_time_seconds?: number | null;
}