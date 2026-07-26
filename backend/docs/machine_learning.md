# Machine Learning Documentation

> **XGBoost damage grade prediction model for building seismic resilience**

---

## Model Purpose

Predict building damage grade (Low/Medium/High) from structural characteristics using the **Richter Predictor dataset** (Nepal 2015 Gorkha earthquake, ~260K buildings). The model outputs class probabilities which are converted to a continuous **Structural Seismic Resilience Score (0-100)**.

---

## Model Artifacts

| File | Path | Description |
|------|------|-------------|
| Model | `backend/models/seismic_resilience_xgb.pkl` | Joblib-serialized XGBoost classifier |
| Features | `backend/models/model_features.json` | Ordered list of 121 expected feature names |

**Loading (in `main.py` lifespan):**
```python
model = joblib.load(MODEL_PATH)
with open(SCHEMA_PATH) as f:
    expected_features = json.load(f)
```

---

## Training Data: Richter Predictor Dataset

**Source:** DrivenData "Richter's Predictor: Modeling Earthquake Damage" competition

| Aspect | Detail |
|--------|--------|
| Event | 2015 Gorkha Earthquake (M7.8), Nepal |
| Buildings | ~260,000 surveyed |
| Target | `damage_grade` (1=Low, 2=Medium, 3=High) |
| Features | 30 raw → ~121 engineered (after OHE) |
| Key structural features | age, floors, height, area, material flags, foundation/roof/floor type |

**Material Flags (mutually exclusive in theory, multi-hot in practice):**
- `has_superstructure_mud_mortar_stone`
- `has_superstructure_rc_engineered`
- `has_superstructure_cement_mortar_brick`
- `has_superstructure_rc_non_engineered`
- `has_superstructure_adobe_mud`
- `has_superstructure_timber`

**Categorical Codes (Richter dataset):**
| Feature | Codes |
|---------|-------|
| `foundation_type` | r, w, i, u, h |
| `roof_type` | n, q, x |
| `ground_floor_type` | f, v, x, m, z |

**Mapping:** See `backend/richtor_mappings.py` for code → description + vulnerability rating.

---

## Input Features (User-Facing)

The API accepts these **raw building parameters** (validated by `BuildingInput` in `project_schema.py`):

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `count_floors_pre_eq` | int | 1–10 | Stories before earthquake |
| `age` | int | 0–999 | Building age (years) |
| `area_sq_ft` | int | 70–5000 | Floor area |
| `height_ft` | int | 6–305 | Building height |
| `foundation_type` | str | 1 char | Code: r/w/i/u/h |
| `roof_type` | str | 1 char | Code: n/q/x |
| `ground_floor_type` | str | 1 char | Code: f/v/x/m/z |
| `has_superstructure_*` | int | 0/1 | 6 material flags |

---

## Feature Engineering Pipeline

**Location:** `services/pipeline.py`

### 1. Physical Dimension Scaling (`scale_user_inputs`)

Maps real-world measurements to **Richter dataset quantile codes** via piecewise-linear interpolation:

```python
# Area mapping
area_sqft_nodes     = [70, 250, 500, 1000, 1800, 3500, 5000]
richter_area_nodes  = [1, 3, 5, 8, 12, 22, 35]

# Height mapping  
height_ft_nodes     = [6, 12, 18, 30, 50, 90, 305]
richter_height_nodes= [2, 3, 5, 8, 14, 25, 32]

area_percentage = np.interp(clamped_area, area_sqft_nodes, richter_area_nodes)
height_percentage = np.interp(clamped_height, height_ft_nodes, richter_height_nodes)
```

**Why?** The training data uses these quantile codes, not raw measurements. Direct interpolation preserves the distributional assumptions the model learned.

---

### 2. Structural Feature Extraction (`StructuralFeatureExtractor`)

Custom `sklearn` transformer (`BaseEstimator`, `TransformerMixin`):

```python
class StructuralFeatureExtractor:
    def transform(self, X):
        # 1. Validate required fields
        required = ['age', 'count_floors_pre_eq', 'height_percentage', 'area_percentage']
        
        # 2. Compute derived mechanical indicators
        X['height_to_floor_ratio'] = X['height_percentage'] / (X['count_floors_pre_eq'] + 1e-5)
        X['area_to_height_ratio'] = X['area_percentage'] / (X['height_percentage'] + 1e-5)
        
        # 3. Material vulnerability flags
        X['is_highly_vulnerable_material'] = (
            X.get('has_superstructure_mud_mortar_stone', 0) == 1) | \
            (X.get('has_superstructure_mud_mortar_brick', 0) == 1)
        
        X['is_engineered_material'] = (
            X.get('has_superstructure_rc_engineered', 0) == 1) | \
            (X.get('has_superstructure_cement_mortar_brick', 0) == 1)
        
        # 4. Structural degradation proxy
        X['structural_age_stress'] = X['age'] * X['count_floors_pre_eq']
        
        # 5. Drop non-structural columns
        drop_cols = ['building_id', 'geo_level_*_id', 'legal_ownership_status',
                     'land_surface_condition', 'position'] + secondary_use_cols
        X = X.drop(columns=drop_cols)
        
        return X
```

**Key Design Decision:** Drops geolocation and socio-economic proxies to prevent "geographical cheating" — the model must learn structural vulnerability, not location correlation.

---

### 3. Categorical Encoding & Schema Alignment

```python
# One-hot encode
categorical = ["foundation_type", "roof_type", "ground_floor_type"]
df_encoded = pd.get_dummies(df_transformed, columns=available_categorical, dtype=int)

# Align to training schema (121 features)
for col in expected_features_list:
    if col not in df_encoded.columns:
        df_encoded[col] = 0
df_final = df_encoded.reindex(columns=expected_features_list, fill_value=0)
```

