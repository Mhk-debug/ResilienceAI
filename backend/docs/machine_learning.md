# Machine Learning Documentation

> **Ordinal building-damage model (damage grades 1–5) for seismic resilience screening.**
>
> This documents the model deployed in September 2026. It replaced a 3-class classifier that the API
> could only feed 13 of 43 inputs to; that artifact measured 19.3 % accuracy on the served path
> against a 56.9 % majority-class baseline. The retired files live in `backend/models/retired/` for
> reference and are not loaded by the application.

---

## 1. What the model is

| | |
|---|---|
| Type | Ordinal cumulative-link decomposition: four binary XGBoost boosters estimating `P(grade > k)`, k = 1…4 |
| Target | `damage_grade` ∈ {1, 2, 3, 4, 5} (1 = no damage, 5 = destruction) |
| Inputs | 54 features after one-hot encoding (see §3) |
| Artifacts | `backend/models/seismic_damage_v3/` — `ordinal_grade_gt1..4.pkl` + `model_metadata.json` + `MODEL_CARD.md` |
| `model_version` | `damage-v3m-monotone` |
| Loader | `backend/services/damage_model.py` (`DamageModel`, `load_damage_model`) |
| Called from | `services/resilience_service.py::predict_resilience` ← `routes/resilience.py` ← `routes/assessment.py` |

Output per building: the full five-grade probability distribution, `E[grade]`, the most likely grade,
`P(grade ≥ 4)`, a 0–100 resilience score, and a list of caveats. See `resilience_scoring.md` for how
those are derived and combined with the hazard score.

### Why ordinal, not flat multiclass

Damage grades are ordered: predicting Grade 1 as Grade 5 is a worse error than predicting Grade 1 as
Grade 2. A flat softmax treats all misclassifications alike. The cumulative-link decomposition gives
the model ordered decision boundaries and, on this data, produced better MAE and QWK than the flat
softmax for the price of ~1 point of accuracy. The measured comparison is in the research notes
(`~/HermesWork/resilienceai-ml-research/`), summarised in §5.

---

## 2. Training data

| | |
|---|---|
| Source | Nepal 2015 Building Structure Survey (Gorkha earthquake), 11 most-affected districts |
| Rows | 762,094 labelled buildings (`training/csv_building_structure.csv`, stored via git-LFS) |
| Label distribution | Grade 1 10.34 % · Grade 2 11.45 % · Grade 3 17.90 % · Grade 4 24.12 % · Grade 5 36.18 % |
| Majority-class baseline | 36.1 % (always predicting Grade 5) |
| Split | 533,465 train / 76,210 validation / 152,419 test, stratified, seed 42 |

**The target is not the DrivenData competition label.** Two datasets circulate with this project's
name: the DrivenData "Richter's Predictor" table (260,601 rows, 3 damage classes, anonymised
geography) and the survey file above (762,094 rows, 5 grades, named districts). The retired artifact
spoke the DrivenData schema; this model speaks the survey schema.

**Never train on these four columns.** `count_floors_post_eq`, `height_ft_post_eq`,
`condition_post_eq` and `technical_solution_proposed` were recorded *after* the earthquake and
determine the label: `height_ft_post_eq == 0` covers 261,353 rows (34.29 %) and **100 % of them are
Grade 5**; `condition_post_eq = "Damaged-Rubble…"` has mean grade exactly 5.00; "Not damaged" exactly
1.00. A model trained on "everything except `damage_grade`" is reading the surveyor's post-event
assessment off the form and scores ~89 % — that figure appears in public notebooks and is leakage.
The form collects pre-earthquake fields only, which is why honest accuracy sits in the 40–56 % range.

---

## 3. Input features (54, all supplyable by the form)

| Group | Count | Source in the request |
|---|---|---|
| Numeric | 4 | `count_floors_pre_eq`, `age`, `area_sq_ft`, `height_ft` |
| Derived | 3 | `storey_height_ft`, `slenderness`, `age_floors` (computed in the loader) |
| Material flags | 11 | the eleven `has_superstructure_*` booleans |
| Categorical one-hots | 35 | `land_surface_condition` (3), `foundation_type` (5), `roof_type` (3), `ground_floor_type` (5), `other_floor_type` (4), `position` (4), `plan_configuration` (10) |
| Site term | 2 | `epi_distance_km`, `has_distance` |

Two properties of this list matter as much as its contents:

