# Model card — ResilienceAI seismic damage model (v3m, monotone)

**Version:** `damage-v3m-monotone` · trained 19 Sep 2026 · **Type:** ordinal cumulative-link
decomposition (4 × binary `XGBClassifier` on `P(damage_grade > k)`, k = 1…4) · **Target:**
`damage_grade` ∈ {1,2,3,4,5} (1 = no damage, 5 = destruction) · **Inputs:** 54 features.

## Why this model exists

It replaces a 3-class classifier trained on the DrivenData "Richter's Predictor" table. That artifact
was fed **13 of its 43 inputs as constant zeros** by this API (the form never collected them) and
measured **19.3 % accuracy on the served path against a 56.9 % majority-class baseline**. This model
is trained on the team's real data, on a target that is ordered, using only inputs the form can supply.

## Measured performance

### Same-district (152,419 held-out buildings, 80/10/10 stratified, seed 42)

| Metric | Value |
|---|---|
| Accuracy | **45.79 %** |
| Macro-F1 | 0.4295 |
| MAE (grades) | **0.712** |
| Adjacent accuracy (±1) | **86.54 %** |
| Quadratic weighted kappa | 0.6500 |
| AUC (grade ≥ 4) | 0.8094 |
| Majority-class baseline (always Grade 5) | 36.1 % |

### Cross-district — the honest number for a country the model has never seen

3 folds, 0 % of test rows in a district the model trained on, 40,000-row stratified subsample:

| Variant | Accuracy | MAE | QWK | ±1 |
|---|---:|---:|---:|---:|
| **this model** (monotone in distance) | **33.44 %** | **0.933** | **0.482** | **79.4 %** |
| same features, unconstrained | 29.53 % | 1.017 | 0.399 | 76.2 % |
| the same comparison at 120,000 rows | see `results_grouped_v3.json` in the research workspace |

The unconstrained variant scores **8.2 points higher on a random split (53.99 %)** and lower here on
every metric. That gap is the measured size of the geography it memorises through the distance
feature, and it is why the constrained model is the one deployed. Quote the grouped figure for
Myanmar claims; the random-split figure is optimistic by roughly 12 points.

### What "MAE 0.712" means

The average prediction is about seven tenths of a damage grade away from the truth, and 86.5 % of
predictions land within ±1 grade. Use this as a **screening ranker** — it ranks buildings and
sites sensibly (see below) — not as an absolute grade oracle.

## Distance response (measured, one building held fixed)

From the monotonicity audit in `train_v3_monotone.py` — the sweep that asserts the constraint:

| Building | Distance | E[grade] | Resilience score (derived) |
|---|---:|---:|---:|
| Mud-mortar stone, 3 storey, 40 y | 10 km | 4.895 | 2.6 |
| Mud-mortar stone, 3 storey, 40 y | 30 km | 4.079 | 23.0 |
| Mud-mortar stone, 3 storey, 40 y | 150 km | 3.889 | 27.8 |
| Engineered RC, 4 storey, 5 y | 10 km | 3.545 | 36.4 |
| Engineered RC, 4 storey, 5 y | 50 km | 1.948 | 76.3 |
| Engineered RC, 4 storey, 5 y | 75 km | 1.712 | 82.2 |

Two properties to check when the artifact changes: engineered RC must score above mud-mortar stone at
any fixed site, and every profile must degrade monotonically as it approaches the event. The complete
sweep (2–200 km, ten points per profile) is in `model_metadata.json["metrics"]["monotonicity_audit"]`.

## The site term (read before deploying)

* The only site-specific input is `epi_distance_km`: the great-circle distance to the **governing
  event** — the event the hazard engine used for `estimated_mmi` / `estimated_pga_g`, exposed as
  `environmental_context.ground_motion.governing_event`. Supply it from there, not from a different
  magnitude/distance source.
* Training range: **2.4–215.5 km**. Outside it the loader adds an extrapolation caveat to the response
  `flags` rather than silently extrapolating.
* `P(grade > k)` is constrained **non-increasing in distance** (`monotone_constraints` in
  `model_metadata.json`). `train_v3_monotone.py` asserts this by sweeping a distance grid with one
  building held fixed; both archetypes pass.