**Result:** Fixed 121-column feature matrix matching training exactly.

---

## Prediction Process

**Location:** `services/resilience_engine.py` → `calculate_resilience_score()`

```python
def calculate_resilience_score(trained_model, feature_matrix):
    # XGBoost returns probabilities for 3 classes
    # Col 0: P(Low Damage), Col 1: P(Medium Damage), Col 2: P(High Damage)
    probabilities = trained_model.predict_proba(feature_matrix)
    
    low_damage_prob = probabilities[:, 0]
    med_damage_prob = probabilities[:, 1]
    
    # Expected value weighting: Low=100, Medium=45, High=0
    resilience_scores = (low_damage_prob * 100) + (med_damage_prob * 45)
    
    return float(np.round(resilience_scores[0], 2))
```

### Score Interpretation

| Resilience Score | Damage Grade | Interpretation |
|------------------|--------------|----------------|
| 85–100 | Low (Grade 1) | Highly resilient, minor damage expected |
| 50–84 | Medium (Grade 2) | Moderate vulnerability, significant damage possible |
| 0–49 | High (Grade 3) | Fragile, likely severe damage/collapse |

**Weighting Rationale:**
- Low damage → full credit (100)
- Medium damage → partial credit (45) — life safety but major repair
- High damage → zero credit — collapse/loss

---

## Output: `ResilienceAssessmentResponse`

```python
{
    "status": "success",
    "resilience_score": 72.5,           # 0-100 continuous
    "building_llm_context": {
        "structural": {
            "floors": 2,
            "age_years": 25,
            "floor_area_sq_feets": 1200,
            "height_feets": 24
        },
        "material": {
            "roof_type": "Corrugated Galvanized Iron (CGI) sheets",
            "foundation_type": "Reinforced Concrete (RC) / Cement",
            "ground_floor_type": "Reinforced Concrete (RC) slab floor"
        },
        "substructure": {
            "mud_mortar_stone": false,
            "cement_brick": false,
            "rc_engineered": true,
            "rc_non_engineered": false,
            "adobe_mud": false,
            "timber": false
        }
    }
}
```

---

## Model Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **MAE (damage grade)** | ~0.60 | On Richter test set |
| **R² (resilience score)** | ~0.57 | Continuous score vs true grade |
| **Ordinal accuracy** | ~68% | Exact grade match |
| **Adjacent accuracy** | ~92% | Off-by-one or less |

**Training Details (from memory/experiments):**
- XGBoost with loose regularization (not ordinal-specific)
- Trees naturally learn ordinal boundaries
- Mord `LogisticAT` tried but worse (MAE ~1.08)
- Feature importance dominated by: material flags, age, floors, height/area ratios

---

## Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Nepal-specific training data** | May not generalize to Myanmar/other typologies | Knowledge base covers Myanmar adaptations; hazard engine is location-agnostic |
| **No geospatial features** | Cannot learn regional code enforcement differences | Intentional — structural vulnerability should be location-independent |
| **Single event (Gorkha 2015)** | One earthquake, one soil condition | Hazard engine provides site-specific hazard |
| **Material flags multi-hot** | Real buildings mix materials; dataset assumes dominant | User selects primary; KB covers mixed constructions |
| **Ordinal target as classification** | Loses ordinal information in loss function | Trees handle this well empirically; MAE competitive |
| **No uncertainty quantification** | Point prediction only | Confidence from hazard engine + LLM confidence field |

---

## Inference Code Path

```
routes/resilience.py:calculate_pure_resilience()
    └─ services/resilience_service.py:predict_resilience()
        ├─ payload.model_dump()
        ├─ services/pipeline.py:process_and_align_inference_data()
        │   ├─ scale_user_inputs()
        │   ├─ StructuralFeatureExtractor.fit_transform()
        │   ├─ pd.get_dummies()
        │   └─ reindex(expected_features)
        ├─ services/resilience_engine.py:calculate_resilience_score()
        │   └─ model.predict_proba() → weighted score
        └─ BuildingLLMContext construction (richtor_mappings.decode_building_feature)
```

---

## Retraining / Updating

**To retrain:**
1. Obtain new labeled dataset (same schema)
2. Run feature engineering pipeline (`pipeline.py`) on training data
3. Train XGBoost with same hyperparameters
4. Save model: `joblib.dump(model, 'seismic_resilience_xgb.pkl')`
5. Save feature list: `json.dump(list(X.columns), open('model_features.json', 'w'))`
6. Replace files in `backend/models/`
7. Restart backend (lifespan reloads automatically)

**Required hyperparameters** (match training):
```python
# From training experiments
params = {
    'objective': 'multi:softprob',
    'num_class': 3,
    'eta': 0.1,
    'max_depth': 6,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'reg_alpha': 0.1,      # Loose L1
    'reg_lambda': 1.0,     # Loose L2
    'eval_metric': 'mlogloss',
    'n_estimators': 500,
    'early_stopping_rounds': 50
}
```

---

## Validation Script

```bash
# Full pipeline validation including ML
python scripts/validate_pipeline.py

# Output includes:
# Scenario                    Resilience    Hazard    Chunks  LLM Conf  Time
# RC Engineered - Dhaka       72.50         45.2      5       0.87      12.34
# Mud Mortar Stone - Kathmandu 23.10        67.8      4       0.82      14.12
# Adobe Mud - Rural Myanmar   12.30         34.5      3       0.79      11.89
```