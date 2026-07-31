# \"\"\"
# tests/test_hazard.py

# Comprehensive test suite verifying key components of the Earthquake Hazard Engine:
# - Distance / Haversine math
# - Independent weights (magnitude, distance, depth, age)
# - Calibration & normalization ranges
# - Fallback soil classifiers
# \"\"\"

import pytest
import math
from services.hazard_engine.utils import haversine_distance, distance_to_line_segment
from services.hazard_engine.weights import (
    compute_distance_weight,
    compute_depth_weight,
    compute_magnitude_weight,
    compute_age_weight
)
from services.hazard_engine.soil import classify_soil_texture, evaluate_liquefaction_risk
from services.hazard_engine.calibration import calibrate_hazard_score, classify_hazard_level


def test_haversine_distance():
    # \"\"\"
    # Verifies Haversine distance calculations against known standards.
    # \"\"\"
    # Distance between San Francisco and Oakland is approx 13-15 km
    sf = (37.7749, -122.4194)
    oak = (37.8044, -122.2711)
    dist = haversine_distance(sf[0], sf[1], oak[0], oak[1])
    assert 12.0 < dist < 16.0

    # Distance to identical point must be zero
    assert haversine_distance(37.0, -122.0, 37.0, -122.0) == 0.0


def test_distance_to_line_segment():
    # \"\"\"
    # Verifies closest point projections to line segments representing faults.
    # \"\"\"
    # Segment running straight along longitude -120 from lat 35 to 36
    # Query point at lat 35.5, lon -120.1 (approx 9 km west)
    dist = distance_to_line_segment(35.5, -120.1, 35.0, -120.0, 36.0, -120.0)
    assert 8.0 < dist < 11.0


def test_independent_weights():
    # \"\"\"
    # Verifies that seismic parameters scale correctly according to physical expectations.
    # \"\"\"
    # 1. Distance weight: closer events should have heavier weights
    w_close = compute_distance_weight(10.0)
    w_far = compute_distance_weight(100.0)
    assert w_close > w_far
    assert 0.0 < w_close <= 1.0

    # 2. Depth weight: shallow events should be heavier than deep mantle events
    w_shallow = compute_depth_weight(5.0)
    w_deep = compute_depth_weight(150.0)
    assert w_shallow > w_deep
    assert w_deep < 0.1

    # 3. Magnitude weight: larger magnitude must scale exponentially
    w_m5 = compute_magnitude_weight(5.0, min_magnitude=4.0)
    w_m7 = compute_magnitude_weight(7.0, min_magnitude=4.0)
    assert w_m7 > w_m5 * 10.0  # Exp damage potential scaling should grow rapidly

    # 4. Age weight: older events must decay relative to recent ones
    w_recent = compute_age_weight(1.0)
    w_old = compute_age_weight(50.0)
    assert w_recent > w_old


def test_soil_texture_and_liquefaction():
    # \"\"\"
    # Verifies the soil texture classifier and engineering liquefaction logic.
    # \"\"\"
    # Soil with 90% sand should be classified as Sand or Loamy Sand
    classification = classify_soil_texture(90.0, 5.0, 5.0)
    assert "Sand" in classification

    # High sand, low clay, low bulk density should flag high liquefaction risk
    soft_sands = {
        "sand_pct": 80.0,
        "clay_pct": 5.0,
        "silt_pct": 15.0,
        "bulk_density": 1.2,
        "coarse_fragments_pct": 2.0,
        "organic_carbon_pct": 0.5,
        "soil_class": "Sand"
    }
    risk = evaluate_liquefaction_risk(soft_sands)
    assert "High" in risk["classification"]
    assert risk["color"] == "red"


