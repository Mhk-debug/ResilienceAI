# Hazard Engine Documentation

> **Deterministic seismic hazard assessment using USGS catalogs, SoilGrids, fault databases, and physics-based scoring**

---

## Overview

The Hazard Engine computes a **Seismic Hazard Score (0–100)** for any latitude/longitude by combining:

1. **Historical Seismicity** — USGS earthquake catalog analysis
2. **Fault Proximity** — Distance to major fault systems
3. **Soil Conditions** — SoilGrids properties + liquefaction susceptibility
4. **Ground Motion** — ShakeMap integration for MMI/PGA estimation

All calculations are **deterministic** (no ML models) using physics-based formulas with calibrated constants.

---

## Input Parameters (`HazardInput`)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `latitude` | float | required | WGS84 latitude |
| `longitude` | float | required | WGS84 longitude |
| `search_radius_km` | float | 100.0 | Earthquake search radius |
| `historical_years` | float | 50.0 | Catalog time span |
| `minimum_magnitude` | float | 4.5 | Min magnitude to include |

---

## Component Modules

### 1. USGS Earthquake Catalog (`services/hazard_engine/usgs.py`)

**Function:** `query_usgs_catalog()`

```python
def query_usgs_catalog(latitude, longitude, search_radius_km, historical_years, min_magnitude):
    # Query USGS FDSNWS service
    # https://earthquake.usgs.gov/fdsnws/event/1/query
    
    params = {
        "format": "geojson",
        "latitude": latitude,
        "longitude": longitude,
        "maxradius": search_radius_km / 111.12,  # degrees
        "starttime": (now - historical_years).isoformat(),
        "minmagnitude": min_magnitude,
        "orderby": "time-asc"
    }
```

**Returns:** List of events with:
- `id`, `magnitude`, `distance_km`, `depth_km`, `date`, `place`, `max_mmi`

**Error Handling:**
- 6-second timeout
- Returns empty list + warnings on failure
- Graceful degradation: hazard engine continues with zero historical events

---

### 2. Soil Properties (`services/hazard_engine/soil.py`)

**Function:** `fetch_soilgrids_data()` → `evaluate_liquefaction_risk()`

**SoilGrids WCS Query:**
- 6 properties × 3 depths = 18 layers
- Properties: `clay`, `sand`, `silt`, `bdod` (bulk density), `cfvo` (coarse fragments), `soc` (organic carbon)
- Depths: `0-5cm`, `5-15cm`, `15-30cm`
- Parallel fetches via `ThreadPoolExecutor(max_workers=8)`

**Liquefaction Susceptibility Index (LSI):**
```python
sand_factor = min(1.0, max(0.0, (sand_pct - 30) / 45))
clay_factor = min(1.0, max(0.0, (30 - clay_pct) / 20))
density_factor = min(1.0, max(0.0, (1.6 - bulk_density) / 0.45))
coarse_factor = min(1.0, max(0.0, (25 - coarse_fragments_pct) / 20))

lsi = sand_factor * clay_factor * density_factor * coarse_factor
```

**LSI Classification:**
| LSI Range | Classification | Color | Amplification |
|-----------|----------------|-------|---------------|
| ≥ 0.55 | High Liquefaction Risk | Red | 1.45x |
| 0.25–0.55 | Moderate Liquefaction Risk | Yellow | 1.15x |
| < 0.25 | Low Liquefaction Risk | Green | 0.85x |

**Soil Texture Classification:** USDA triangle (Sand/Clay/Silt percentages)

**Fallback Soils:** If SoilGrids fails, deterministic regional heuristics:
- Delta regions (Bangladesh, Mississippi, Bangkok, etc.) → Loose alluvial
- Elsewhere → Regional loam

**Caching:** 24-hour in-memory cache keyed by rounded lat/lon (0.001°)

---

### 3. Fault Proximity (`services/hazard_engine/faults.py`)

**Function:** `find_nearest_fault()`

**Fault Database:** Hardcoded major fault polylines (10 systems):
- San Andreas, Alpine (NZ), Anatolian (Turkey), Himalayan MFT
- Japan Trench, Cascadia, Peru-Chile Trench, Mariana Trench
- Sumatra Sunda Megathrust, South Island Hope Fault (NZ)

**Distance Calculation:** Haversine to line segments (vertex-to-vertex)

**Classification Thresholds (`constants.py`):**
| Distance | Classification | Color |
|----------|----------------|-------|
| ≤ 10 km | Very High Proximity | Red |
| 10–30 km | High Proximity | Red |
| 30–75 km | Moderate Proximity | Yellow |
| > 75 km | Low Proximity | Green |
| > 150 km | "Unmapped Local Crustal Fault" | Green (background est.) |

---

