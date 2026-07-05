"""
hazard_engine/scoring.py
"""
import math
from typing import List, Dict, Any, Tuple
from .weights import compute_event_contribution

def calculate_historical_seismic_hazard(
    events: List[Dict[str, Any]],
    min_magnitude: float = 4.0
) -> Tuple[float, List[Dict[str, Any]]]:
    processed_events = []
    total_raw_score = 0.0
    
    for ev in events:
        from .utils import calculate_age_years
        age = calculate_age_years(ev["date"])
        
        weights = compute_event_contribution(
            distance_km=ev["distance_km"],
            depth_km=ev["depth_km"],
            magnitude=ev["magnitude"],
            age_years=age,
            min_magnitude=min_magnitude
        )
        
        total_raw_score += weights["contribution"]
        
        processed_ev = {
            "id": ev["id"],
            "magnitude": ev["magnitude"],
            "distance_km": ev["distance_km"],
            "depth_km": ev["depth_km"],
            "date": ev["date"],
            "place": ev["place"],
            "individual_contribution": round(weights["contribution"], 4),
            "distance_weight": round(weights["distance_weight"], 3),
            "depth_weight": round(weights["depth_weight"], 3),
            "age_weight": round(weights["age_weight"], 3),
            "magnitude_weight": round(weights["magnitude_weight"], 3)
        }
        processed_events.append(processed_ev)
        
    processed_events = sorted(processed_events, key=lambda x: x["individual_contribution"], reverse=True)
    
    event_score = min(35.0, 13.0 * math.log(1.0 + total_raw_score))
    
    return round(event_score, 2), processed_events
