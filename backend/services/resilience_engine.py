import numpy as np

def calculate_resilience_score(trained_model, feature_matrix):
    """
    Translates raw XGBoost class probabilities into a continuous 
    Structural Seismic Resilience Score scaled from 0 (Extremely Fragile) to 100 (Highly Resilient).
    """
    # Get probability matrices: shape (N, 3)
    # Col 0: P(Low Damage), Col 1: P(Medium Damage), Col 2: P(High Damage)
    probabilities = trained_model.predict_proba(feature_matrix)
    
    # Mathematical Expected Value Weighting Matrix
    # We assign maximal value to Low Damage survival, moderate value to partial damage, and 0 to collapse.
    low_damage_prob = probabilities[:, 0]
    med_damage_prob = probabilities[:, 1]
    
    # Linear scale calculation
    resilience_scores = (low_damage_prob * 100) + (med_damage_prob * 45)

    return float(np.round(resilience_scores[0], 2))