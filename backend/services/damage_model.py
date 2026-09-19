"""
services/damage_model.py

The building damage model: an ordinal cumulative-link decomposition over damage grades 1-5
(four binary XGBoost boosters, P(grade > k)), trained on the 762,094 labelled buildings of the
2015 Nepal Building Structure Survey. It replaces the retired 3-class DrivenData artifact, which
was fed 13 of its 43 inputs as constant zeros by this API and measured at 19.3 % accuracy on the
served path against a 56.9 % majority-class baseline.

Contract and measured performance: `backend/docs/model_v3_contract.md`, `models/seismic_damage_v3/MODEL_CARD.md`.

The only site-specific input is the epicentral distance to the governing event (see the model card
for why an absolute intensity term is deliberately not used); every other field comes from the form.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BUNDLE_DIR = os.path.join(_BASE_DIR, "models", "seismic_damage_v3")

# ---------------------------------------------------------------------------------------------
# Vocabulary. The survey's own category strings are the model's training vocabulary: never
# "tidy" them (note the survey's spellings `TImber/Bamboo-Mud` and `Timber-Planck`).
# ---------------------------------------------------------------------------------------------

SURVEY_CATEGORIES: Dict[str, list] = {
    "land_surface_condition": ["Flat", "Moderate slope", "Steep slope"],
    "foundation_type": ["Mud mortar-Stone/Brick", "Bamboo/Timber", "Cement-Stone/Brick", "RC", "Other"],
    "roof_type": ["Bamboo/Timber-Light roof", "Bamboo/Timber-Heavy roof", "RCC/RB/RBC"],
    "ground_floor_type": ["Mud", "RC", "Brick/Stone", "Timber", "Other"],
    "other_floor_type": ["TImber/Bamboo-Mud", "Timber-Planck", "Not applicable", "RCC/RB/RBC"],
    "position": ["Not attached", "Attached-1 side", "Attached-2 side", "Attached-3 side"],
    "plan_configuration": ["Rectangular", "Square", "L-shape", "T-shape", "Multi-projected",
                           "Others", "U-shape", "E-shape", "Building with Central Courtyard", "H-shape"],
}

# The three fields the form has always sent as single-letter codes. Verified against the training
# data by joint distribution (86,400 permutations), marginal prevalence and the measured damage
# ordering; see `backend/richtor_mappings.py` and `backend/scripts/verify_code_mappings.py`.
# Ground floor `v` is RC and `x` is brick/stone — the pair was once swapped in both directions.
APP_CODE_TO_SURVEY: Dict[str, Dict[str, str]] = {
    "foundation_type": {"r": "Mud mortar-Stone/Brick", "w": "Bamboo/Timber",
                        "i": "RC", "u": "Cement-Stone/Brick", "h": "Other"},
    "roof_type": {"n": "Bamboo/Timber-Light roof", "q": "Bamboo/Timber-Heavy roof",
                  "x": "RCC/RB/RBC"},
    "ground_floor_type": {"f": "Mud", "v": "RC", "x": "Brick/Stone", "m": "Other", "z": "Timber"},
}

# Population modes of the training data, used only when a field is missing from the payload.
SURVEY_MODES = {"land_surface_condition": "Flat", "other_floor_type": "TImber/Bamboo-Mud",
                "position": "Not attached", "plan_configuration": "Rectangular"}

SUPERSTRUCTURE_FLAGS = [
    "has_superstructure_adobe_mud", "has_superstructure_mud_mortar_stone",
    "has_superstructure_stone_flag", "has_superstructure_cement_mortar_stone",
    "has_superstructure_mud_mortar_brick", "has_superstructure_cement_mortar_brick",
    "has_superstructure_timber", "has_superstructure_bamboo",
    "has_superstructure_rc_non_engineered", "has_superstructure_rc_engineered",
    "has_superstructure_other",
]

NUMERIC_FIELDS = ["count_floors_pre_eq", "age_building", "plinth_area_sq_ft", "height_ft_pre_eq"]

TRAINING_DISTANCE_RANGE_KM = (2.4, 215.5)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        out = float(value)
        return out if np.isfinite(out) else default
    except (TypeError, ValueError):
        return default


class DamageModel:
    """Ordinal damage model over grades 1-5 with a cumulative monotonicity guard."""

    def __init__(self, bundle_dir: str = DEFAULT_BUNDLE_DIR):
        self.bundle_dir = bundle_dir
        with open(os.path.join(bundle_dir, "model_metadata.json"), encoding="utf-8") as fh:
            self.metadata: Dict[str, Any] = json.load(fh)
        self.features: list = list(self.metadata["features"])
        self.thresholds = self.metadata.get("thresholds", {}).get("default", [0.5] * 4)
        self.model_version = self.metadata.get("model_version", "damage-v3-ordinal")
        import joblib
        self.boosters = [
            joblib.load(os.path.join(bundle_dir, f"ordinal_grade_gt{k}.pkl")) for k in range(1, 5)
        ]

    # ------------------------------------------------------------------ feature construction
    def _survey_value(self, field: str, raw: Any, warnings: list) -> Optional[str]:
        """Resolve a categorical field to the survey vocabulary, mapping app codes when needed."""
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return SURVEY_MODES.get(field)
        value = str(raw).strip()
        if field in APP_CODE_TO_SURVEY:
            code = value.lower()
            mapped = APP_CODE_TO_SURVEY[field].get(code)
            if mapped is None:
                warnings.append(f"{field}='{value}' is not a known code; ignored")
                return None
            return mapped
        allowed = SURVEY_CATEGORIES[field]
        if value not in allowed:
            # tolerate case/spacing drift from the form without inventing a category
            for candidate in allowed:
                if candidate.lower() == value.lower():
                    return candidate
            warnings.append(f"{field}='{value}' is not in the training vocabulary; ignored")
            return None
        return value

    def build_features(self, payload: Dict[str, Any],
                       epi_distance_km: Optional[float]) -> Tuple[pd.DataFrame, list]:
        warnings: list = []
        row: Dict[str, float] = {
            "count_floors_pre_eq": _as_float(payload.get("count_floors_pre_eq"), 1.0),
            "age_building": _as_float(payload.get("age"), 0.0),
            "plinth_area_sq_ft": _as_float(payload.get("area_sq_ft"), 1.0),
            "height_ft_pre_eq": _as_float(payload.get("height_ft"), 1.0),
        }
        floors = max(row["count_floors_pre_eq"], 1.0)
        row["storey_height_ft"] = row["height_ft_pre_eq"] / floors
        row["slenderness"] = row["height_ft_pre_eq"] / np.sqrt(max(row["plinth_area_sq_ft"], 1.0))
        row["age_floors"] = row["age_building"] * row["count_floors_pre_eq"]

        for flag in SUPERSTRUCTURE_FLAGS:
            row[flag] = 1.0 if _as_float(payload.get(flag)) >= 0.5 else 0.0

        for field in SURVEY_CATEGORIES:
            value = self._survey_value(field, payload.get(field), warnings)
            if value is None:
                value = SURVEY_MODES.get(field)
            row[f"{field}_{value}"] = 1.0

        if epi_distance_km is None:
            distances_seen = [d for d in (payload.get("epi_distance_km"),) if d is not None]
            epi_distance_km = _as_float(distances_seen[0]) if distances_seen else None
        if epi_distance_km is None:
            # No site term available: the model still runs, but the site dimension is neutralised
            # at the training mean so the prediction degrades to the structural-only behaviour.
            warnings.append("no site distance available — the model ran without its site term")
            row["epi_distance_km"] = float(np.mean(TRAINING_DISTANCE_RANGE_KM))
            row["has_distance"] = 0.0
        else:
            distance = float(epi_distance_km)
            if not (TRAINING_DISTANCE_RANGE_KM[0] <= distance <= TRAINING_DISTANCE_RANGE_KM[1]):
                warnings.append(
                    f"epicentral distance {distance:.1f} km is outside the training range "
                    f"{TRAINING_DISTANCE_RANGE_KM} — the site term is an extrapolation")
            row["epi_distance_km"] = distance
            row["has_distance"] = 1.0

        frame = pd.DataFrame([row]).reindex(columns=self.features, fill_value=0).astype(np.float32)
        # A categorical contributes exactly one hot column; every other category of that field is a
        # legitimate zero, so it must not be reported as an absent input.
        categorical_prefixes = tuple(f"{field}_" for field in SURVEY_CATEGORIES)
        missing = [c for c in self.features
                   if c not in row and not c.startswith(categorical_prefixes)]
        if missing:
            warnings.append(f"{len(missing)} model inputs were not provided and were zero-filled")
        return frame, warnings

    # ------------------------------------------------------------------ inference
    def predict(self, payload: Dict[str, Any], epi_distance_km: Optional[float] = None) -> Dict[str, Any]:
        frame, warnings = self.build_features(payload, epi_distance_km)
        P = np.vstack([m.predict_proba(frame)[:, 1] for m in self.boosters]).T
        P_mono = np.minimum.accumulate(P, axis=1)
        if not np.allclose(P_mono, P):
            warnings.append("cumulative probabilities were non-monotone and have been corrected")

        probabilities = np.zeros(5)
        previous = 1.0
        for k in range(1, 6):
            if k <= 4:
                probabilities[k - 1] = previous - P_mono[0, k - 1]
                previous = P_mono[0, k - 1]
            else:
                probabilities[k - 1] = previous
        probabilities = np.clip(probabilities, 0, None)
        probabilities = probabilities / probabilities.sum()

        expected_grade = float(1.0 + P_mono[0].sum())
        grade_class = int(1 + int((P_mono[0] > np.asarray(self.thresholds)).sum()))
        resilience_score = float(np.clip(100.0 * (5.0 - expected_grade) / 4.0, 0.0, 100.0))

        return {
            "model_version": self.model_version,
            "resilience_score": round(resilience_score, 2),
            "expected_grade": round(expected_grade, 3),
            "grade_class": grade_class,
            "probabilities": {f"grade{i + 1}": round(float(probabilities[i]), 4) for i in range(5)},
            "p_severe_grade45": round(float(probabilities[3] + probabilities[4]), 4),
            "flags": warnings,
        }


_MODEL: Optional[DamageModel] = None


def load_damage_model(bundle_dir: str = DEFAULT_BUNDLE_DIR) -> Optional[DamageModel]:
    """Load (once) and return the damage model, or None when the bundle is absent/corrupt."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        _MODEL = DamageModel(bundle_dir)
        logger.info("Damage model loaded: %s (%d features, %d boosters)",
                    _MODEL.model_version, len(_MODEL.features), len(_MODEL.boosters))
        return _MODEL
    except Exception as exc:  # pragma: no cover - surfaced at boot as a missing model
        logger.error("Damage model failed to load from %s: %s", bundle_dir, exc, exc_info=True)
        return None
