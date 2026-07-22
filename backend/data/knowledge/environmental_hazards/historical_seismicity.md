---
id: "env-historical-seismicity"
category: "environmental_hazards"
tags: ["historical", "seismicity", "earthquake_catalog", "Gutenberg_Richter", "recurrence", "USGS", "Myanmar"]
source:
  title: "USGS Earthquake Catalog and Seismicity Analysis Methods"
  organization: "USGS"
  url: "https://earthquake.usgs.gov/earthquakes/search/"
  license: "Public domain (US Government)"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Kagan, Y.Y. 'Statistical Distributions of Earthquake Numbers: Consequences of the Branching Process.' GJI, 2010."
    - title: "Woessner, J., et al. 'The 2013 European Seismic Hazard Model (ESHM13).' ETH Zurich, 2015."

---

# Historical Seismicity and Recurrence Analysis

Historical earthquake records are the foundation of probabilistic seismic hazard analysis (PSHA). This document explains how the hazard engine uses historical data.

## Catalog Requirements

| Requirement | This Project | Standard Practice |
|-------------|--------------|-------------------|
| **Minimum magnitude** | M4.5 | M4.0–M5.0 |
| **Time span** | 50 years (configurable) | 50–100+ years |
| **Completeness** | M4.5+ for 50 yr | Varies by region |
| **Declustering** | Not applied (simple model) | Required for PSHA |

## USGS Catalog Query (from `usgs.py`)

```python
query_usgs_catalog(
    latitude, longitude,
    search_radius_km=100,
    historical_years=50,
    min_magnitude=4.5
)
```

Returns: events list with magnitude, distance, depth, date, place.

## Gutenberg-Richter Relationship

The fundamental recurrence law:
```
log₁₀(N) = a - b·M
```
Where:
- N = annual number of events ≥ magnitude M
- a = activity rate (seismicity level)
- b = b-value (relative frequency of small vs large events)

**Typical b-values**:
- Global average: b ≈ 1.0
- Subduction zones: b ≈ 0.8–1.2
- Continental interiors: b ≈ 0.9–1.1
- Myanmar (Sagaing Fault): b ≈ 0.95 (Wang et al., 2025)

## Recurrence Calculation (from `recurrence.py`)

The hazard engine computes:

```python
def calculate_gutenberg_richter(magnitudes, years, min_mag):
    # Maximum likelihood b-value
    b = log10(e) / (mean(mag) - min_mag)
    a = log10(N_total / years) + b * min_mag
    
    # Recurrence for target magnitude
    recurrence_yr = 10^(a - b * M_target)
```

**Example outputs** (for Myanmar region):
| Target M | Recurrence (years) | Annual Probability |
|----------|-------------------|-------------------|
| M5.0 | ~2–5 | 20–50% |
| M6.0 | ~15–30 | 3–7% |
| M7.0 | ~100–300 | 0.3–1% |
| M7.5 | ~300–1000 | 0.1–0.3% |

## Hazard Engine Integration

From `engine.py`:
```python
recurrence_data = calculate_gutenberg_richter(all_mags, historical_years, min_magnitude)
# Returns: b_value, a_value, recurrence_m6_years, recurrence_m7_years
```

Used in `summary_sentences`:
> "Local Gutenberg-Richter b-value is calculated at 0.95, indicating a statistical M6.0+ recurrence interval of approximately 22 years."

## Limitations of Simple Approach

| Limitation | Impact | Better Alternative |
|------------|--------|-------------------|
| No declustering | Overcounts aftershocks → inflated rate | Reasenberg or ZMAP declustering |
| Fixed min magnitude | Misses small-event info for b-value | Use variable completeness |
| Uniform spatial | Treats all directions equal | Smoothing kernels (KDE) |
| No fault-specific | Mixes fault/background | Fault-based PSHA |

**For this competition**: The simple approach is acceptable as a screening tool. The hazard engine explicitly notes limitations in metadata:
```json
"metadata": {
  "warnings": ["Catalog declustering not applied; rates may be inflated"],
  "model_version": "v1.1.2-deterministic"
}
```

## Myanmar Catalog Characteristics

| Period | Catalog | Completeness |
|--------|---------|--------------|
| Pre-1900 | Historical accounts (pagoda damage, chronicles) | M7+ only |
| 1900–1960 | Regional networks (Calcutta, Rangoon) | M6+ |
| 1960–2000 | Global networks (ISC, NEIC) | M5+ |
| 2000–present | USGS, GFZ, local Myanmar networks | M4.5+ |

**Key Myanmar sequences** in catalog:
- 1839 Ava (M7.8) — Kabaw Fault
- 1930 Bago (M7.3) — Kyaukkyan Fault
- 1946 Sagaing (M7.0) — Sagaing Fault
- 1956 Sagaing (M7.0) — Sagaing Fault
- 1991 Kachin (M6.8) — Sagaing Fault northern
- 2012 Thabeikkyin (M6.8) — Sagaing Fault
- 2025 Sagaing (M7.7) — Central Sagaing Fault

## Source
- USGS Earthquake Catalog (ComCat) — Primary data source for hazard engine
- ISC Bulletin — Supplementary for pre-2000 events
- **Myanmar**: Hurukawa, N., et al. "Seismicity and Seismic Hazard in Myanmar." J. Seismol., 2014.
- Wang, Y., et al. "The 2025 Mw 7.7 Sagaing Fault Earthquake." Nature Geoscience, 2025.