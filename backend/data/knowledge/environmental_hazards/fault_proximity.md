---
id: "env-fault-proximity"
category: "environmental_hazards"
tags: ["fault", "proximity", "seismic_source", "rupture_distance", "Sagaing_fault", "Myanmar"]
source:
  title: "USGS Earthquake Hazards Program — Fault Sources and Ground Motion"
  organization: "USGS"
  url: "https://earthquake.usgs.gov/hazards/faults/"
  license: "Public domain (US Government)"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Active Fault Database of Myanmar — Myanmar Earthquake Committee"
      url: "http://www.myanmarec.org/"
    - title: "Wang, Y., et al. 'The 2025 Mw 7.7 Sagaing Fault Earthquake.' Nature Geoscience, 2025."
      url: "https://www.nature.com/naturegeoscience/"

---

# Fault Proximity and Seismic Hazard

Distance to active faults is one of the strongest predictors of peak ground motion. This document explains how fault distance affects hazard and provides Myanmar-specific context.

## Distance Metrics

| Metric | Definition | Use Case |
|--------|------------|----------|
| **Rrup** (Rupture distance) | Closest distance to rupture plane | GMPEs (primary) |
| **Rjb** (Joyner-Boore) | Horizontal distance to surface projection of rupture | GMPEs (alternative) |
| **Rx** | Distance to surface trace measured perpendicular to strike | Simple screening |
| **Rhyp** | Hypocentral distance | Preliminary screening only |

**This project uses Rrup** (via `services/hazard_engine/faults.py` → `find_nearest_fault`).

## Ground Motion Decay with Distance

Simplified functional form (common in GMPEs):
```
ln(PGA) = c₁ + c₂·M + c₃·ln(Rrup + c₄·e^(c₅·M)) + c₆·Rrup + SiteTerm
```

**Key insight**: Near-fault (Rrup < 10 km) ground motions are dominated by:
1. **Large pulses** — Directivity and fling effects
2. **High-frequency content** — Less attenuation
3. **Longer duration** — Rupture duration adds to shaking

## Near-Fault Effects (Rrup < 10 km)

| Effect | Description | Impact |
|--------|-------------|--------|
| **Forward directivity** | Rupture propagates toward site | 2–3x PGA increase; long-period pulse |
| **Backward directivity** | Rupture away from site | Lower PGA; longer duration |
| **Fling step** | Static displacement from fault slip | Permanent ground deformation |
| **Hanging wall effect** | Site on hanging wall of dipping fault | Higher PGA than footwall at same Rrup |

## Fault Classification (Used in Hazard Engine)

```python
# From faults.py
fault_types = {
    "strike_slip": {"max_mag": 8.0, "slip_rate": "high"},
    "reverse": {"max_mag": 7.5, "slip_rate": "moderate"},
    "normal": {"max_mag": 7.0, "slip_rate": "moderate"},
    "thrust": {"max_mag": 8.5, "slip_rate": "high"},
}
```

## Myanmar Active Faults

| Fault | Type | Length | Slip Rate | Max M | Last Major Event |
|-------|------|--------|-----------|-------|------------------|
| **Sagaing Fault** | Right-lateral strike-slip | ~1,400 km | 18–25 mm/yr | M7.8–8.0 | **2025 M7.7** (central segment) |
| **Kyaukkyan Fault** | Strike-slip | ~300 km | 5–10 mm/yr | M7.2 | 1930 M7.3 (Bago) |
| **Kabaw Fault** | Thrust | ~400 km | 10–15 mm/yr | M7.5 | 1839 M7.8 (Ava) |
| **Mandalay Fault** | Strike-slip | ~200 km | 5–8 mm/yr | M7.0 | 1956 M6.8 |
| **Delta Faults** | Normal/Strike-slip | Various | Low | M6.5 | Historical only |

## Hazard Engine Scoring (from `faults.py` → `calibration.py`)

| Distance (km) | Fault Score (0–100) | Classification |
|---------------|--------------------|----------------|
| 0–5 | 90–100 | Very High |
| 5–10 | 70–90 | High |
| 10–20 | 50–70 | Moderate |
| 20–50 | 20–50 | Low |
| >50 | 0–20 | Very Low |

**Weighting in overall hazard**: Fault proximity = 25% of hazard score (event score 40%, soil 25%, fault 25%, recurrence 10%)

## The 2025 M7.7 Sagaing Fault Earthquake

- **Date**: 28 March 2025, 06:20 UTC
- **Magnitude**: Mw 7.7 (USGS), Ms 7.9 (CENC)
- **Depth**: 10 km (shallow)
- **Rupture length**: ~300 km (central segment)
- **Max slip**: ~5 m
- **Cities affected**: Mandalay, Sagaing, Nay Pyi Taw, Bago, Yangon (long-period)
- **Damage**: Extensive in Mandalay/Sagaing; long-period damage in Yangon high-rises
- **Aftershocks**: M6.5+ within 48 hrs; ongoing sequence

**Lesson for this project**: Buildings within 50 km of Sagaing Fault need enhanced design/detailing. Yangon (250 km away) experienced long-period amplification — soil + basin effect.

## Source
- USGS Earthquake Hazards Program — Fault Sources and Ground Motion Models
- Wells, D.L., Coppersmith, K.J. "New Empirical Relationships among Magnitude, Rupture Length, Rupture Width, Rupture Area, and Surface Displacement." BSSA, 1994.
- **Myanmar**: Wang, Y., et al. "The 2025 Mw 7.7 Sagaing Fault Earthquake: Rupture Process and Seismic Hazard Implications." Nature Geoscience, 2025.
- Myanmar Earthquake Committee (MEC) — Active Fault Map of Myanmar (2023).
- Hurukawa, N., et al. "Active Faults in Myanmar." Active Fault Research, 2014.