"""
hazard_engine/engine.py
"""
import time
from typing import Dict, Any, List

from project_schema import HazardInput, HazardReport
from .usgs import query_usgs_catalog
from .shakemap import integrate_shakemap_data
from .soil import fetch_soilgrids_data, evaluate_liquefaction_risk
from .faults import find_nearest_fault
from .scoring import calculate_historical_seismic_hazard
from .recurrence import calculate_gutenberg_richter
from .calibration import (
    calculate_fault_score,
    calculate_soil_score,
    calibrate_hazard_score,
    get_indicator_colors
)
from .statistics import compute_catalog_statistics

async def calculate_hazard(
    latitude: float,
    longitude: float,
    search_radius_km: float = 100.0,
    historical_years: float = 50.0,
    minimum_magnitude: float = 4.5
) -> Dict[str, Any]:
    start_time = time.time()
    warnings = []
    api_status = {}
    
    place_name = f"Grid Reference [{latitude:.4f}, {longitude:.4f}]"
    
    events, usgs_status, usgs_warnings = query_usgs_catalog(
        latitude=latitude,
        longitude=longitude,
        search_radius_km=search_radius_km,
        historical_years=historical_years,
        min_magnitude=minimum_magnitude
    )
    warnings.extend(usgs_warnings)
    api_status["USGS_Catalog"] = usgs_status["status"]
    
    soil_props = await fetch_soilgrids_data(latitude, longitude)
    api_status["SoilGrids"] = "success" if "API" in soil_props["source"] else "fallback"
    if "Fallback" in soil_props["source"]:
        warnings.append(f"SoilGrids API query failed or timed out. {soil_props['source']} utilized.")
        
    soil_risk = evaluate_liquefaction_risk(soil_props)
    
    fault_proximity = find_nearest_fault(latitude, longitude)
    
    event_score, processed_events = calculate_historical_seismic_hazard(events, minimum_magnitude)
    
    fault_score = calculate_fault_score(fault_proximity["distance_km"])
    soil_score = calculate_soil_score(soil_risk["lsi_score"])
    
    overall_score, hazard_level, confidence = calibrate_hazard_score(event_score, fault_score, soil_score)
    
    all_mags = [e["magnitude"] for e in events]
    recurrence_data = calculate_gutenberg_richter(all_mags, historical_years, minimum_magnitude)
    
    shakemap_data = integrate_shakemap_data(events, latitude, longitude)
    
    catalog_stats = compute_catalog_statistics(
        events=events,
        catalog_span_years=historical_years,
        nearest_fault_distance_km=fault_proximity["distance_km"],
        soil_classification=soil_risk["soil_class"],
        recurrence_m6_years=recurrence_data["recurrence_m6_years"]
    )
    
    hist_level, hist_color = get_indicator_colors(event_score, 28.0)
    soil_level, soil_color = get_indicator_colors(soil_score, 12.0)
    
    zone_score = event_score * 0.6 + fault_score * 0.4
    zone_level, zone_color = get_indicator_colors(zone_score, 24.0)
    
    indicators = {
        "seismic_zone": {
            "value": f"Zone {zone_level}",
            "classification": f"{zone_level} regional seismic energy buildup",
            "color": zone_color
        },
        "historical_activity": {
            "value": f"{len(events)} events analyzed",
            "classification": f"{hist_level} historical activity density",
            "color": hist_color
        },
        "soil_liquefaction": {
            "value": soil_risk["soil_class"],
            "classification": soil_risk["classification"],
            "color": soil_color
        },
        "fault_proximity": {
            "value": f"{fault_proximity['distance_km']} km",
            "classification": f"Proximity to {fault_proximity['fault_name']} ({fault_proximity['classification']})",
            "color": fault_proximity["color"]
        }
    }
    
    summary_sentences = [
        f"The geographic query location has a calibrated overall Seismic Hazard Score of {overall_score}/100, resulting in a '{hazard_level}' classification.",
        f"Proximity risk is dominated by the {fault_proximity['fault_name']} fault system located {fault_proximity['distance_km']} km away, representing a '{fault_proximity['classification']}' rating.",
        f"Local surface soil texture consists of {soil_risk['soil_class']} with a loose bulk density of {soil_props['bulk_density']} g/cm^3, causing a '{soil_risk['classification']}' profile with a seismic wave amplification factor of {soil_risk['amplification_multiplier']}x.",
    ]
    if len(events) > 0:
        summary_sentences.append(f"Historical earthquake record shows {len(events)} analyzed events of M{minimum_magnitude}+ within a {search_radius_km}km radius over the past {historical_years} years. The largest event registered magnitude M{catalog_stats['largest_historical_earthquake']} located {catalog_stats['closest_earthquake_km']}km away.")
        if recurrence_data["recurrence_m6_years"]:
            summary_sentences.append(f"Local Gutenberg-Richter b-value is calculated at {recurrence_data['b_value']:.2f}, indicating a statistical M6.0+ recurrence interval of approximately {recurrence_data['recurrence_m6_years']:.1f} years.")
    else:
        summary_sentences.append(f"No historical earthquake events of magnitude M{minimum_magnitude}+ were found within {search_radius_km}km of coordinates in the past {historical_years} years, indicating a highly stable geological crust.")
        
    environmental_context = {
        "hazard_score": overall_score,
        "hazard_level": hazard_level,
        "historical_activity": {
            "classification": hist_level,
            "events_within_radius": len(events),
            "largest_magnitude": catalog_stats["largest_historical_earthquake"]
        },
        "faults": {
            "distance_km": fault_proximity["distance_km"],
            "classification": fault_proximity["classification"]
        },
        "soil": {
            "classification": soil_risk["classification"],
            "dominant_soil": soil_risk["soil_class"]
        },
        "ground_motion": {
            "estimated_mmi": shakemap_data["peak_mmi"],
            "estimated_pga_g": shakemap_data["peak_pga"],
            "confidence": confidence
        },
        "summary": summary_sentences
    }
    
    execution_time = time.time() - start_time
    
    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "place_name": place_name
        },
        "hazard": {
            "overall_score": overall_score,
            "hazard_level": hazard_level,
            "confidence": confidence
        },
        "indicators": indicators,
        "statistics": catalog_stats,
        "environmental_context": environmental_context,
        "events": processed_events,
        "metadata": {
            "warnings": warnings,
            "execution_time_seconds": round(execution_time, 4),
            "api_status": api_status,
            "model_version": "v1.1.2-deterministic"
        }
    }

async def calculate_hazard_pydantic(inputs: HazardInput) -> HazardReport:
    # Ensure optional numeric inputs from the Pydantic model are coerced to
    # concrete float values expected by calculate_hazard.
    search_radius = inputs.search_radius_km if inputs.search_radius_km is not None else 100.0
    historical_years = inputs.historical_years if inputs.historical_years is not None else 50.0
    minimum_magnitude = inputs.minimum_magnitude if inputs.minimum_magnitude is not None else 4.5

    report_dict = await calculate_hazard(
        latitude=inputs.latitude,
        longitude=inputs.longitude,
        search_radius_km=search_radius,
        historical_years=historical_years,
        minimum_magnitude=minimum_magnitude
    )
    return HazardReport(**report_dict)