1. **Every input is collected by the form.** The retired model was fed 13 of its 43 inputs as
   constant zeros, which is what destroyed its accuracy. Feature order comes from
   `model_metadata.json["features"]`; the loader reindexes to that order with `fill_value=0` and never
   re-sorts.
2. **Categorical values are the survey's own vocabulary** (`Mud mortar-Stone/Brick`,
   `Bamboo/Timber-Light roof`, and the survey's own spellings `TImber/Bamboo-Mud` and
   `Timber-Planck`). The three legacy fields still arrive as single-letter codes and are mapped in
   `services/damage_model.py::APP_CODE_TO_SURVEY`; that table was verified against the training data by
   joint distribution (86,400 permutations), marginal prevalence and measured damage ordering. Ground
   floor `v` is RC and `x` is brick/stone — the pair is easy to swap and `scripts/verify_code_mappings.py`
   exists to stop it regressing.

### The site term, and why it is distance rather than intensity

The model conditions on one site-specific input: the epicentral distance to the **governing event** the
hazard engine identified (the largest-magnitude event within the search radius that drives
`estimated_mmi` / `estimated_pga_g`). The hazard report exposes that event as
`environmental_context.ground_motion.governing_event`, and `routes/assessment.py` passes its
`distance_km` to the model. The pipeline therefore runs **hazard → building → LLM**, not in parallel.

An absolute intensity term (MMI) was the first choice and was rejected on measurement: the app's own
attenuation relation, `services/hazard_engine/shakemap.py::estimate_pga_g`, is a *perfect monotone
function of epicentral distance* (Spearman −1.000 against distance, +0.146 against damage grade),
whereas the ward-level intensity field the research used correlates +0.502 with grade. Feeding the
app's MMI therefore reproduces only the distance signal while pretending to add information. Two further
defects found in the same check were fixed regardless:

* `integrate_shakemap_data` overwrote the GMPE-consistent MMI with `event.max_mmi × ratio`, collapsing
  it towards 1.0 for any distant event. A Gorkha ward with scenario MMI 8.00 reported **MMI 1.0
  alongside PGA 0.125 g** (which implies ≈ MMI 5.5). The site MMI is now `pga_to_mmi(est_pga)`, with
  the event's own peak MMI used only as an upper bound.
* The governing event was not reported at all, so nothing downstream could condition on it.

### Monotonicity, and why the deployed model is constrained

Damage must not increase with distance from the fault. The unconstrained model is **not** monotone,
because distance is confounded with district construction practice in the training data: holding a
mud-mortar stone, 3-storey, 40-year building fixed, it scores 22.4 at 60 km but 16.8 at 150 km.

| Variant | Constraint | Same-district accuracy | Same-district MAE | Grouped accuracy | Grouped MAE |
|---|---|---:|---:|---:|---:|
| `models_v3` | none | **53.99 %** | **0.589** | 29.53 % | 1.017 |
| **`models_v3m` — deployed** | `epi_distance_km = −1` | 45.79 % | 0.712 | **33.44 %** | **0.933** |

The constraint costs **8.2 accuracy points on a random split**, which is why it was not obvious to
adopt. It pays for itself the moment whole districts are held out: on 3 district-grouped folds the
constrained model wins accuracy, MAE, QWK (0.482 vs 0.399) and ±1 (79.4 % vs 76.2 %) — every metric,
every fold. The unconstrained model's same-district advantage is memory of *which district* a building
is in, channelled through the distance feature, and it does not exist in a country the model has never
seen. Since the target users are in Myanmar, the deployed model is the constrained one.

The constrained model also passes a distance sweep for both archetypes (`E[grade]` 4.90 → 2.50 for the
mud-stone profile from 2 km to 200 km; 3.56 → 1.23 for engineered RC), which is asserted in
`train_v3_monotone.py` and recorded in the bundle metadata.

Grouped figures above are from the 40k-row stratified subsample that fits the comparison in one
sitting; the run configuration is recorded alongside them in `results_grouped_v3.json`.

---

## 4. Inference contract

```
payload (22 form fields)  +  epi_distance_km (from the hazard engine)
        │
        ├─ build_features: numeric/derived/flags verbatim, categoricals one-hot by vocabulary,
        │                  distance + has_distance, reindex to metadata["features"]
        ├─ four boosters → P(grade > k)
        ├─ monotonicity guard: P(grade > k) ≤ P(grade > k−1), flagged when it fires
        └─ probabilities, E[grade], grade_class, resilience_score, p_severe_grade45, flags
```

