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


def process_and_align_inference_data(raw_input_dict, trained_model, expected_features_list):
    """
    Utility wrapper designed for real-time inference execution (e.g., inside FastAPI).
    Converts a single incoming user dictionary payload, pipes it through the Transformer,
    handles structural categorical alignment, and yields the pure array matrix.
    """
    # Convert raw payload into a DataFrame processing space
    df_raw = pd.DataFrame([raw_input_dict])
    
    # Initialize and run our Scikit-Learn transformer class block
    transformer = StructuralFeatureExtractor()
    df_transformed = pd.DataFrame(transformer.fit_transform(df_raw))
    
    # Apply standard One-Hot string dummy variables expansion
    categorical_features = ['foundation_type', 'roof_type', 'ground_floor_type']
    available_cats = [col for col in categorical_features if col in df_transformed.columns]
    df_encoded = pd.get_dummies(df_transformed, columns=available_cats)
    
    # Align structural layout perfectly with the schema layout generated during training
    for col in expected_features_list:
        if col not in df_encoded.columns:
            df_encoded[col] = 0  # Impute absent categorical choices safely with 0
            
    # Force exact dimension sorting order match
    df_final = df_encoded[expected_features_list]
    
    return df_final