import sys
sys.path.insert(0, r"d:\Work\Projects\ResillienceAI\backend")

from services.hazard_engine.usgs import query_usgs_catalog
from services.hazard_engine.weights import compute_event_contribution
from services.hazard_engine.utils import calculate_age_years
from services.hazard_engine.faults import find_nearest_fault
from services.hazard_engine.soil import fetch_soilgrids_data, evaluate_liquefaction_risk
from services.hazard_engine.calibration import calculate_fault_score, calculate_soil_score, calibrate_hazard_score
from services.hazard_engine.scoring import calculate_historical_seismic_hazard

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
    total = 0.0
    for e in events:
        age = calculate_age_years(e["date"])
        total += compute_event_contribution(
            e["distance_km"], e["depth_km"], e["magnitude"], age, 4.0
        )["contribution"]
    ev_score, _ = calculate_historical_seismic_hazard(events, 4.0)
    fault = find_nearest_fault(lat, lon)
    soil = evaluate_liquefaction_risk(fetch_soilgrids_data(lat, lon))
    fault_s = calculate_fault_score(fault["distance_km"])
    soil_s = calculate_soil_score(soil["lsi_score"])
    overall, level, _ = calibrate_hazard_score(ev_score, fault_s, soil_s)
    print(
        f"{name}|raw_sum={total:.3f}|event={ev_score}|fault_d={fault['distance_km']}|"
        f"fault_s={fault_s:.2f}|lsi={soil['lsi_score']:.4f}|soil_s={soil_s:.2f}|"
        f"overall={overall}|n={len(events)}"
    )
