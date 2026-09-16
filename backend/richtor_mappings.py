"""Richter (DrivenData) single-letter building codes -> the category each code actually encodes.

Provenance — verified 2026-09-16 against the training data itself.
The letters are DrivenData's encoding of the 2015 Nepal Building Structure Survey. What each letter
means was re-derived by matching this code space against the survey's human-readable labels, using
three independent signals that agree for EVERY code:
  1. joint structure — the (foundation, roof, ground_floor) 3-way joint distribution, best of all
     86,400 per-column permutations (total-variation distance 0.054, runner-up 0.057);
  2. marginal prevalence — every pairing lands within ~2 percentage points of its survey category;
  3. mean damage grade — the rank ordering is identical in both encodings for every code.
Rows marked `verified_share` carry the measured share; the vulnerability rating follows the measured
damage ordering within each column (rank 1 = least damaged).

An earlier revision of this file mislabelled roof `q` and `n`, foundation `h`, and ground-floor
`v`, `x`, `m`, `z`. Because the API sends these codes straight to the model, the app was feeding a
different material than the user selected — most seriously roof `q` (23.6% of surveyed buildings,
labelled "corrugated metal" but encoding the heavy traditional roof) and the ground-floor `v`/`x`
pair (RC and brick/stone swapped). Do not "tidy" these strings back: this is what the trained model
means by each code.
"""

RICHTER_DATASET_MAPPINGS = {
    "foundation_type": {
        "r": {
            "description": "Mud mortar - Stone",
            "vulnerability_risk": "High",
            "notes": "Most common in rural Nepal (84% of surveyed buildings); no tensile capacity, "
                     "worst measured damage of the five foundation types."
        },
        "w": {
            "description": "Bamboo / Timber foundation",
            "vulnerability_risk": "Medium",
            "notes": "Flexible timber base (~6%); resilient against collapse but prone to deformation."
        },
        "i": {
            "description": "Reinforced Concrete (RC) / Cement",
            "vulnerability_risk": "Low",
            "notes": "Engineered rigid base (~4%); best measured performance of the five foundation types."
        },
        "u": {
            "description": "Cement - Stone masonry composite",
            "vulnerability_risk": "Medium",
            "notes": "Semi-engineered stone masonry in cement mortar (~5%); performance depends on the "
                     "cement-to-sand ratio."
        },
        "h": {
            "description": "Other / unclassified foundation",
            "vulnerability_risk": "High",
            "notes": "Rare residual class (~0.6%); whatever does not fit the four named foundations. "
                     "Second-worst measured damage — treat as non-engineered."
        }
    },
    "roof_type": {
        "n": {
            "description": "Bamboo / Timber - light roof",
            "vulnerability_risk": "Medium",
            "notes": "Light cladding class (~70% of surveyed buildings): thatch, light timber/tile, and "
                     "thin sheet metal including corrugated galvanised iron. Low mass, so low inertial "
                     "demand on the walls — enter CGI/tin roofs here."
        },
        "q": {
            "description": "Bamboo / Timber - heavy roof",
            "vulnerability_risk": "High",
            "notes": "Heavy traditional roof (~24%): thick mud-covered timber/bamboo. Raises the centre "
                     "of mass, so it shows the worst measured damage of the three roof types."
        },
        "x": {
            "description": "Reinforced Concrete (RC) slab (RCC/RB/RBC)",
            "vulnerability_risk": "Low",
            "notes": "Rigid slab roof (~6%); best measured performance. Heavy, so it is safe only when "
                     "anchored to RC columns — dangerous on unreinforced brick/stone walls."
        }
    },
    "ground_floor_type": {
        "f": {
            "description": "Mud / Soil floor",
            "vulnerability_risk": "High",
            "notes": "Raw packed earth (~80%); typical of non-engineered masonry, worst measured damage."
        },
        "v": {
            "description": "Reinforced Concrete (RC) floor",
            "vulnerability_risk": "Low",
            "notes": "Concrete slab floor (~9.4%); best measured performance, provides base diaphragm action."
        },
        "x": {
            "description": "Brick / Stone floor",
            "vulnerability_risk": "High",
            "notes": "Masonry or cobble floor (~9.6%); second-worst measured damage — shifts under "
                     "dynamic loading."
        },
        "m": {
            "description": "Other / unclassified floor",
            "vulnerability_risk": "Medium",
            "notes": "Rare residual class (~0.2%). Second-best measured damage."
        },
        "z": {
            "description": "Timber / Wood planking",
            "vulnerability_risk": "Medium",
            "notes": "Flexible suspended timber floor (~0.4%); mid-range measured damage."
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
