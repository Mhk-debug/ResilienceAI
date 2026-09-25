#!/usr/bin/env python3
"""Generate the landing page's shake-lab data from the SHIPPED model. Nothing here is hand-typed.

Two tables, because the page's two controls drive two genuinely different computations:

  hazard_by_magnitude_distance   the hazard engine's own attenuation (estimate_pga_g -> pga_to_mmi).
                                 Magnitude matters here.
  damage_by_archetype_distance   the damage model. It conditions on DISTANCE to the governing
                                 event only — magnitude does not enter it (see machine_learning.md
                                 §3: an absolute shaking term was rejected because the project's
                                 GMPE is a perfect monotone function of distance). So the damage
                                 table has no magnitude axis, and the landing must not imply one.

Emitting a 144-cell magnitude x distance x archetype grid would have meant three identical damage
rows per (archetype, distance) — a slider that moves and changes nothing. Two honest tables instead.

Run:  cd frontend && python3 scripts/generate_shake_lab.py
Writes: frontend/lib/landing/shake-lab.json
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.dirname(HERE)
REPO = os.path.dirname(FRONTEND)
BACKEND = os.path.join(REPO, "backend")
sys.path.insert(0, BACKEND)

from services.damage_model import DamageModel                     # noqa: E402
from services.hazard_engine.shakemap import estimate_pga_g, pga_to_mmi  # noqa: E402

BUNDLE = os.path.join(BACKEND, "models", "seismic_damage_v3")
OUT = os.path.join(FRONTEND, "lib", "landing", "shake-lab.json")

MAGNITUDES = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]
DISTANCES_KM = [5, 10, 25, 50, 100, 150]
EVENT_DEPTH_KM = 10.0   # fixed hypocentral depth for the attenuation panel; stated in the payload

# Four archetypes, each an honest, self-consistent building profile. Values are the survey's own
# vocabularies and the app's verified single-letter codes.
ARCHETYPES = {
    "mud_stone": {
        "label": "Mud-mortar stone masonry",
        "blurb": "Rural load-bearing stone in mud mortar. The most common building in the 2015 Nepal "
                 "survey and the worst performer in it.",
        "icon": "stone",
        "profile": {
            "count_floors_pre_eq": 3, "age": 40, "area_sq_ft": 700, "height_ft": 28,
            "foundation_type": "r", "roof_type": "q", "ground_floor_type": "f",
            "land_surface_condition": "Flat", "position": "Not attached",
            "plan_configuration": "Rectangular", "other_floor_type": "TImber/Bamboo-Mud",
            "has_superstructure_mud_mortar_stone": 1,
        },
    },
    "brick_cement": {
        "label": "Cement-mortar brick, attached",
        "blurb": "Brick in cement mortar, attached on two sides — a typical urban row building with "
                 "pounding risk against its neighbours.",
        "icon": "brick",
        "profile": {
            "count_floors_pre_eq": 2, "age": 20, "area_sq_ft": 900, "height_ft": 22,
            "foundation_type": "u", "roof_type": "n", "ground_floor_type": "x",
            "land_surface_condition": "Flat", "position": "Attached-2 side",
            "plan_configuration": "Rectangular", "other_floor_type": "RCC/RB/RBC",
            "has_superstructure_cement_mortar_brick": 1,
        },
    },
    "timber_bamboo": {
        "label": "Timber / bamboo on a slope",
        "blurb": "Light single-storey timber with bamboo, on sloping ground. Flexible, but the site "
                 "itself is working against it.",
        "icon": "timber",
        "profile": {
            "count_floors_pre_eq": 1, "age": 10, "area_sq_ft": 400, "height_ft": 12,
            "foundation_type": "w", "roof_type": "n", "ground_floor_type": "z",
            "land_surface_condition": "Moderate slope", "position": "Not attached",
            "plan_configuration": "L-shape", "other_floor_type": "Not applicable",
            "has_superstructure_timber": 1, "has_superstructure_bamboo": 1,
        },
    },
    "engineered_rc": {
        "label": "Engineered reinforced concrete",
        "blurb": "A modern RC frame with an engineered design — the reference case for what a "
                 "resilient building looks like in this model.",
        "icon": "rc",
        "profile": {
            "count_floors_pre_eq": 4, "age": 5, "area_sq_ft": 1600, "height_ft": 44,
            "foundation_type": "i", "roof_type": "x", "ground_floor_type": "v",
            "land_surface_condition": "Flat", "position": "Not attached",
            "plan_configuration": "Rectangular", "other_floor_type": "RCC/RB/RBC",
            "has_superstructure_rc_engineered": 1,
        },
    },
}


def main() -> int:
    model = DamageModel(BUNDLE)

    hazard = []
    for m in MAGNITUDES:
        for d in DISTANCES_KM:
            pga = estimate_pga_g(m, float(d), EVENT_DEPTH_KM)
            hazard.append({
                "magnitude": m,
                "distance_km": d,
                "pga_g": round(float(pga), 4),
                "mmi": round(float(pga_to_mmi(pga)), 2),
            })

    damage = []
    for key, spec in ARCHETYPES.items():
        for d in DISTANCES_KM:
            out = model.predict(spec["profile"], epi_distance_km=float(d))
            damage.append({
                "archetype": key,
                "distance_km": d,
                "expected_grade": out["expected_grade"],
                "grade_class": out["grade_class"],
                "resilience_score": out["resilience_score"],
                "p_severe_grade45": out["p_severe_grade45"],
                "probabilities": out["probabilities"],
                "flags": out["flags"],
            })

    meta = model.metadata
    same = meta["metrics"].get("E1m_monotone__full", {})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generator": "frontend/scripts/generate_shake_lab.py",
        "model_version": model.model_version,
        "bundle": "backend/models/seismic_damage_v3",
        "provenance": {
            "damage": "ordinal cumulative-link model (4 x binary XGBoost) over damage grades 1-5, "
                      "trained on the 2015 Nepal Building Structure Survey; site term = epicentral "
                      "distance to the governing event",
            "hazard": "the app's own attenuation relation (estimate_pga_g) plus the piecewise PGA->MMI "
                      "conversion, at a fixed hypocentral depth",
            "event_depth_km": EVENT_DEPTH_KM,
            "note": "These are model outputs for fixed archetypes, so the page can show the real "
                    "model without a live request. The live app scores real buildings.",
            "archetype_order": "engineered_rc > brick_cement > timber_bamboo > mud_stone, asserted "
                               "at every distance by the generator against measured mean damage "
                               "grades in the training survey (1.443 / 1.954 / 3.390 / 3.966)",
        },
        "magnitudes": MAGNITUDES,
        "distances_km": DISTANCES_KM,
        "archetypes": {k: {"label": v["label"], "blurb": v["blurb"], "icon": v["icon"]}
                       for k, v in ARCHETYPES.items()},
        "hazard_by_magnitude_distance": hazard,
        "damage_by_archetype_distance": damage,
        # Numbers the page is allowed to quote, taken from the artifact rather than from prose.
        "model_facts": {
            "model_version": model.model_version,
            "features": meta.get("n_features"),
            # The train split the model actually learned from...
            "trained_on_rows": meta.get("trained_on_rows"),
            # ...and the size of the labelled survey it was drawn from. Both are published because
            # quoting the second while the model saw only the first would mislead.
            "survey_rows": sum(meta.get("split") or [meta.get("trained_on_rows") or 0]),
            "split": meta.get("split"),
            "same_district": {
                "accuracy": same.get("accuracy"),
                "mae": same.get("mae"),
                "adjacent_accuracy": same.get("adjacent_accuracy"),
                "qwk": same.get("qwk"),
            },
            "grouped_cv": meta.get("grouped_cv", {}).get("n_rows_120k_3folds", {}),
            "dataset": "Nepal 2015 Building Structure Survey, 11 districts",
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")

    size_kb = os.path.getsize(OUT) / 1024
    print(f"wrote {OUT} ({size_kb:.1f} KB)")
    print(f"  hazard rows : {len(hazard)}  ({len(MAGNITUDES)} magnitudes x {len(DISTANCES_KM)} distances)")
    print(f"  damage rows : {len(damage)}  ({len(ARCHETYPES)} archetypes x {len(DISTANCES_KM)} distances)")
    print(f"  model       : {payload['model_version']} | grouped acc "
          f"{payload['model_facts']['grouped_cv'].get('monotone', {}).get('accuracy')}")

    # Sanity: the model must rank archetypes the way the TRAINING DATA does, at every distance.
    # The expected order is measured, not assumed — mean damage grade by material flag in
    # training/csv_building_structure.csv (n = 762,094):
    #   rc_engineered 1.443 · cement_mortar_brick 1.954 · timber 3.390 · mud_mortar_stone 3.966
    # (combined profiles agree: cement-brick flag + brick/stone floor 1.983 vs timber flag +
    # timber floor 2.752). So "timber/bamboo is safer than masonry" is a plausible-sounding
    # assumption this dataset does not support — do not "fix" the order without re-measuring.
    ORDER = ["engineered_rc", "brick_cement", "timber_bamboo", "mud_stone"]
    ranks_ok = True
    for d in DISTANCES_KM:
        rows = {r["archetype"]: r["resilience_score"] for r in damage if r["distance_km"] == d}
        if [k for k in ORDER if k in rows] != sorted(rows, key=lambda k: -rows[k]):
            ranks_ok = False
            print(f"  RANK WARNING at {d} km: {rows}")
    monotone_ok = all(
        all(
            [r for r in damage if r["archetype"] == a and r["distance_km"] == d][0]["expected_grade"]
            >= [r for r in damage if r["archetype"] == a and r["distance_km"] == d2][0]["expected_grade"]
            for i, d in enumerate(DISTANCES_KM[:-1])
            for d2 in [DISTANCES_KM[i + 1]]
        )
        for a in ARCHETYPES
    )
    print(f"  archetype ranking by resilience: {'OK' if ranks_ok else 'FAILED'}")
    print(f"  expected grade non-increasing with distance: {'OK' if monotone_ok else 'FAILED'}")
    return 0 if (ranks_ok and monotone_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
