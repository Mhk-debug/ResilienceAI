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