RICHTER_DATASET_MAPPINGS = {
    "foundation_type": {
        "r": {
            "description": "Mud mortar - Stone",
            "vulnerability_risk": "High",
            "notes": "Most common in rural Nepal; highly prone to dynamic shear failure."
        },
        "w": {
            "description": "Wooden / Timber foundation",
            "vulnerability_risk": "Medium",
            "notes": "Flexible; resilient against total collapse but highly prone to deformation."
        },
        "i": {
            "description": "Reinforced Concrete (RC) / Cement",
            "vulnerability_risk": "Low",
            "notes": "Modern engineered or rigid framed base foundation configuration."
        },
        "u": {
            "description": "Cement - Stone masonry composite",
            "vulnerability_risk": "Medium",
            "notes": "Semi-engineered; performance depends heavily on cement-to-sand ratios."
        },
        "h": {
            "description": "Bamboo / Adobe / Mud pile",
            "vulnerability_risk": "High",
            "notes": "Rudimentary non-engineered base structure; highly vulnerable to shaking."
        }
    },
    "roof_type": {
        "n": {
            "description": "Bamboo / Timber / Mud plain roofing",
            "vulnerability_risk": "High",
            "notes": "Heavy, thick traditional roof structure that creates top-heavy inertial forces."
        },
        "q": {
            "description": "Corrugated Galvanized Iron (CGI) sheets",
            "vulnerability_risk": "Low",
            "notes": "Tin sheets; extremely lightweight, reducing the building's center of mass."
        },
        "x": {
            "description": "Reinforced Concrete (RC) slab",
            "vulnerability_risk": "Medium",
            "notes": "Rigid and heavy; structurally safe if anchored to RC columns, dangerous if on brick walls."
        }
    },
    "ground_floor_type": {
        "f": {
            "description": "Mud / Soil floor",
            "vulnerability_risk": "High",
            "notes": "Raw packed dirt or mud; highly typical of non-engineered masonry buildings."
        },
        "v": {
            "description": "Brick / Stone masonry with cement mortar",
            "vulnerability_risk": "Medium",
            "notes": "Intermediate rigid floor structure utilizing standard binding materials."
        },
        "x": {
            "description": "Reinforced Concrete (RC) slab floor",
            "vulnerability_risk": "Low",
            "notes": "Modern, monolithic slab foundation floor providing strong base diaphragm action."
        },
        "m": {
            "description": "Timber / Wood planking",
            "vulnerability_risk": "Medium",
            "notes": "Flexible and lightweight; common in multi-story traditional construction."
        },
        "z": {
            "description": "Other localized / composite sub-materials",
            "vulnerability_risk": "Medium",
            "notes": "Miscellaneous or variable hybrid building floor types."
        }
    }
}

# Quick testing helper to decode values on the fly:
def decode_building_feature(feature_name: str, code: str) -> str:
    """Returns the descriptive string for a given feature code."""
    try:
        return RICHTER_DATASET_MAPPINGS[feature_name][code.lower()]["description"]
    except KeyError:
        return f"Unknown code [{code}] for feature [{feature_name}]"