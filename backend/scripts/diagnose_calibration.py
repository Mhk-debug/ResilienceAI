"""Standalone calibration diagnostic (no pydantic dependency)."""
import sys
sys.path.insert(0, r"d:\Work\Projects\ResillienceAI\backend")

from services.hazard_engine.faults import find_nearest_fault
from services.hazard_engine.soil import fetch_soilgrids_data, evaluate_liquefaction_risk
from services.hazard_engine.calibration import calculate_fault_score, calculate_soil_score, calibrate_hazard_score
from services.hazard_engine.scoring import calculate_historical_seismic_hazard
from services.hazard_engine.usgs import query_usgs_catalog

CITIES = {
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Yangon": (16.7753, 96.1594),
    "Mandalay": (21.9588, 96.0891),
    "Tokyo": (35.6762, 139.6503),
    "San Francisco": (37.7749, -122.4194),
}

TARGETS = {
    "Singapore": (10, 25),
    "Bangkok": (20, 40),
    "Yangon": (45, 60),
    "Mandalay": (55, 70),
    "Tokyo": (80, 95),
    "San Francisco": (75, 90),
}

print("CURRENT CALIBRATION BASELINE")
print("=" * 70)
for name, (lat, lon) in CITIES.items():
    events, _, _ = query_usgs_catalog(lat, lon, 100, 50, 4.0)
    ev_score, _ = calculate_historical_seismic_hazard(events, 4.0)
    fault = find_nearest_fault(lat, lon)
    soil_props = fetch_soilgrids_data(lat, lon)
    soil_risk = evaluate_liquefaction_risk(soil_props)
    fault_score = calculate_fault_score(fault["distance_km"])
    soil_score = calculate_soil_score(soil_risk["lsi_score"])
    raw = ev_score + fault_score + soil_score
    overall, level, _ = calibrate_hazard_score(ev_score, fault_score, soil_score)
    lo, hi = TARGETS[name]
    ok = "OK" if lo <= overall <= hi else "MISS"

    print(f"{name:15} overall={overall:5.1f} ({level:10}) target=[{lo}-{hi}] {ok}")
    print(f"  event={ev_score:5.2f} fault={fault_score:5.2f} soil={soil_score:5.2f} raw={raw:5.2f} n={len(events)}")
    print(f"  fault: {fault['fault_name']} @ {fault['distance_km']}km")
    print()
