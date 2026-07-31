"""
hazard_engine/engine.py

Orchestrates seismic hazard calculation with per-component isolation and a
full degraded fallback so external API failures never crash the assessment.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from project_schema import HazardInput, HazardReport
from .usgs import query_usgs_catalog
from .shakemap import integrate_shakemap_data
from .soil import fetch_soilgrids_data, evaluate_liquefaction_risk, get_fallback_soil_properties
from .faults import find_nearest_fault
from .scoring import calculate_historical_seismic_hazard
from .recurrence import calculate_gutenberg_richter
from .calibration import (
    calculate_fault_score,
    calculate_soil_score,
    calibrate_hazard_score,
    get_indicator_colors,
)
from .statistics import compute_catalog_statistics

logger = logging.getLogger(__name__)


def _safe_fault_proximity(latitude: float, longitude: float) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        return find_nearest_fault(latitude, longitude), None
    except Exception as e:
        logger.exception("Fault proximity calculation failed")
        return {
            "fault_name": "Unmapped Local Crustal Fault",
            "distance_km": 120.0,
            "classification": "Low Proximity",
            "color": "green",
        }, f"Fault proximity calculation failed; using conservative default. ({e})"


def _safe_historical_score(
    events: List[Dict[str, Any]],
    minimum_magnitude: float,
) -> Tuple[float, List[Dict[str, Any]], Optional[str]]:
    try:
        event_score, processed_events = calculate_historical_seismic_hazard(
            events, minimum_magnitude
        )
        return event_score, processed_events, None
    except Exception as e:
        logger.exception("Historical seismic scoring failed")
        return 0.0, [], f"Historical seismic scoring failed; event score set to 0. ({e})"


def _safe_recurrence(
    magnitudes: List[float],
    historical_years: float,
    minimum_magnitude: float,
) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        return calculate_gutenberg_richter(magnitudes, historical_years, minimum_magnitude), None
    except Exception as e:
        logger.exception("Gutenberg-Richter recurrence failed")
        return {
            "a_value": None,
            "b_value": None,
            "recurrence_m6_years": None,
        }, f"Recurrence analysis failed. ({e})"


def _safe_shakemap(
    events: List[Dict[str, Any]],
    latitude: float,
    longitude: float,
) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        return integrate_shakemap_data(events, latitude, longitude), None
    except Exception as e:
        logger.exception("ShakeMap integration failed")
        return {
            "peak_pga": 0.0,
            "peak_mmi": 1.0,
        }, f"Ground-motion estimate failed; defaults applied. ({e})"


def _safe_catalog_stats(
    events: List[Dict[str, Any]],
    historical_years: float,
    nearest_fault_distance_km: float,
    soil_classification: str,
    recurrence_m6_years: Optional[float],
) -> Tuple[Dict[str, Any], Optional[str]]:
    try:
        return compute_catalog_statistics(
            events=events,
            catalog_span_years=historical_years,
            nearest_fault_distance_km=nearest_fault_distance_km,
            soil_classification=soil_classification,
            recurrence_m6_years=recurrence_m6_years,
        ), None
    except Exception as e:
        logger.exception("Catalog statistics failed")
        return {
            "largest_historical_earthquake": None,
            "closest_earthquake_km": None,
            "average_depth_km": None,
            "average_magnitude": None,
            "median_magnitude": None,
            "events_analyzed": len(events),
            "catalog_span_years": historical_years,
            "nearest_fault_distance_km": nearest_fault_distance_km,
            "estimated_recurrence_interval_years": None,
            "soil_classification": soil_classification,
        }, f"Catalog statistics failed. ({e})"


def _build_degraded_report(
    latitude: float,
    longitude: float,
    search_radius_km: float,
    historical_years: float,
    minimum_magnitude: float,
    start_time: float,
    error: Exception,
    partial: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Last-resort report so the assessment pipeline can always continue.
    Uses only local/deterministic inputs (faults + regional soil heuristics).
    """
    partial = partial or {}
    warnings = list(partial.get("warnings", []))
    warnings.append(
        f"Hazard engine entered degraded mode due to unexpected failure: {error}"
    )
    api_status = dict(partial.get("api_status", {}))
    api_status.setdefault("USGS_Catalog", "unavailable")
    api_status.setdefault("SoilGrids", "fallback")
    api_status["engine"] = "degraded"

    events = partial.get("events") or []
    soil_props = partial.get("soil_props") or get_fallback_soil_properties(latitude, longitude)
    try:
        soil_risk = evaluate_liquefaction_risk(soil_props)
    except Exception:
        soil_risk = {
            "lsi_score": 0.2,
            "classification": "Moderate Liquefaction Risk",
            "color": "yellow",
            "soil_class": "Loam",
            "amplification_multiplier": 1.15,
            "assumptions": ["Degraded-mode default soil risk."],
        }

    fault_proximity, fault_warn = _safe_fault_proximity(latitude, longitude)
    if fault_warn:
        warnings.append(fault_warn)

    event_score = float(partial.get("event_score", 0.0))
    fault_score = calculate_fault_score(fault_proximity["distance_km"])
    soil_score = calculate_soil_score(soil_risk["lsi_score"])
    overall_score, hazard_level, confidence = calibrate_hazard_score(
        event_score, fault_score, soil_score
    )
    # Degraded mode always reduces confidence.
    confidence = round(max(0.2, confidence - 0.35), 2)

    catalog_stats = {
        "largest_historical_earthquake": None,
        "closest_earthquake_km": None,
        "average_depth_km": None,
        "average_magnitude": None,
        "median_magnitude": None,
        "events_analyzed": len(events),
        "catalog_span_years": historical_years,
        "nearest_fault_distance_km": fault_proximity["distance_km"],
        "estimated_recurrence_interval_years": None,
        "soil_classification": soil_risk["soil_class"],
    }

    hist_level, hist_color = get_indicator_colors(event_score, 28.0)
    soil_level, soil_color = get_indicator_colors(soil_score, 12.0)
    zone_score = event_score * 0.6 + fault_score * 0.4
    zone_level, zone_color = get_indicator_colors(zone_score, 24.0)

    indicators = {
        "seismic_zone": {
            "value": f"Zone {zone_level}",
            "classification": f"{zone_level} regional seismic energy buildup",
            "color": zone_color,
        },
        "historical_activity": {
            "value": f"{len(events)} events analyzed",
            "classification": f"{hist_level} historical activity density",
            "color": hist_color,
        },
        "soil_liquefaction": {
            "value": soil_risk["soil_class"],
            "classification": soil_risk["classification"],
            "color": soil_color,
        },
        "fault_proximity": {
            "value": f"{fault_proximity['distance_km']} km",
            "classification": (
                f"Proximity to {fault_proximity['fault_name']} "
                f"({fault_proximity['classification']})"
            ),
            "color": fault_proximity["color"],
        },
    }

    summary_sentences = [
        (
            f"The geographic query location has a calibrated overall Seismic Hazard Score of "
            f"{overall_score}/100, resulting in a '{hazard_level}' classification."
        ),
        (
            "This result was produced in degraded mode because one or more external hazard "
            "data sources were unavailable; confidence is reduced."
        ),
        (
            f"Proximity risk is dominated by the {fault_proximity['fault_name']} fault system "
            f"located {fault_proximity['distance_km']} km away, representing a "
            f"'{fault_proximity['classification']}' rating."
        ),
        (
            f"Local surface soil texture consists of {soil_risk['soil_class']} "
            f"(source: {soil_props.get('source', 'fallback')}), causing a "
            f"'{soil_risk['classification']}' profile."
        ),
    ]

    environmental_context = {
        "hazard_score": overall_score,
        "hazard_level": hazard_level,
        "historical_activity": {
            "classification": hist_level,
            "events_within_radius": len(events),
            "largest_magnitude": catalog_stats["largest_historical_earthquake"],
        },
        "faults": {
            "distance_km": fault_proximity["distance_km"],
            "classification": fault_proximity["classification"],
        },
        "soil": {
            "classification": soil_risk["classification"],
            "dominant_soil": soil_risk["soil_class"],
        },
        "ground_motion": {
            "estimated_mmi": 1.0,
            "estimated_pga_g": 0.0,
            "confidence": confidence,
        },
        "summary": summary_sentences,
    }

    execution_time = time.time() - start_time
    place_name = f"Grid Reference [{latitude:.4f}, {longitude:.4f}]"

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "place_name": place_name,
        },
        "hazard": {
            "overall_score": overall_score,
            "hazard_level": hazard_level,
            "confidence": confidence,
        },
        "indicators": indicators,
        "statistics": catalog_stats,
        "environmental_context": environmental_context,
        "events": partial.get("processed_events") or [],
        "metadata": {
            "warnings": warnings,
            "execution_time_seconds": round(execution_time, 4),
            "api_status": api_status,
            "model_version": "v1.1.2-deterministic",
            "degraded": True,
        },
    }


