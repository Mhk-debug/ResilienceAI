# Resilience Scoring Documentation

> **How the building damage model turns a building profile + site into a damage distribution, a
> 0–100 resilience score, and a composite risk score.**

The scoring engine was replaced in September 2026. The previous version read three class
probabilities (`P(Low)/P(Medium)/P(High)`) out of a 3-class DrivenData-trained classifier and
combined them as `P(Low)·100 + P(Medium)·45`. That model was retired because the API only ever
supplied 13 of its 43 inputs (the rest were constant zeros) and it measured 19.3 % accuracy on the
served path against a 56.9 % majority-class baseline. The current engine is described below; the
measured performance lives in `machine_learning.md` and in
`backend/models/seismic_damage_v3/MODEL_CARD.md`.

---

## What the model outputs

An ordinal model over damage grades 1–5 (1 = no damage, 5 = destruction), implemented as a
cumulative-link decomposition: four binary boosters estimate `P(grade > k)` for k = 1…4, and the
five class probabilities are recovered from consecutive differences:

```
P(grade = 1) = 1 − P(grade > 1)
P(grade = 2) = P(grade > 1) − P(grade > 2)
...
P(grade = 5) = P(grade > 4)

E[grade] = 1 + Σ_k P(grade > k)
```

Independently trained binaries can cross (`P(grade > 2) > P(grade > 1)`), which would produce a
negative probability. `services/damage_model.py` enforces `P(grade > k) ≤ P(grade > k−1)` with
`np.minimum.accumulate` and records a caveat in the response `flags` when it fires.

---

## The 0–100 resilience score

```python
# services/damage_model.py
expected_grade = 1.0 + sum(P_grade_gt_k)
resilience_score = clip(100.0 * (5.0 - expected_grade) / 4.0, 0, 100)
```

- **100** — the model expects no damage (`E[grade] = 1`), the building is effectively untested
- **0** — the model expects total destruction (`E[grade] = 5`)

Because `E[grade]` is a continuous expectation, the score is continuous even though the model is a
classifier. Two buildings with the same most-likely grade get different scores when their
distributions differ in spread.

### Interpretation

| Resilience score | Expected grade | Reading |
|---|---|---|
| 85–100 | ≤ 1.6 | **Highly resilient** — damage, if any, is cosmetic |
| 60–84 | 1.6–2.6 | **Resilient** — repairable damage expected |
| 35–59 | 2.6–3.6 | **Vulnerable** — structural damage likely; retrofit worth costing |
| 0–34 | > 3.6 | **Highly vulnerable** — severe damage or collapse probable |

### Reporting the uncertainty, not just the number

The response carries the whole distribution:

| Field | Meaning |
|---|---|
| `probabilities` | `{grade1 … grade5}`, the model's calibrated class probabilities |
| `expected_grade` | `E[grade]`, what the score is derived from |
| `grade_class` | the most likely single grade (max probability) |
| `p_severe_grade45` | `P(grade ≥ 4)` — severe damage or collapse |
| `flags` | model caveats: extrapolated site term, non-monotone correction, missing inputs |

The dashboard shows these as a stacked distribution plus a severe-damage callout, deliberately
instead of a single number: the model's own calibration is exact (mean predicted
`P(grade = 1)` 0.103 vs observed 0.103 on held-out data), so the spread is information the user
should see.

---

## Relationship to the hazard score

| Aspect | Resilience score | Hazard score |
|---|---|---|
| Source | Building + site distance (ML) | Site environment (deterministic engine) |
| Range | 0–100 | 0–100 |
| Meaning | Damage this building takes when shaken | How violent the shaking at this site can be |
| High = good | Yes | No (high = worse) |

The two are **not independent**: the damage model conditions on the epicentral distance to the
governing event the hazard engine identified. That is a deliberate one-directional dependency —
hazard engine first, then the building — and it is why the composite score is a product rather than a
sum.

---

## Composite risk score

```
vulnerability = (expected_grade − 1) / 4          # 0 = no damage expected, 1 = destruction
risk_score    = (hazard_score / 100) × vulnerability × 100
```

The previous formula was `hazard·0.6 + (100 − resilience)·0.4`. Once the damage model is conditioned
on the site's shaking, that counted shaking twice: the hazard score already expresses how violent the
ground motion is, and the resilience term then encoded it again. The product form keeps both terms
meaningful — *hazard* is the demand, *vulnerability* is the response.

### Risk bands

```typescript
// frontend/utils/risk.ts
risk ≤ 15  → Low
risk ≤ 30  → Moderate
risk ≤ 45  → High
risk > 45  → Critical
```

Band edges are the vulnerability thresholds for minor / moderate / severe expected damage (0.25 /
0.50 / 0.75 on the damage ratio) scaled by a reference hazard score of 60. They are deliberately not
population terciles: the training population is a strongly shaken, heavily damaged one (median
vulnerability 0.72), so terciles would place almost every realistic assessment in the top band.

### Worked example

Mandalay (21.9769, 96.0836), mud-mortar stone, 3 storeys, 42 years, moderate slope, attached on two
sides:

```
hazard score          70.1 / 100          (governing event M7.7, 15.65 km away)
probabilities         g1 0.001  g2 0.143  g3 0.697  g4 0.045  g5 0.115
E[grade]              3.13                → resilience score 46.76
vulnerability         0.53
risk_score            (70.1/100) × 0.53 × 100 = 37   → High
p_severe_grade45      0.16
```

---

## Integration with the LLM context

`services/resilience_service.py` puts the distribution into `BuildingLLMContext.damage` so the model
reasons about the severe-damage probability and the spread, not just a point score:

```python
"damage": {
    "expected_damage_grade": 3.13,
    "most_likely_grade": 3,
    "grade_probabilities": {"grade1": 0.0011, "grade2": 0.1425, "grade3": 0.6966,
                            "grade4": 0.045, "grade5": 0.1147},
    "severe_damage_probability_grade4_or_5": 0.1597,
    "resilience_score": 46.76,
    "model_version": "damage-v3-ordinal",
}
```

---

## Validation & Testing

```bash
cd backend && .venv/bin/python -m pytest -q          # 102 tests
.venv/bin/python scripts/validate_pipeline.py        # per-scenario scores + distributions
```

`validate_pipeline.py` prints the resilience score, expected grade, severe-damage probability and the
full distribution for each scenario, and surfaces any model caveats.

---

## Known behaviours

| Behaviour | Explanation |
|---|---|
| Score can be exactly 100 | only when the model puts essentially all mass on grade 1 |
| Score can be 0 | only when the model puts essentially all mass on grade 5 |
| Score moves with the site | the model's site term is the distance to the governing event, so the same building scores differently at different sites — that is intended |
| Site term is bounded | the training range is 2.4–215.5 km; outside it the response carries an extrapolation caveat |
| Out-of-distribution shaking | the training data is entirely strongly-shaken buildings (MMI 6.24–8.0). Weakly shaken sites are a known limitation, not a solved case |
| Rounding | the score is rounded to 2 decimals in the response |
