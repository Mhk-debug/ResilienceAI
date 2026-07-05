"""
hazard_engine/shakemap.py
"""
import math
from typing import List, Dict, Any

def estimate_pga_g(mag: float, dist: float, depth: float) -> float:
    c0 = -3.5
    c1 = 0.85
    c2 = 1.15
    c3 = 0.0035
    h = 8.5
    
    R = math.sqrt(dist * dist + depth * depth + h * h)
    ln_pga = c0 + c1 * mag - c2 * math.log(R) - c3 * R
    return math.exp(ln_pga)

def pga_to_mmi(pga_g: float) -> float:
    if pga_g <= 0.0017:
        return 1.0
    if pga_g <= 0.014:
        return 1.0 + 1.5 * (math.log10(pga_g) - math.log10(0.0017)) / (math.log10(0.014) - math.log10(0.0017))
    if pga_g <= 0.039:
        return 3.0 + 1.0 * (math.log10(pga_g) - math.log10(0.014)) / (math.log10(0.039) - math.log10(0.014))
    if pga_g <= 0.092:
        return 4.0 + 1.0 * (math.log10(pga_g) - math.log10(0.039)) / (math.log10(0.092) - math.log10(0.039))
    if pga_g <= 0.18:
        return 5.0 + 1.0 * (math.log10(pga_g) - math.log10(0.092)) / (math.log10(0.18) - math.log10(0.092))
    if pga_g <= 0.34:
        return 6.0 + 1.0 * (math.log10(pga_g) - math.log10(0.18)) / (math.log10(0.34) - math.log10(0.18))
    if pga_g <= 0.65:
        return 7.0 + 1.0 * (math.log10(pga_g) - math.log10(0.34)) / (math.log10(0.65) - math.log10(0.34))
    return min(12.0, 8.0 + 2.0 * (math.log10(pga_g) - math.log10(0.65)))

def integrate_shakemap_data(events: List[Dict[str, Any]], lat: float, lon: float) -> Dict[str, Any]:
    sig_events = [e for e in events if e["magnitude"] >= 5.5 and e["distance_km"] <= 80.0]
    peak_pga = 0.0
    peak_mmi = 1.0
    
    if sig_events:
        dominant = sorted(sig_events, key=lambda x: x["magnitude"], reverse=True)[0]
        est_pga = estimate_pga_g(dominant["magnitude"], dominant["distance_km"], dominant["depth_km"])
        peak_pga = est_pga
        peak_mmi = pga_to_mmi(est_pga)
        
        if dominant.get("max_mmi") is not None:
            ratio = est_pga / estimate_pga_g(dominant["magnitude"], 1.0, dominant["depth_km"])
            peak_mmi = max(1.0, min(12.0, dominant["max_mmi"] * (1.0 - (1.0 - ratio))))
            
    return {
        "peak_pga": round(peak_pga, 4),
        "peak_mmi": round(peak_mmi, 2)
    }