* An absolute shaking term in MMI was **rejected on measurement**: the app's own attenuation relation
  is a perfect monotone function of distance (Spearman −1.000 with distance, +0.146 with damage grade,
  against +0.502 for the ward-level field the research used), so feeding it would add a pretence of
  information, not information.

## Input vocabulary — verified

The form supplies the survey's own strings for `land_surface_condition`, `other_floor_type`,
`position`, `plan_configuration` (note the survey's own spellings `TImber/Bamboo-Mud` and
`Timber-Planck` — do not "fix" them) and single-letter codes for the three legacy material fields.
The code → survey mapping in `services/damage_model.py::APP_CODE_TO_SURVEY` was verified against the
training data by three independent signals (the 3-way joint distribution over 86,400 permutations,
marginal prevalence, and measured damage ordering):

| Field | Codes |
|---|---|
| `foundation_type` | `r` mud mortar–stone/brick · `w` bamboo/timber · `i` RC · `u` cement–stone/brick · `h` other |
| `roof_type` | `n` light roof (thatch, light tile, CGI/tin) · `q` heavy traditional (thick mud-covered) · `x` RCC/RB/RBC |
| `ground_floor_type` | `f` mud · **`v` RC** · **`x` brick/stone** · `m` other · `z` timber |

The `v`/`x` pair has been swapped in this project before, in both directions. It is now pinned by
`backend/scripts/verify_code_mappings.py`, which re-derives the mapping from the data and exits
non-zero on disagreement. Run it after touching any option label or decode string.

## Coupling to the form

Every one of the 54 inputs is collectable in the UI. Nine fields were added for this model (terrain
slope, attached sides, plan shape, floor-above-ground, and five material flags); if a user skips the
new sections the request still validates and scores, falling back to the training population's modal
category for each uncollected field. That fallback cost **3.8 accuracy points** measured on the
unconstrained variant (50.19 % vs 53.99 %); the same measurement has not been repeated on the
monotone variant, so treat 3.8 points as the order of magnitude rather than an exact figure for this
artifact. The retired model's 20-point gap was a different failure — inputs the API could never
supply at all, not user-skippable sections.

## Domain limits

* **One event, one country.** Nepal 2015 Gorkha, 11 districts. Mid-rise engineered RC frames — the
  common Yangon/Mandalay typology — are barely represented (4.2 % RC foundations, 44,584 RCC roofs
  out of 762,094).
* **Never train on** `count_floors_post_eq`, `height_ft_post_eq`, `condition_post_eq` or
  `technical_solution_proposed`: they are post-earthquake recordings that determine the label
  (`height_ft_post_eq == 0` ⇒ 100 % Grade 5). Public notebooks reporting ~89 % on this file are
  reading the answer sheet.
* **Weakly shaken sites are out of distribution** (all training buildings are MMI 6.24–8.0). Gate
  low-hazard sites instead of trusting the raw prediction there.
* Not a design tool. Screening plus hazard-engine context only.

## Files

| File | Purpose |
|---|---|
| `ordinal_grade_gt1..4.pkl` | the four boosters, in grade order |
| `model_metadata.json` | ordered feature list, thresholds, best iterations, monotone constraints, metrics, grouped-CV summary, data hashes, site contract |
| `MODEL_CARD.md` | this document |

## Deployment notes

1. Build features **in exactly `model_metadata.json["features"]` order**, reindexing with
   `fill_value=0`; never re-sort.
2. Apply the cumulative monotonicity guard (`P(grade>k) ≤ P(grade>k−1)`) — the loader does, and flags
   when it fires.
3. Score: `resilience = 100 · (5 − E[grade]) / 4`, clipped to 0–100, where `E[grade] = 1 + Σ_k P(grade>k)`.
   Report `P(grade ≥ 4)` beside it.
4. Retrain with `train_v3_monotone.py` (this model) or `train_v3.py` (unconstrained); splits are
   seeded and `model_metadata.json` records the data hashes.
5. The composite risk score consumes `E[grade]`, not the raw probability — see
   `backend/docs/resilience_scoring.md`.