### 4. Historical Hazard Scoring (`services/hazard_engine/scoring.py`)

**Function:** `calculate_historical_seismic_hazard()`

**Event Weighting (`weights.py`):**
```python
w_dist = exp(-distance_km / 50.0)      # DECAY_DISTANCE_KM
w_depth = exp(-depth_km / 35.0)        # DECAY_DEPTH_KM
w_mag = exp(1.2 * (magnitude - min_mag))  # MAGNITUDE_DAMAGE_COEFF
w_age = exp(-age_years / 15.0)         # DECAY_AGE_YEARS

contribution = w_dist * w_depth * w_mag * w_age
```

**Event Score:**
```
event_score = min(35.0, 13.0 * ln(1.0 + Σ contributions))
```

**Cap at 35** ensures historical component doesn't dominate.

---

### 5. Gutenberg-Richter Recurrence (`services/hazard_engine/recurrence.py`)

**Function:** `calculate_gutenberg_richter()`

```python
# b-value estimation (maximum likelihood)
b = log10(e) / (mean_mag - (min_mag - 0.05))
b = clamp(b, 0.5, 2.0)

# Annual rate
annual_rate = N_events / catalog_span_years

# M6 recurrence
a_annual = log10(annual_rate) + b * min_mag
m6_rate = 10^(a_annual - b * 6.0)
recurrence_m6_years = 1.0 / m6_rate
```

**Returns:** `a_value`, `b_value`, `recurrence_m6_years`

---

### 6. Calibration & Final Score (`services/hazard_engine/calibration.py`)

**Component Scores:**
| Component | Formula | Max |
|-----------|---------|-----|
| Event | `min(35, 13 * ln(1 + Σw))` | 35 |
| Fault | `26 * exp(-distance / 31)` | 26 |
| Soil | `14 * LSI` | 14 |

**Combined Score:**
```python
raw_combined = event_score + fault_score + soil_score + 2.5
final_score = 100 * (1 - exp(-raw_combined / 31.8))
final_score = clamp(final_score, 0, 100)
```

**Saturation Constant (31.8)** calibrated so typical max inputs → ~90-95.

**Hazard Levels:**
| Score | Level |
|-------|-------|
| 0–20 | Very Low |
| 20–40 | Low |
| 40–60 | Moderate |
| 60–80 | High |
| 80–100 | Very High |

**Confidence:**
- Base: 0.95
- -0.25 if event_score < 1.0 (sparse catalog)

---

### 7. ShakeMap Integration (`services/hazard_engine/shakemap.py`)

**Function:** `integrate_shakemap_data()`

Estimates peak MMI and PGA from nearby events:
- Uses event magnitudes/distances
- Empirical GMPE approximations
- Returns `peak_mmi`, `peak_pga`

---

### 8. Statistics (`services/hazard_engine/statistics.py`)

**Function:** `compute_catalog_statistics()`

Returns:
- `largest_historical_earthquake`
- `closest_earthquake_km`
- `average_depth_km`, `average_magnitude`, `median_magnitude`
- `events_analyzed`
- `catalog_span_years`
- `nearest_fault_distance_km`
- `estimated_recurrence_interval_years` (M6)
- `soil_classification`

---

## Scoring Formula Summary

```mermaid
flowchart TD
    USGS[USGS Events] --> EventScore[Event Score\nmax 35]
    Faults[Fault Distance] --> FaultScore[Fault Score\nmax 26]
    Soil[SoilGrids LSI] --> SoilScore[Soil Score\nmax 14]
    
    EventScore --> Combine[Raw Combined\n= Event + Fault + Soil + 2.5]
    FaultScore --> Combine
    SoilScore --> Combine
    
    Combine --> Calibrate[Calibrate\n100 * (1 - exp(-raw/31.8))]
    Calibrate --> Final[Final Score 0-100]
    Final --> Level[Hazard Level]
```

---

## Output: `HazardReport` + `EnvironmentalContext`

### HazardReport (Full Technical)

```json
{
  "location": { "latitude": 23.8103, "longitude": 90.4125, "place_name": "..." },
  "hazard": { "overall_score": 45.2, "hazard_level": "Moderate", "confidence": 0.95 },
  "indicators": {
    "seismic_zone": { "value": "Zone Moderate", "classification": "...", "color": "yellow" },
    "historical_activity": { "value": "12 events", "classification": "...", "color": "yellow" },
    "soil_liquefaction": { "value": "Silty Loam", "classification": "Moderate Liquefaction Risk", "color": "yellow" },
    "fault_proximity": { "value": "45.2 km", "classification": "...", "color": "yellow" }
  },
  "statistics": { "largest_historical_earthquake": 7.2, "closest_earthquake_km": 15.3, ... },
  "events": [ { "id": "...", "magnitude": 6.8, "distance_km": 15.3, "individual_contribution": 0.045, ... } ],
  "metadata": { "warnings": [], "execution_time_seconds": 3.42, "api_status": {...}, "model_version": "v1.1.2-deterministic" }
}
```

