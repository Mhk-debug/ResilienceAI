# Resilience Scoring Documentation

> **How the structural resilience score is calculated from XGBoost damage grade probabilities**

---

## Overview

The **Structural Seismic Resilience Score (0–100)** translates the XGBoost model's damage grade probabilities into a continuous metric where:
- **100** = Extremely resilient (very low damage probability)
- **0** = Extremely fragile (very high collapse probability)

---

## Score Formula

```python
# From services/resilience_engine.py

def calculate_resilience_score(trained_model, feature_matrix):
    # probabilities shape: (N, 3)
    # Col 0: P(Low Damage / Grade 1)
    # Col 1: P(Medium Damage / Grade 2)
    # Col 2: P(High Damage / Grade 3)
    probabilities = trained_model.predict_proba(feature_matrix)
    
    low_damage_prob = probabilities[:, 0]
    med_damage_prob = probabilities[:, 1]
    
    # Expected value weighting
    resilience_scores = (low_damage_prob * 100) + (med_damage_prob * 45)
    
    return float(np.round(resilience_scores[0], 2))
```

### Weighting Rationale

| Damage Grade | Probability | Weight | Contribution |
|--------------|-------------|--------|--------------|
| Grade 1 (Low) | P₁ | 100 | P₁ × 100 |
| Grade 2 (Medium) | P₂ | 45 | P₂ × 45 |
| Grade 3 (High) | P₃ | 0 | P₃ × 0 |

**Why these weights?**
- **Low damage (100)**: Building essentially undamaged, fully functional
- **Medium damage (45)**: Significant structural damage, repairable but major cost/disruption; life safety generally preserved
- **High damage (0)**: Near collapse or collapse; total loss, life safety threatened

The weights represent **expected post-earthquake utility** on a 0–100 scale.

---

## Score Interpretation

| Resilience Score | Damage Grade | Interpretation |
|------------------|--------------|----------------|
| **85–100** | Grade 1 (Low) | **Highly Resilient** — Minor non-structural damage expected |
| **55–84** | Grade 1–2 | **Moderately Resilient** — Some structural damage possible, repairable |
| **30–54** | Grade 2 (Medium) | **Vulnerable** — Significant structural damage likely |
| **0–29** | Grade 2–3 | **Highly Vulnerable** — Severe damage or collapse probable |

---

## Relationship to Hazard Score

The resilience score and hazard score are **independent but combined** in the final assessment:

| Aspect | Resilience Score | Hazard Score |
|--------|------------------|--------------|
| **Source** | Building structure (ML) | Site environment (deterministic) |
| **Range** | 0–100 | 0–100 |
| **Meaning** | Building's inherent capacity | Ground shaking demand |
| **High = Good** | Yes | No (High = Bad) |

**Combined Risk Mental Model:**
```
Risk ≈ Hazard Demand / Structural Capacity
      ≈ Hazard_Score / Resilience_Score
```

- High Hazard + Low Resilience = **Critical Risk**
- Low Hazard + High Resilience = **Low Risk**
- High Hazard + High Resilience = **Managed Risk** (engineered for the hazard)
- Low Hazard + Low Resilience = **Moderate Risk** (unreinforced masonry in stable zone)

---

## Example Calculations

### Example 1: RC Engineered Building
```
XGBoost Probabilities: P(Low)=0.65, P(Med)=0.30, P(High)=0.05
Resilience = 0.65*100 + 0.30*45 + 0.05*0 = 65 + 13.5 = 78.5
→ "Moderately Resilient"
```

### Example 2: Mud Mortar Stone Building
```
XGBoost Probabilities: P(Low)=0.10, P(Med)=0.35, P(High)=0.55
Resilience = 0.10*100 + 0.35*45 + 0.55*0 = 10 + 15.75 = 25.75
→ "Highly Vulnerable"
```

### Example 3: Uncertain Prediction
```
XGBoost Probabilities: P(Low)=0.33, P(Med)=0.34, P(High)=0.33
Resilience = 0.33*100 + 0.34*45 = 33 + 15.3 = 48.3
→ "Vulnerable" (model uncertain, medium damage likely)
```

---

## Integration with LLM Context

The resilience score and building context are combined into `BuildingLLMContext` for the LLM prompt:

```python
# In services/resilience_service.py

context_data = {
    "structural": {
        "floors": raw_input["count_floors_pre_eq"],
        "age_years": raw_input["age"],
        "floor_area_sq_feets": raw_input["area_sq_ft"],
        "height_feets": raw_input["height_ft"]
    },
    "material": {
        "roof_type": decode_building_feature("roof_type", roof_code),
        "foundation_type": decode_building_feature("foundation_type", foundation_code),
        "ground_floor_type": decode_building_feature("ground_floor_type", floor_code)
    },
    "substructure": {
        "mud_mortar_stone": bool(raw_input["has_superstructure_mud_mortar_stone"]),
        "cement_brick": bool(raw_input["has_superstructure_cement_mortar_brick"]),
        "rc_engineered": bool(raw_input["has_superstructure_rc_engineered"]),
        "rc_non_engineered": bool(raw_input["has_superstructure_rc_non_engineered"]),
        "adobe_mud": bool(raw_input["has_superstructure_adobe_mud"]),
        "timber": bool(raw_input["has_superstructure_timber"])
    }
}

building_context = BuildingLLMContext.model_validate(context_data)
```

This context is passed to the LLM alongside the environmental context for joint reasoning.

---

## Validation & Testing

```bash
# Run validation script
python scripts/validate_pipeline.py

# Sample output:
# RC Engineered - Dhaka:       Resilience=72.50
# Mud Mortar Stone - Kathmandu: Resilience=23.10
# Adobe Mud - Rural Myanmar:    Resilience=12.30
```

---

## Known Behaviors

| Behavior | Explanation |
|----------|-------------|
| Score never exceeds 100 | Max P(Low)=1.0 → 100 |
| Score can be 0 | P(Low)=0, P(Med)=0 → 0 |
| Medium damage caps contribution | Even at P(Med)=1.0, max contribution = 45 |
| Rounding | Final score rounded to 2 decimal places |

---

## Future Considerations

- **Uncertainty quantification**: Add prediction intervals via quantile regression or conformal prediction
- **Ordinal calibration**: Ensure P(Low) > P(Med) > P(High) for typical buildings
- **Regional calibration**: Adjust weights for different building codes (e.g., MNBC 2016 vs pre-code)
- **Multi-hazard**: Extend to wind/flood resilience scoring