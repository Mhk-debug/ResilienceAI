"""Detailed historical raw score analysis."""
import sys
import math
sys.path.insert(0, r"d:\Work\Projects\ResillienceAI\backend")

from services.hazard_engine.usgs import query_usgs_catalog
from services.hazard_engine.scoring import calculate_historical_seismic_hazard
from services.hazard_engine.weights import compute_event_contribution
from services.hazard_engine.utils import calculate_age_years
from services.hazard_engine.faults import find_nearest_fault
from services.hazard_engine.soil import fetch_soilgrids_data, evaluate_liquefaction_risk
from services.hazard_engine.calibration import calculate_fault_score, calculate_soil_score, calibrate_hazard_score

CITIES = {
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Yangon": (16.7753, 96.1594),
    "Mandalay": (21.9588, 96.0891),
    "Tokyo": (35.6762, 139.6503),
    "San Francisco": (37.7749, -122.4194),
}

for name, (lat, lon) in CITIES.items():
    events, _, _ = query_usgs_catalog(lat, lon, 100, 50, 4.0)
    total_raw = 0.0
    for ev in events:
        age = calculate_age_years(ev["date"])
        w = compute_event_contribution(ev["distance_km"], ev["depth_km"], ev["magnitude"], age, 4.0)
        total_raw += w["contribution"]
    ev_score, _ = calculate_historical_seismic_hazard(events, 4.0)
    fault = find_nearest_fault(lat, lon)
    fault_score = calculate_fault_score(fault["distance_km"])
    soil_risk = evaluate_liquefaction_risk(fetch_soilgrids_data(lat, lon))
    soil_score = calculate_soil_score(soil_risk["lsi_score"])
    overall, level, _ = calibrate_hazard_score(ev_score, fault_score, soil_score)
    print(f"{name}: n={len(events):4d} total_raw={total_raw:7.2f} event_score={ev_score:5.2f} "
          f"fault={fault_score:5.2f} soil={soil_score:5.2f} overall={overall}")

# Test Japan Trench distance for Tokyo
from services.hazard_engine.utils import distance_to_line_segment
from services.hazard_engine.constants import MAJOR_FAULTS
lat, lon = 35.6762, 139.6503
for fname, verts in MAJOR_FAULTS.items():
    min_d = 9999
    for i in range(len(verts)-1):
        d = distance_to_line_segment(lat, lon, verts[i][0], verts[i][1], verts[i+1][0], verts[i+1][1])
        min_d = min(min_d, d)
    print(f"Tokyo -> {fname}: {min_d:.1f} km")
