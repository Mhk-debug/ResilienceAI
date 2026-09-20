# Damage model v3 — API contract

Frozen 2026-09-19. Both the form (frontend) and the pipeline (backend) must match this document.
The old artifact (`backend/models/seismic_resilience_xgb.pkl`, 3-class DrivenData schema) is retired;
the new bundle is an ordinal damage model over Nepal survey grades 1–5.

## Why the request grew

The retired model scored well only when fed 13 of its 43 inputs by constant zeros. The new model is
trained on the columns the survey actually records, so the form must collect them. Nine new fields,
all of them answerable by looking at the building.

## Request — `AssessmentRequest` (frontend → `POST /assessment/process`)

Existing fields (unchanged): `latitude`, `longitude`, `count_floors_pre_eq`, `age`, `area_sq_ft`,
`height_ft`, `foundation_type`, `roof_type`, `ground_floor_type`,
`has_superstructure_mud_mortar_stone`, `has_superstructure_rc_engineered`,
`has_superstructure_cement_mortar_brick`, `has_superstructure_rc_non_engineered`,
`has_superstructure_adobe_mud`, `has_superstructure_timber`.

New fields — values must be these exact strings:

| Field | Allowed values | User-facing question |
|---|---|---|
| `land_surface_condition` | `Flat` · `Moderate slope` · `Steep slope` | What does the ground under the building look like? |
| `position` | `Not attached` · `Attached-1 side` · `Attached-2 side` · `Attached-3 side` | How many sides of the building are attached to neighbouring buildings? |
| `plan_configuration` | `Rectangular` · `Square` · `L-shape` · `T-shape` · `U-shape` · `E-shape` · `H-shape` · `Multi-projected` · `Building with Central Courtyard` · `Others` | Footprint shape in plan |
| `other_floor_type` | `Timber-Planck` · `TImber/Bamboo-Mud` (spelling is the survey's) · `RCC/RB/RBC` · `Not applicable` | Floor construction above the ground floor (`Not applicable` for single-storey) |
| `has_superstructure_stone_flag` | 0 · 1 | Stone flag / dressed stone in the structure |
| `has_superstructure_cement_mortar_stone` | 0 · 1 | Stone laid in cement mortar |
| `has_superstructure_mud_mortar_brick` | 0 · 1 | Brick laid in mud mortar |
| `has_superstructure_bamboo` | 0 · 1 | Bamboo structural elements |
| `has_superstructure_other` | 0 · 1 | Any other structural material |

Server-side only (the frontend never sends these): `epi_distance_km` and the site shaking terms,
which the hazard engine computes for the assessment's coordinates.

## Response — `building` object inside `AssessmentIDResponse`

```json
{
  "status": "success",
  "model_version": "damage-v3-ordinal",
  "resilience_score": 41.7,
  "expected_grade": 3.33,
  "grade_class": 3,
  "probabilities": { "grade1": 0.09, "grade2": 0.23, "grade3": 0.34, "grade4": 0.22, "grade5": 0.12 },
  "p_severe_grade45": 0.34,
  "used_fallback_model": false,
  "flags": ["..."],
  "building_llm_context": { "structural": {}, "material": {}, "substructure": {} }
}
```

* `resilience_score = 100 × (5 − E[grade]) / 4`, clipped to 0–100 (unchanged scale and direction).
* `probabilities` now has five entries (was a single number). The dashboard shows them as a stacked
  distribution — that is the model's real output and its honest uncertainty.
* `flags` carries model caveats (out-of-range intensity, fallback used, non-monotone correction).
  Surface them in the UI rather than hiding them.

## Composite risk score

The ML score is now a damage estimate, so the old `hazard·0.6 + (100 − resilience)·0.4` counted
shaking twice. Replacement:

```
vulnerability = (expected_grade − 1) / 4          # 0 = no damage expected, 1 = destruction
risk_score    = (hazard_score / 100) × vulnerability × 100
```

Interpretation to use everywhere (UI copy, docs, pitch): **hazard** is how violent the shaking at
this site can be, **vulnerability** is how much damage this building takes when it is shaken,
**risk** is the expected damage. `frontend/utils/risk.ts` owns the formula and the bands.
