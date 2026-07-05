"""
hazard_engine/calibration.py
"""
import math
from typing import Tuple, Dict, Any

def calculate_fault_score(distance_km: float) -> float:
    return 26.0 * math.exp(-max(0.0, distance_km) / 31.0)

def calculate_soil_score(lsi: float) -> float:
    return 14.0 * min(1.0, max(0.0, lsi))

def calibrate_hazard_score(event_score: float, fault_score: float, soil_score: float) -> Tuple[float, str, float]:
    raw_combined = event_score + fault_score + soil_score + 2.5
    
    final_score = 100.0 * (1.0 - math.exp(-raw_combined / 31.8))
    final_score = min(100.0, max(0.0, final_score))
    
    level = classify_hazard_level(final_score)
    
    confidence = 0.95
    if event_score < 1.0:
        confidence -= 0.25
        
    return round(final_score, 1), level, round(confidence, 2)

def classify_hazard_level(score: float) -> str:
    if score < 20.0:
        return "Very Low"
    elif score < 40.0:
        return "Low"
    elif score < 60.0:
        return "Moderate"
    elif score < 80.0:
        return "High"
    else:
        return "Very High"

def get_indicator_colors(score: float, max_possible: float) -> Tuple[str, str]:
    ratio = score / max_possible if max_possible > 0 else 0
    if ratio < 0.3:
        return "Low", "green"
    elif ratio < 0.65:
        return "Moderate", "yellow"
    else:
        return "High", "red"
