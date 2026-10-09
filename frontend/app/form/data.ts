import type { FormFields } from "./schema";

/**
 * Default form state — a worst-case screening scenario.
 *
 * Location: Sagaing town, Sagaing Region, Myanmar — directly on the Sagaing
 * Fault (1,400 km right-lateral strike-slip; source of the 2025 Mw 7.7
 * earthquake, see backend/data/knowledge/local_context/sagaing_fault.md).
 *
 * Building: the archetypal worst performer in the 2015 Nepal training data —
 * a ≥3-storey, pre-code, unreinforced mud-mortar stone house with a heavy
 * timber roof, mud floors, an irregular plan, on a steep slope and attached
 * on three sides.
 */
export const DEFAULT_FORM_VALUES: FormFields = {
    latitude: 21.97, // Sagaing town — directly on the Sagaing Fault
    longitude: 95.986,
    count_floors_pre_eq: 3, // 3+ storeys is the worst-performing band for mud-mortar stone
    age: 75, // old, pre-code, no seismic detailing
    foundation_type: "r", // mud-stone masonry — "high seismic vulnerability"
    roof_type: "q", // heavy bamboo/timber — worst roof type in the 2015 Nepal data
    ground_floor_type: "f", // mud floor — compacted soil, no shear transmission
    has_superstructure_mud_mortar_stone: 1, // worst-performing superstructure material
    has_superstructure_rc_engineered: 0,
    has_superstructure_cement_mortar_brick: 0,
    has_superstructure_rc_non_engineered: 0,
    has_superstructure_adobe_mud: 0,
    has_superstructure_timber: 0,
    has_superstructure_stone_flag: 0,
    has_superstructure_cement_mortar_stone: 0,
    has_superstructure_mud_mortar_brick: 0,
    has_superstructure_bamboo: 0,
    has_superstructure_other: 0,
    land_surface_condition: "Steep slope", // landslide-prone, amplifies shaking
    position: "Attached-3 side", // crowded on three sides — high pounding risk
    plan_configuration: "H-shape", // irregular plan — re-entrant corners, torsional response
    other_floor_type: "TImber/Bamboo-Mud", // weak heavy traditional floors (value matches schema enum)
    area_sq_ft: 1500, // standard detached house footprint default
    height_ft: 36, // 3-story building height (12 ft per floor)
};

export const plinchAreaTemplates = [
    {
        label: "Cabin / Cottage",
        value: 600,
    },
    {
        label: "Standard Home",
        value: 1500,
    },
    {
        label: "Large House",
        value: 2500,
    },
    {
        label: "Large Res / Commercial",
        value: 4000,
    },
];

export const heightTemplates = [
    {
        label: "1-Story Building",
        value: 12,
    },
    {
        label: "2-Story Building",
        value: 24,
    },
    {
        label: "3-Story Building",
        value: 36,
    },
    {
        label: "Commercial Block",
        value: 60,
    },
];

export const LAND_SURFACE_OPTIONS = [
    {
        value: "Flat",
        label: "Flat",
        description: "Level ground — standard shaking conditions",
    },
    {
        value: "Moderate slope",
        label: "Moderate slope",
        description: "Gentle incline — may amplify shaking",
    },
    {
        value: "Steep slope",
        label: "Steep slope",
        description: "Significant gradient — higher landslide risk",
    },
] as const;

export const POSITION_OPTIONS = [
    {
        value: "Not attached",
        label: "Not attached",
        description: "Standalone building, no pounding from neighbours",
    },
    {
        value: "Attached-1 side",
        label: "Attached — 1 side",
        description: "Touching one neighbouring building",
    },
    {
        value: "Attached-2 side",
        label: "Attached — 2 sides",
        description: "Sandwiched between two neighbours",
    },
    {
        value: "Attached-3 side",
        label: "Attached — 3 sides",
        description: "Crowded on three sides — high pounding risk",
    },
] as const;

export const PLAN_CONFIGURATION_OPTIONS = [
    { value: "Rectangular", label: "Rectangular" },
    { value: "Square", label: "Square" },
    { value: "L-shape", label: "L-shape" },
    { value: "T-shape", label: "T-shape" },
    { value: "U-shape", label: "U-shape" },
    { value: "E-shape", label: "E-shape" },
    { value: "H-shape", label: "H-shape" },
    { value: "Multi-projected", label: "Multi-projected" },
    { value: "Building with Central Courtyard", label: "Courtyard" },
    { value: "Others", label: "Others" },
] as const;

export const OTHER_FLOOR_TYPE_OPTIONS = [
    {
        value: "Timber-Planck",
        label: "Timber-Plank",
        description: "Wooden plank flooring on upper levels",
    },
    {
        value: "TImber/Bamboo-Mud",
        label: "Timber/Bamboo-Mud",
        description: "Traditional timber or bamboo with mud infill",
    },
    {
        value: "RCC/RB/RBC",
        label: "RCC / RB / RBC",
        description: "Reinforced concrete or brick-concrete composite",
    },
    {
        value: "Not applicable",
        label: "Not applicable",
        description: "Single-storey building — no upper floor",
    },
] as const;