def test_calibration_bounds():
    # """
    # Verifies calibrated overall score boundaries and level mappings.
    # """
    # Empty seismicity, far fault, rigid soil -> Very Low risk (minimum ~7.6 due to base hazard constant)
    score, level, conf = calibrate_hazard_score(0.0, 0.0, 0.0)
    assert 7.0 < score < 8.5  # Minimum score due to base constant in calibration formula
    assert level == "Very Low"

    # Extreme inputs: high seismicity, active fault intersect, loose sand
    # Final overall score must be continuous and bounded strictly by [0, 100]
    score_extreme, level_extreme, conf_extreme = calibrate_hazard_score(45.0, 28.0, 18.0)
    assert 0.0 < score_extreme <= 100.0
    assert level_extreme == "Very High"


def test_hazard_levels():
    # \"\"\"
    # Validates boundary conditions for score classifications.
    # \"\"\"
    assert classify_hazard_level(15.0) == "Very Low"
    assert classify_hazard_level(30.0) == "Low"
    assert classify_hazard_level(50.0) == "Moderate"
    assert classify_hazard_level(70.0) == "High"
    assert classify_hazard_level(95.0) == "Very High"


def test_soil_fallback_yangon_region():
    """Yangon soft-soil fallback must be used when SoilGrids is unavailable."""
    from services.hazard_engine.soil import get_fallback_soil_properties

    props = get_fallback_soil_properties(16.8661, 96.1951)  # Yangon
    assert "Fallback" in props["source"]
    assert "Yangon" in props["source"] or "Irrawaddy" in props["source"]
    assert props["bulk_density"] < 1.35


def test_usgs_failure_returns_empty_catalog(monkeypatch):
    """USGS network failures must degrade to empty events, not raise."""
    import urllib.request
    from services.hazard_engine.usgs import query_usgs_catalog

    def _boom(*_args, **_kwargs):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)

    events, status, warnings = query_usgs_catalog(16.8, 96.1)
    assert events == []
    assert status["status"] in {"timeout", "failure"}
    assert warnings


@pytest.mark.asyncio
async def test_engine_survives_api_failures(monkeypatch):
    """
    Full hazard pipeline must return a valid report when both external APIs fail.
    """
    from services.hazard_engine import engine as engine_mod
    from services.hazard_engine.soil import get_fallback_soil_properties

    def _usgs_fail(*_args, **_kwargs):
        return [], {"status": "timeout"}, ["USGS API query timed out."]

    async def _soil_fail(lat, lon):
        return get_fallback_soil_properties(lat, lon)

    monkeypatch.setattr(engine_mod, "query_usgs_catalog", _usgs_fail)
    monkeypatch.setattr(engine_mod, "fetch_soilgrids_data", _soil_fail)

    report = await engine_mod.calculate_hazard(16.8661, 96.1951)

    assert "hazard" in report
    assert 0.0 <= report["hazard"]["overall_score"] <= 100.0
    assert report["hazard"]["hazard_level"] in {
        "Very Low", "Low", "Moderate", "High", "Very High"
    }
    assert report["metadata"]["api_status"]["USGS_Catalog"] == "timeout"
    assert report["metadata"]["api_status"]["SoilGrids"] == "fallback"
    assert report["metadata"]["warnings"]
    assert report["environmental_context"]["summary"]
    # Confidence should be reduced when APIs degrade
    assert report["hazard"]["confidence"] < 0.95


@pytest.mark.asyncio
async def test_engine_survives_unexpected_exception(monkeypatch):
    """Outer safety net must return a degraded report instead of raising."""
    from services.hazard_engine import engine as engine_mod

    def _explode(*_args, **_kwargs):
        raise RuntimeError("catastrophic unexpected failure")

    monkeypatch.setattr(engine_mod, "query_usgs_catalog", _explode)

    # Even if USGS raises (should be caught), and if something else blows up,
    # calculate_hazard must still return a dict report.
    report = await engine_mod.calculate_hazard(37.77, -122.42)

    assert isinstance(report, dict)
    assert "hazard" in report
    assert "overall_score" in report["hazard"]
    assert "metadata" in report
    assert report["metadata"].get("warnings")
