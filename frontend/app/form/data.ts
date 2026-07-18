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