* `has_distance = 1` whenever a governing event exists. When none does, the loader warns, neutralises
  the site term at the training mean, and sets the flag `no site distance available`.
* A distance outside the training range (2.4–215.5 km) adds an extrapolation flag rather than silently
  extrapolating.
* `flags` are surfaced in the dashboard, not hidden.

---

## 5. Measured performance

Same-district split (152,419 held-out buildings, seed 42), model v3m (deployed):

| Metric | Value |
|---|---|
| Accuracy | **45.79 %** |
| Macro-F1 | 0.4295 |
| **MAE (grades)** | **0.712** |
| Adjacent accuracy (±1) | 86.54 % |
| Quadratic weighted kappa | 0.6500 |
| AUC (grade ≥ 4) | 0.8094 |
| Majority-class baseline | 36.1 % |

**Cross-district (district-grouped) results** are the honest "works in a country we have no data for"
number: **33.44 % accuracy / MAE 0.933 / QWK 0.482 / ±1 79.4 %**, against 29.53 % / 1.017 / 0.399 /
76.2 % for the unconstrained variant on identical folds. Same-district accuracy overstates transfer by
roughly 12 points, so quote the grouped figure whenever the claim is about Myanmar.

Comparisons on the same split:

| Model | Accuracy | MAE | Notes |
|---|---:|---:|---|
| **Deployed `models_v3m`** (form features + distance, monotone) | 45.79 % | 0.712 | what ships |
| `models_v3` (same features, unconstrained) | 53.99 % | 0.589 | loses on every grouped metric |
| Same, with the form's uncollected fields zero-filled | 50.19 % | 0.632 | the cost of a user skipping the new sections |
| Upper bound with ward-level ShakeMap intensity | 56.29 % | 0.550 | not shippable: no intensity field exists for a hypothetical event at an arbitrary site |
| Retired 3-class artifact, as the API fed it | 19.3 % | 1.065 | on the DrivenData table |

### What did not work (measured, not assumed)

New globally-available site features (SRTM topography, USGS ShakeMap intensity measures including site
velocity) gained +1.13 points same-district and **lost 1.19 points cross-district** — they encode which
district a building is in. Loss functions aimed directly at MAE, threshold tuning, SMOTE-style
oversampling, soft-label mixup, seed ensembling and a two-stage structural-index hybrid were all
neutral or negative. District/ward identity features gain ~13 points on a random split and lose ~9.5
on unseen districts. Full tables: the ML research notes (`backend/docs` deliberately does not restate
them).

---

## 6. Retraining

```bash
cd ~/HermesWork/resilienceai-ml-research
SMOKE=1 .venv/bin/python train_v3.py          # ~3 min sanity pass on a 20k subsample — always first
.venv/bin/python train_v3.py                  # full run, ~25 min on 4 cores
.venv/bin/python train_v3_monotone.py         # the constrained variant
.venv/bin/python verify_v3_served.py          # service-path accuracy + archetype checks
```

Then copy `ordinal_grade_gt*.pkl` + `model_metadata.json` into
`backend/models/seismic_damage_v3/` and restart the backend. Splits are seeded (42) and the data
hashes in the metadata identify the exact inputs.

---

## 7. Limitations

| Limitation | Consequence |
|---|---|
| **Trained on one earthquake in one country** (Nepal 2015, 11 districts) | It is a screening model for buildings and sites resembling Nepal's 2015 stock. Mid-rise engineered RC frames, common in Yangon and Mandalay, are barely represented (4.2 % RC foundations). |
| **Same-district vs cross-district gap** | Random-split accuracy is optimistic by roughly 17 points for districts the model has never seen. Quote the grouped number when the claim is "works anywhere". |
| **Distance is monotone only because it is constrained** | The deployed model constrains `P(grade>k)` to be non-increasing in distance, which costs 8.2 points same-district and buys ~4 points cross-district. See §3. |
| **Weakly shaken sites are out of distribution** | Every training building was strongly shaken (MMI 6.24–8.0). A low-hazard site still gets a comparatively high damage estimate; gate low-hazard sites rather than trusting the raw number. |
| **No multi-hazard input** | Flood and cyclone are not modelled. |
| **Point predictions with real uncertainty** | The distribution is calibrated, but there is no conformal interval or quantile regression; the spread is the model's, not a coverage guarantee. |
