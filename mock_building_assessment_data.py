from typing import List, Dict, Any, Optional

# Mock dataset containing 5 realistic structural configurations and their final risk metrics
MOCK_BUILDING_RISK_DATA: List[Dict[str, Any]] = [
    {
        "assessment_id": "EQ-2026-001",
        "timestamp": "2026-06-25T10:30:00Z",
        "location": {
            "latitude": 16.7753,
            "longitude": 96.1594,
            "display_name": "Downtown Yangon Region"
        },
        "building_characteristics": {
            "count_floors_pre_eq": 4,
            "age_years": 45,
            "foundation_type": "r",      # r = non-engineered reinforced concrete raft
            "roof_type": "n",            # n = ordinary/slates
            "ground_floor_type": "v",     # v = brick/concrete floor
            "other_floor_type": "q",      # q = timber beam/wood
            "plan_configuration": "u",    # u = irregular 'U' layout shape
            "position": "t",              # t = attached on both sides (row house)
            "superstructure_flags": {
                "has_superstructure_mud_mortar_stone": 0,
                "has_superstructure_cement_mortar_brick": 1,
                "has_superstructure_timber": 0,
                "has_superstructure_bamboo": 0
            },
            "maintenance_condition": "Poor (Visible foundational wall cracks)"
        },
        "risk_results": {
            "earthquake_risk_score": 82,   # Combined risk score (0-100)
            "risk_level": "Critical Risk"  # UI tier classification
        }
    },
    {
        "assessment_id": "EQ-2026-002",
        "timestamp": "2026-06-26T14:15:00Z",
        "location": {
            "latitude": 17.3333,
            "longitude": 96.4833,
            "display_name": "Bago Area"
        },
        "building_characteristics": {
            "count_floors_pre_eq": 2,
            "age_years": 12,
            "foundation_type": "i",      # i = engineered concrete piles/paddings
            "roof_type": "x",            # x = light reinforced/metal sheeting
            "ground_floor_type": "f",     # f = mud/brick/stone base
            "other_floor_type": "j",      # j = reinforced concrete slab
            "plan_configuration": "d",    # d = regular rectangular baseline layout
            "position": "s",              # s = detached/isolated structure
            "superstructure_flags": {
                "has_superstructure_mud_mortar_stone": 0,
                "has_superstructure_cement_mortar_brick": 1,
                "has_superstructure_timber": 1,
                "has_superstructure_bamboo": 0
            },
            "maintenance_condition": "Excellent (Recently reinforced)"
        },
        "risk_results": {
            "earthquake_risk_score": 54,
            "risk_level": "Moderate Risk"
        }
    },
    {
        "assessment_id": "EQ-2026-003",
        "timestamp": "2026-06-27T09:00:00Z",
        "location": {
            "latitude": 21.9588,
            "longitude": 96.0891,
            "display_name": "Mandalay Urban Outskirts"
        },
        "building_characteristics": {
            "count_floors_pre_eq": 5,
            "age_years": 35,
            "foundation_type": "w",      # w = traditional wooden posts
            "roof_type": "n",            # n = ordinary/slates
            "ground_floor_type": "f",     # f = mud/brick/stone base
            "other_floor_type": "q",      # q = timber beam/wood
            "plan_configuration": "u",    # u = irregular layout
            "position": "j",              # j = corner house block boundary
            "superstructure_flags": {
                "has_superstructure_mud_mortar_stone": 1,
                "has_superstructure_cement_mortar_brick": 0,
                "has_superstructure_timber": 0,
                "has_superstructure_bamboo": 1
            },
            "maintenance_condition": "Fair (Aged superstructure masonry)"
        },
        "risk_results": {
            "earthquake_risk_score": 69,
            "risk_level": "High Risk"
        }
    },
    {
        "assessment_id": "EQ-2026-004",
        "timestamp": "2026-06-28T11:45:00Z",
        "location": {
            "latitude": 19.7450,
            "longitude": 96.1219,
            "display_name": "Naypyidaw Central Residential"
        },
        "building_characteristics": {
            "count_floors_pre_eq": 1,
            "age_years": 8,
            "foundation_type": "i",      # i = engineered concrete piles
            "roof_type": "x",            # x = lightweight metal sheeting
            "ground_floor_type": "v",     # v = brick/concrete floor
            "other_floor_type": "j",      # j = reinforced concrete floor deck
            "plan_configuration": "d",    # d = regular rectangular layout
            "position": "s",              # s = isolated detached house
            "superstructure_flags": {
                "has_superstructure_mud_mortar_stone": 0,
                "has_superstructure_cement_mortar_brick": 1,
                "has_superstructure_timber": 0,
                "has_superstructure_bamboo": 0
            },
            "maintenance_condition": "Excellent (New structural design)"
        },
        "risk_results": {
            "earthquake_risk_score": 12,
            "risk_level": "Low Risk"
        }
    },
    {
        "assessment_id": "EQ-2026-005",
        "timestamp": "2026-06-29T08:20:00Z",
        "location": {
            "latitude": 20.1042,
            "longitude": 93.7314,
            "display_name": "Western Mountainous Zone"
        },
        "building_characteristics": {
            "count_floors_pre_eq": 2,
            "age_years": 28,
            "foundation_type": "r",      # r = non-engineered concrete raft
            "roof_type": "n",            # n = ordinary/slates
            "ground_floor_type": "f",     # f = mud/stone base
            "other_floor_type": "q",      # q = timber beam/wood
            "plan_configuration": "d",    # d = regular rectangular layout
            "position": "s",              # s = isolated detached house
            "superstructure_flags": {
                "has_superstructure_mud_mortar_stone": 1,
                "has_superstructure_cement_mortar_brick": 0,
                "has_superstructure_timber": 1,
                "has_superstructure_bamboo": 0
            },
            "maintenance_condition": "Fair (Rustic non-reinforced frame)"
        },
        "risk_results": {
            "earthquake_risk_score": 65,
            "risk_level": "High Risk"
        }
    }
]

def get_all_mock_building_risks() -> List[Dict[str, Any]]:
    """Returns the full mock architectural dataset with finalized risk scores."""
    return MOCK_BUILDING_RISK_DATA

def get_building_risk_by_id(assessment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single structural configuration profile by its unique assessment ID."""
    for building in MOCK_BUILDING_RISK_DATA:
        if building["assessment_id"] == assessment_id:
            return building
    return None

if __name__ == "__main__":
    print(f"Loaded {len(get_all_mock_building_risks())} building profiles with risk scores.")
    print("Example risk classification check:", get_all_mock_building_risks()[0]["risk_results"])