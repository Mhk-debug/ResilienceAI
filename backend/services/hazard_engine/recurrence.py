"""
hazard_engine/recurrence.py
"""
import math
from typing import Dict, Any, List

def calculate_gutenberg_richter(
    magnitudes: List[float],
    catalog_span_years: float,
    min_magnitude: float
) -> Dict[str, Any]:
    valid = [m for m in magnitudes if m >= min_magnitude]
    if len(valid) < 3:
        return {
            "a_value": None,
            "b_value": None,
            "recurrence_m6_years": None
        }
        
    avg_m = sum(valid) / len(valid)
    bin_correction = 0.05
    b_denom = avg_m - (min_magnitude - bin_correction)
    
    b_value = 1.0
    if b_denom > 0:
        b_value = math.log10(math.e) / b_denom
    b_value = max(0.5, min(2.0, b_value))
    
    annual_rate = len(valid) / max(0.1, catalog_span_years)
    a_value_annual = math.log10(annual_rate) + b_value * min_magnitude
    
    m6_rate = 10.0 ** (a_value_annual - b_value * 6.0)
    recurrence_m6 = 1.0 / m6_rate if m6_rate > 0 else None
    
    return {
        "a_value": a_value_annual + math.log10(max(1.0, catalog_span_years)),
        "b_value": b_value,
        "recurrence_m6_years": recurrence_m6
    }