### EnvironmentalContext (LLM-Friendly)

```json
{
  "hazard_score": 45.2,
  "hazard_level": "Moderate",
  "historical_activity": { "classification": "Moderate", "events_within_radius": 12, "largest_magnitude": 7.2 },
  "faults": { "distance_km": 45.2, "classification": "Moderate Proximity" },
  "soil": { "classification": "Moderate Liquefaction Risk", "dominant_soil": "Silty Loam" },
  "ground_motion": { "estimated_mmi": 7.5, "estimated_pga_g": 0.18, "confidence": 0.95 },
  "summary": [
    "The geographic query location has a calibrated overall Seismic Hazard Score of 45.2/100...",
    "Proximity risk is dominated by the Himalayan Main Frontal Thrust fault system...",
    "Local surface soil texture consists of Silty Loam with a loose bulk density of 1.32 g/cm³...",
    "Historical earthquake record shows 12 analyzed events..."
  ]
}
```

---

## Constants (`hazard_engine/constants.py`)

```python
# Event weighting decay constants
DECAY_DISTANCE_KM = 50.0
DECAY_DEPTH_KM = 35.0
MAGNITUDE_DAMAGE_COEFF = 1.2
DECAY_AGE_YEARS = 15.0

# Fault proximity thresholds (km)
FAULT_VERY_HIGH_LIMIT = 10.0
FAULT_HIGH_LIMIT = 30.0
FAULT_MODERATE_LIMIT = 75.0
```

---

## API Endpoint

**`POST /api/hazard/calculate`** → Returns `HazardReport`

**`POST /api/assessment/process`** → Includes hazard in SSE pipeline

---

## API Failure Protection & Graceful Degradation

The hazard engine is designed to **never crash** due to external API failures. Every network-dependent component is wrapped with isolation, timeouts, and deterministic fallbacks.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    calculate_hazard()                           │
├─────────────────────────────────────────────────────────────────┤
│  USGS Catalog (network)     →  _safe_usgs()      →  [] + warn  │
│  SoilGrids (network)        →  _safe_soil()      →  fallback   │
│  Fault Proximity (local)    →  _safe_fault()     →  120km est. │
│  Historical Scoring (local) →  _safe_score()     →  0.0        │
│  Recurrence (local)         →  _safe_recurrence()→  null       │
│  ShakeMap (local)           →  _safe_shakemap()  →  0.0 PGA    │
│  Statistics (local)         →  _safe_stats()     →  null       │
├─────────────────────────────────────────────────────────────────┤
│  Calibration                →  try/except → _build_degraded()  │
│  Top-level catch-all        →  except → _build_degraded()      │
└─────────────────────────────────────────────────────────────────┘
```

### Per-Component Timeouts & Fallbacks

| Component | Timeout | Failure Mode | Fallback Behavior |
|-----------|---------|--------------|-------------------|
| **USGS Catalog** | 6.0 s | timeout / HTTP error / JSON decode | Empty event list, `api_status: "timeout"`, warning added |
| **SoilGrids** | 12.0 s overall, 5.0 s per layer | timeout / WCS error / < 3 layers | Deterministic regional heuristic (e.g., "Irrawaddy Delta / Yangon"), `api_status: "fallback"` |
| **Fault Proximity** | N/A (local) | Exception | `"Unmapped Local Crustal Fault"` at 120 km, Green |
| **Historical Scoring** | N/A (local) | Exception | Event score = 0.0, empty processed events |
| **Gutenberg-Richter** | N/A (local) | Exception | `a_value: null, b_value: null, recurrence_m6_years: null` |
| **ShakeMap** | N/A (local) | Exception | `peak_pga: 0.0, peak_mmi: 1.0` |
| **Catalog Statistics** | N/A (local) | Exception | All nulls, only `events_analyzed` and `catalog_span_years` filled |

### Degraded Mode Report (`_build_degraded_report()`)

When any unexpected exception occurs, or calibration fails, the engine returns a **complete valid report** using only local/deterministic inputs:

- **Hazard score** computed from: fault proximity + soil fallback + event_score (0.0)
- **Confidence** reduced by **0.35** (minimum 0.20)
- **`metadata.degraded: true`**
- **`metadata.api_status.engine: "degraded"`**
- **Warnings** include the root cause
- **Summary sentences** explicitly state degraded mode

### Confidence Penalties

| Condition | Penalty | Floor |
|-----------|---------|-------|
| USGS Catalog ≠ "success" | −0.20 | 0.20 |
| SoilGrids ≠ "success" | −0.10 | 0.20 |
| Full degraded mode | −0.35 | 0.20 |

### API Status Codes

The `metadata.api_status` object tracks every external dependency:

```json
{
  "USGS_Catalog": "success" | "timeout" | "failure" | "unavailable",
  "SoilGrids": "success" | "fallback" | "failure",
  "engine": "normal" | "degraded"
}
```

### SoilGrids Regional Fallbacks

Deterministic profiles for known soft-soil basins:

| Region | Coordinates | Soil Class | Bulk Density | LSI Risk |
|--------|-------------|------------|--------------|----------|
| Irrawaddy Delta / Yangon | 15.5–17.8°N, 95.5–97.0°E | Clay Loam | 1.20 | Moderate |
| Mississippi Delta / New Orleans | 29.0–31.0°N, 91.0–89.0°W | Loamy Sand | 1.15 | Moderate |
| Ganges Delta / Bangladesh | 21.0–24.0°N, 88.0–91.0°E | Loamy Sand | 1.15 | Moderate |
| Tokyo Bay | 35.2–35.8°N, 139.5–140.2°E | Sandy Clay Loam | 1.25 | Moderate |
| San Francisco Bay | 37.4–38.0°N, 122.5–122.1°W | Clay Loam | 1.18 | Moderate |
| Bangkok / Chao Phraya | 13.5–14.1°N, 100.2–100.8°E | Clay | 1.15 | High |
| **Default (elsewhere)** | — | Loam | 1.42 | Low |

Fallback source string format: `"Deterministic Coastal/Alluvial Heuristic (Fallback) — {Region Name}"`

### Testing Failure Scenarios

```bash
# Unit tests mock external failures
pytest tests/test_hazard.py::test_engine_survives_api_failures -v
pytest tests/test_hazard.py::test_engine_survives_unexpected_exception -v

