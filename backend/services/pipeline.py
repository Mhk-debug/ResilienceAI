import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class StructuralFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    A custom Scikit-Learn transformer that cleans raw earthquake building data.
    It isolates structural engineering features by stripping away geolocation data,
    socioeconomic proxies, and secondary use flags, while computing mechanical indicators.
    """
    def __init__(self):
        # Explicit non-structural columns to discard to prevent geographical cheat paths
        self.non_structural_cols = [
            'building_id', 
            'geo_level_1_id', 
            'geo_level_2_id', 
            'geo_level_3_id', 
            'legal_ownership_status',
            'land_surface_condition',
            'position'
        ]
        
    def fit(self, X, y=None):
        # Stateless transformer, fitting is not required
        return self
        
    def transform(self, X):
        # Work on a deep copy to prevent mutating the original DataFrame in place
        X_clean = X.copy()
        
        # 1. Defensive Validation: Ensure critical structural markers exist before math transforms
        required_fields = ['age', 'count_floors_pre_eq', 'height_percentage', 'area_percentage']
        for field in required_fields:
            if field not in X_clean.columns:
                raise ValueError(f"Pipeline Execution Failure: Missing required structural feature '{field}'")
        
        # Assert logical boundary constraints (Data integrity guardrails)
        if (X_clean['age'] < 0).any():
            raise ValueError("Pipeline Execution Failure: Building 'age' metrics cannot be negative numeric spaces.")
        
        X_clean['height_percentage'] = pd.to_numeric(
            X_clean['height_percentage'],
            errors='coerce'
        )

        X_clean['area_percentage'] = pd.to_numeric(
            X_clean['area_percentage'],
            errors='coerce'
        )

        X_clean['count_floors_pre_eq'] = pd.to_numeric(
            X_clean['count_floors_pre_eq'],
            errors='coerce'
        )
            
        # 2. Advanced Feature Extraction: Calculate spatial-free mechanical aspect ratios
        X_clean['height_to_floor_ratio'] = X_clean['height_percentage'] / (X_clean['count_floors_pre_eq'] + 1e-5)
        X_clean['area_to_height_ratio'] = X_clean['area_percentage'] / (X_clean['height_percentage'] + 1e-5)
        
        # Categorize material vulnerability thresholds
        X_clean['is_highly_vulnerable_material'] = 0
        if 'has_superstructure_mud_mortar_stone' in X_clean.columns or 'has_superstructure_mud_mortar_brick' in X_clean.columns:
            mud_stone = X_clean.get('has_superstructure_mud_mortar_stone', 0)
            mud_brick = X_clean.get('has_superstructure_mud_mortar_brick', 0)
            X_clean['is_highly_vulnerable_material'] = ((mud_stone == 1) | (mud_brick == 1)).astype(int)
            
        # Categorize engineered reinforcement thresholds
        X_clean['is_engineered_material'] = 0
        if 'has_superstructure_rc_engineered' in X_clean.columns or 'has_superstructure_cement_mortar_brick' in X_clean.columns:
            rc_eng = X_clean.get('has_superstructure_rc_engineered', 0)
            cement_brick = X_clean.get('has_superstructure_cement_mortar_brick', 0)
            X_clean['is_engineered_material'] = ((rc_eng == 1) | (cement_brick == 1)).astype(int)
            
        # Structural degradation proxy (Fatigue scaling factor)
        X_clean['structural_age_stress'] = X_clean['age'] * X_clean['count_floors_pre_eq']
        
        # 3. Drop Extraneous Spatial & Categorical Proxies
        # Gather all active dynamic secondary use configurations starting with the standard prefix
        secondary_use_cols = [col for col in X_clean.columns if col.startswith('has_secondary_use')]
        drop_list = [col for col in self.non_structural_cols if col in X_clean.columns] + secondary_use_cols
        
        X_clean = X_clean.drop(columns=drop_list)
        
        return X_clean

def scale_user_inputs(plinth_area_sqft: float, height_ft: float) -> dict:
    """
    Translates real physical dimensions into the exact mathematical 
    quantile mappings used by the Richter Predictor dataset.
    """
    # 1. Non-linear mapping for Plinth Area
    # Connects raw sq footage milestones to the exact Richter area_percentage codes
    area_sqft_nodes = [70, 250, 500, 1000, 1800, 3500, 5000]
    richter_area_nodes = [1, 3, 5, 8, 12, 22, 35]
    
    # Bound the inputs to protect against extreme out-of-distribution values
    clamped_area = max(70, min(plinth_area_sqft, 5000))
    area_percentage = np.interp(clamped_area, area_sqft_nodes, richter_area_nodes)
    
    # 2. Non-linear mapping for Building Height
    # Connects raw physical height in feet to the exact height_percentage codes
    height_ft_nodes = [6, 12, 18, 30, 50, 90, 305]
    richter_height_nodes = [2, 3, 5, 8, 14, 25, 32]
    
    clamped_height = max(6, min(height_ft, 305))
    height_percentage = np.interp(clamped_height, height_ft_nodes, richter_height_nodes)
    
    return {
        "area_percentage": int(round(area_percentage)),
        "height_percentage": int(round(height_percentage))
    }

def process_and_align_inference_data(raw_input_dict, trained_model, expected_features_list):
    """
    Prepare a single inference payload so it matches the feature schema used during training.

    The function converts the raw user payload into a structured DataFrame, derives the
    required engineering ratios, applies the feature extractor, one-hot encodes the
    categorical columns, and reorders the final columns to match the training schema.
    """
    if not isinstance(raw_input_dict, dict):
        raise TypeError("Input payload must be provided as a dictionary.")

    required_fields = {"area_sq_ft", "height_ft"}
    missing_fields = required_fields.difference(raw_input_dict.keys())
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing required input field(s): {missing}")

    df_raw = pd.DataFrame([raw_input_dict])

    plinth_area_sqft = df_raw["area_sq_ft"].iloc[0]
    height_ft = df_raw["height_ft"].iloc[0]
    if pd.isna(plinth_area_sqft) or pd.isna(height_ft):
        raise ValueError("Both 'area_sq_ft' and 'height_ft' must be provided in the input payload.")

    plinth_area_sqft = float(plinth_area_sqft)
    height_ft = float(height_ft)

    area_percentage, height_percentage = scale_user_inputs(plinth_area_sqft, height_ft)

    df_raw["area_percentage"] = area_percentage
    df_raw["height_percentage"] = height_percentage

    df_raw = df_raw.drop(columns=["area_sq_ft", "height_ft"], errors="ignore")

    transformer = StructuralFeatureExtractor()
    df_transformed = pd.DataFrame(transformer.fit_transform(df_raw))

    categorical_features = ["foundation_type", "roof_type", "ground_floor_type"]
    available_categorical_columns = [
        col for col in categorical_features if col in df_transformed.columns
    ]
    df_encoded = pd.get_dummies(
        df_transformed,
        columns=available_categorical_columns,
        dtype=int,
    )

    for col in expected_features_list:
        if col not in df_encoded.columns:
            df_encoded[col] = 0

    df_final = df_encoded.reindex(columns=expected_features_list, fill_value=0)
    return df_final