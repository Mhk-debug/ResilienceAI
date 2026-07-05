"""
hazard_engine/statistics.py
"""
from typing import List, Dict, Any, Optional

def compute_catalog_statistics(
    events: List[Dict[str, Any]],
    catalog_span_years: float,
    nearest_fault_distance_km: float,
    soil_classification: str,
    recurrence_m6_years: Optional[float]
) -> Dict[str, Any]:
    has_events = len(events) > 0
    all_mags = [e["magnitude"] for e in events]
    
    largest_eq = max(all_mags) if has_events else None
    closest_eq = min([e["distance_km"] for e in events]) if has_events else None
    avg_depth = sum([e["depth_km"] for e in events]) / len(events) if has_events else None
    avg_mag = sum(all_mags) / len(events) if has_events else None
    
    median_mag = None
    if has_events:
        sorted_mags = sorted(all_mags)
        n = len(sorted_mags)
        if n % 2 != 0:
            median_mag = sorted_mags[n // 2]
        else:
            median_mag = (sorted_mags[n // 2 - 1] + sorted_mags[n // 2]) / 2.0
            
    return {
        "largest_historical_earthquake": round(largest_eq, 1) if largest_eq is not None else None,
        "closest_earthquake_km": round(closest_eq, 2) if closest_eq is not None else None,
        "average_depth_km": round(avg_depth, 2) if avg_depth is not None else None,
        "average_magnitude": round(avg_mag, 2) if avg_mag is not None else None,
        "median_magnitude": round(median_mag, 2) if median_mag is not None else None,
        "events_analyzed": len(events),
        "catalog_span_years": catalog_span_years,
        "nearest_fault_distance_km": nearest_fault_distance_km,
        "estimated_recurrence_interval_years": round(recurrence_m6_years, 1) if recurrence_m6_years is not None else None,
        "soil_classification": soil_classification
    }