# Manual offline test
python -c "
import asyncio
from unittest.mock import patch
from services.hazard_engine import engine as eng_mod

async def test():
    with patch.object(eng_mod, 'query_usgs_catalog', 
                      lambda *a, **k: ([], {'status': 'timeout'}, ['USGS timeout'])):
        with patch.object(eng_mod, 'fetch_soilgrids_data',
                          lambda lat, lon: eng_mod.get_fallback_soil_properties(lat, lon)):
            r = await eng_mod.calculate_hazard(16.84, 96.17)
            print(f'Score: {r[\"hazard\"][\"overall_score\"]}')
            print(f'API Status: {r[\"metadata\"][\"api_status\"]}')
            print(f'Warnings: {r[\"metadata\"][\"warnings\"]}')

asyncio.run(test())
"
```

### Behavior Guarantees

1. **No unhandled exceptions** — every code path returns a dict matching `HazardReport` schema
2. **Always valid JSON** — Pydantic `HazardReport(**report_dict)` never fails
3. **Deterministic fallbacks** — same lat/lon always produces same degraded output
4. **Informative metadata** — `warnings`, `api_status`, `degraded` flag explain what happened
5. **Confidence reflects data quality** — consumers can trust `confidence` field
6. **Assessment pipeline never blocks** — `/api/assessment/process` SSE always completes

---

## Testing

```bash
# Unit tests
pytest tests/test_hazard.py -v

# Integration test (requires network)
python scripts/validate_pipeline.py
# Scenario: "RC Engineered - Dhaka"
# Hazard Score: 45.2, Level: Moderate, Fault: 45.2km, Soil: Silty Loam
```

---

## Limitations & Assumptions

| Aspect | Assumption | Limitation |
|--------|------------|------------|
| Fault Database | 10 major faults hardcoded | Misses local/unknown faults |
| SoilGrids | 250m resolution, top 30cm | May not reflect site-specific conditions |
| Liquefaction | Simplified LSI, assumes saturation | No groundwater depth, no SPT/CPT data |
| GMPE | Empirical approximations | Not region-calibrated |
| Catalog | USGS completeness > M4.5 | Misses smaller events, pre-instrumental |
| Recurrence | Stationary Poisson process | No time-dependent effects |
| Combination | Additive in raw space | Interactions not modeled |

---

## Extending the Hazard Engine

**Add New Fault:**
```python
# In faults.py
MAJOR_FAULTS["New Fault Name"] = [
    [lat1, lon1], [lat2, lon2], ...
]
```

**Adjust Weights:**
Modify `constants.py` decay constants and recalibrate.

**Add Soil Parameter:**
Extend `properties_names` in `soil.py` and update `_convert_to_features()`.

**New Hazard Component:**
1. Add scoring function in `calibration.py`
2. Add to `raw_combined` sum
3. Recalibrate saturation constant (31.8)