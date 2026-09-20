import type { FormFields } from "./schema";

export const DEFAULT_FORM_VALUES: FormFields = {
    latitude: 37.7749, // 45 Ward North Dagon Myanmar
    longitude: -122.4194,
    count_floors_pre_eq: 2,
    age: 25,
    foundation_type: "i",
    roof_type: "q",
    ground_floor_type: "x",
    has_superstructure_mud_mortar_stone: 0,
    has_superstructure_rc_engineered: 1,
    has_superstructure_cement_mortar_brick: 1,
    has_superstructure_rc_non_engineered: 0,
    has_superstructure_adobe_mud: 0,
    has_superstructure_timber: 0,
    has_superstructure_stone_flag: 0,
    has_superstructure_cement_mortar_stone: 0,
    has_superstructure_mud_mortar_brick: 0,
    has_superstructure_bamboo: 0,
    has_superstructure_other: 0,
    land_surface_condition: "Flat",
    position: "Not attached",
    plan_configuration: "Rectangular",
    other_floor_type: "Not applicable",
    area_sq_ft: 1500, // standard detached house footprint default
    height_ft: 24, // standard 2-story building height default (e.g. 12ft per floor)
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
