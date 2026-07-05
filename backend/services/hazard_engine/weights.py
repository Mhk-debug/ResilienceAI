"""
hazard_engine/weights.py
"""
import math
from typing import Dict, Any
from .constants import (
    DECAY_DISTANCE_KM,
    DECAY_DEPTH_KM,
    MAGNITUDE_DAMAGE_COEFF,
    DECAY_AGE_YEARS
)

def compute_distance_weight(d: float) -> float:
    return math.exp(-max(0.0, d) / DECAY_DISTANCE_KM)

def compute_depth_weight(z: float) -> float:
    return math.exp(-max(0.0, z) / DECAY_DEPTH_KM)

def compute_magnitude_weight(m: float, min_magnitude: float) -> float:
    if m < min_magnitude:
        return 0.0
    return math.exp(MAGNITUDE_DAMAGE_COEFF * (m - min_magnitude))

def compute_age_weight(t: float) -> float:
    return math.exp(-max(0.0, t) / DECAY_AGE_YEARS)

def compute_event_contribution(
    distance_km: float,
    depth_km: float,
    magnitude: float,
    age_years: float,
    min_magnitude: float
) -> Dict[str, Any]:
    w_dist = compute_distance_weight(distance_km)
    w_depth = compute_depth_weight(depth_km)
    w_mag = compute_magnitude_weight(magnitude, min_magnitude)
    w_age = compute_age_weight(age_years)
    
    contribution = w_dist * w_depth * w_mag * w_age
    return {
        "distance_weight": w_dist,
        "depth_weight": w_depth,
        "magnitude_weight": w_mag,
        "age_weight": w_age,
        "contribution": contribution
    }