async def calculate_hazard(
    latitude: float,
    longitude: float,
    search_radius_km: float = 100.0,
    historical_years: float = 50.0,
    minimum_magnitude: float = 4.5,
) -> Dict[str, Any]:
    start_time = time.time()
    warnings: List[str] = []
    api_status: Dict[str, Any] = {}
    partial: Dict[str, Any] = {
        "warnings": warnings,
        "api_status": api_status,
    }

    place_name = f"Grid Reference [{latitude:.4f}, {longitude:.4f}]"

    try:
        # --- USGS catalog (network) ---
        try:
            events, usgs_status, usgs_warnings = query_usgs_catalog(
                latitude=latitude,
                longitude=longitude,
                search_radius_km=search_radius_km,
                historical_years=historical_years,
                min_magnitude=minimum_magnitude,
            )
            warnings.extend(usgs_warnings)
            api_status["USGS_Catalog"] = usgs_status.get("status", "unknown")
            if api_status["USGS_Catalog"] != "success":
                warnings.append(
                    "Continuing hazard calculation without historical USGS events."
                )
        except Exception as e:
            logger.exception("USGS catalog call raised unexpectedly")
            events = []
            api_status["USGS_Catalog"] = "failure"
            warnings.append(
                f"USGS API query failed unexpectedly; continuing with empty catalog. ({e})"
            )

        partial["events"] = events

        # --- SoilGrids (network) ---
        try:
            soil_props = await fetch_soilgrids_data(latitude, longitude)
            source = str(soil_props.get("source", ""))
            if "API" in source and "Fallback" not in source:
                api_status["SoilGrids"] = "success"
            else:
                api_status["SoilGrids"] = "fallback"
                warnings.append(
                    f"SoilGrids API query failed or timed out. {source} utilized."
                )
        except Exception as e:
            logger.exception("Soil fetch raised unexpectedly")
            soil_props = get_fallback_soil_properties(latitude, longitude)
            api_status["SoilGrids"] = "fallback"
            warnings.append(
                f"SoilGrids failed unexpectedly; using regional fallback. ({e})"
            )

        partial["soil_props"] = soil_props

        try:
            soil_risk = evaluate_liquefaction_risk(soil_props)
        except Exception as e:
            logger.exception("Liquefaction evaluation failed")
            soil_risk = {
                "lsi_score": 0.2,
                "classification": "Moderate Liquefaction Risk",
                "color": "yellow",
                "soil_class": "Loam",
                "amplification_multiplier": 1.15,
                "assumptions": ["Fallback liquefaction profile after evaluation error."],
            }
            warnings.append(f"Liquefaction evaluation failed; defaults applied. ({e})")

        # --- Local / deterministic components ---
        fault_proximity, fault_warn = _safe_fault_proximity(latitude, longitude)
        if fault_warn:
            warnings.append(fault_warn)

        event_score, processed_events, score_warn = _safe_historical_score(
            events, minimum_magnitude
        )
        if score_warn:
            warnings.append(score_warn)
        partial["event_score"] = event_score
        partial["processed_events"] = processed_events

        try:
            fault_score = calculate_fault_score(fault_proximity["distance_km"])
            soil_score = calculate_soil_score(soil_risk["lsi_score"])
            overall_score, hazard_level, confidence = calibrate_hazard_score(
                event_score, fault_score, soil_score
            )
        except Exception as e:
            logger.exception("Calibration failed")
            return _build_degraded_report(
                latitude,
                longitude,
                search_radius_km,
                historical_years,
                minimum_magnitude,
                start_time,
                e,
                partial=partial,
            )

        # Reduce confidence when external APIs degraded.
        if api_status.get("USGS_Catalog") != "success":
            confidence = round(max(0.2, confidence - 0.2), 2)
        if api_status.get("SoilGrids") != "success":
            confidence = round(max(0.2, confidence - 0.1), 2)

        all_mags = [e.get("magnitude", 0.0) for e in events if e.get("magnitude") is not None]
        recurrence_data, rec_warn = _safe_recurrence(
            all_mags, historical_years, minimum_magnitude
        )
        if rec_warn:
            warnings.append(rec_warn)

        shakemap_data, shake_warn = _safe_shakemap(events, latitude, longitude)
        if shake_warn:
            warnings.append(shake_warn)

        catalog_stats, stats_warn = _safe_catalog_stats(
            events=events,
            historical_years=historical_years,
            nearest_fault_distance_km=fault_proximity["distance_km"],
            soil_classification=soil_risk["soil_class"],
            recurrence_m6_years=recurrence_data.get("recurrence_m6_years"),
        )
        if stats_warn:
            warnings.append(stats_warn)

        hist_level, hist_color = get_indicator_colors(event_score, 28.0)
        soil_level, soil_color = get_indicator_colors(soil_score, 12.0)

        zone_score = event_score * 0.6 + fault_score * 0.4
        zone_level, zone_color = get_indicator_colors(zone_score, 24.0)

        indicators = {
            "seismic_zone": {
                "value": f"Zone {zone_level}",
                "classification": f"{zone_level} regional seismic energy buildup",
                "color": zone_color,
            },
            "historical_activity": {
                "value": f"{len(events)} events analyzed",
                "classification": f"{hist_level} historical activity density",
                "color": hist_color,
            },
            "soil_liquefaction": {
                "value": soil_risk["soil_class"],
                "classification": soil_risk["classification"],
                "color": soil_color,
            },
            "fault_proximity": {
                "value": f"{fault_proximity['distance_km']} km",
                "classification": (
                    f"Proximity to {fault_proximity['fault_name']} "
                    f"({fault_proximity['classification']})"
                ),
                "color": fault_proximity["color"],
            },
        }

        summary_sentences = [
            (
                f"The geographic query location has a calibrated overall Seismic Hazard Score of "
                f"{overall_score}/100, resulting in a '{hazard_level}' classification."
            ),
            (
                f"Proximity risk is dominated by the {fault_proximity['fault_name']} fault system "
                f"located {fault_proximity['distance_km']} km away, representing a "
                f"'{fault_proximity['classification']}' rating."
            ),
            (
                f"Local surface soil texture consists of {soil_risk['soil_class']} with a loose "
                f"bulk density of {soil_props.get('bulk_density', 'n/a')} g/cm^3, causing a "
                f"'{soil_risk['classification']}' profile with a seismic wave amplification "
                f"factor of {soil_risk.get('amplification_multiplier', 'n/a')}x."
            ),
        ]
        if len(events) > 0:
            summary_sentences.append(
                f"Historical earthquake record shows {len(events)} analyzed events of "
                f"M{minimum_magnitude}+ within a {search_radius_km}km radius over the past "
                f"{historical_years} years. The largest event registered magnitude "
                f"M{catalog_stats['largest_historical_earthquake']} located "
                f"{catalog_stats['closest_earthquake_km']}km away."
            )
        else:
            if api_status.get("USGS_Catalog") != "success":
                summary_sentences.append(
                    f"Historical earthquake catalog was unavailable for this query; "
                    f"hazard score relies on fault proximity and soil conditions within "
                    f"{search_radius_km}km."
                )
            else:
                summary_sentences.append(
                    f"No historical earthquake events of magnitude M{minimum_magnitude}+ were "
                    f"found within {search_radius_km}km of coordinates in the past "
                    f"{historical_years} years, indicating a highly stable geological crust."
                )

        environmental_context = {
            "hazard_score": overall_score,
            "hazard_level": hazard_level,
            "historical_activity": {
                "classification": hist_level,
                "events_within_radius": len(events),
                "largest_magnitude": catalog_stats["largest_historical_earthquake"],
            },
            "faults": {
                "distance_km": fault_proximity["distance_km"],
                "classification": fault_proximity["classification"],
            },
            "soil": {
                "classification": soil_risk["classification"],
                "dominant_soil": soil_risk["soil_class"],
            },
            "ground_motion": {
                "estimated_mmi": shakemap_data["peak_mmi"],
                "estimated_pga_g": shakemap_data["peak_pga"],
                "confidence": confidence,
            },
            "summary": summary_sentences,
        }

        execution_time = time.time() - start_time

        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "place_name": place_name,
            },
            "hazard": {
                "overall_score": overall_score,
                "hazard_level": hazard_level,
                "confidence": confidence,
            },
            "indicators": indicators,
            "statistics": catalog_stats,
            "environmental_context": environmental_context,
            "events": processed_events,
            "metadata": {
                "warnings": warnings,
                "execution_time_seconds": round(execution_time, 4),
                "api_status": api_status,
                "model_version": "v1.1.2-deterministic",
                "degraded": bool(warnings),
            },
        }

    except Exception as e:
        logger.exception("Hazard engine unexpected failure; returning degraded report")
        return _build_degraded_report(
            latitude,
            longitude,
            search_radius_km,
            historical_years,
            minimum_magnitude,
            start_time,
            e,
            partial=partial,
        )


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
        minimum_magnitude=minimum_magnitude,
    )
    return HazardReport(**report_dict)
