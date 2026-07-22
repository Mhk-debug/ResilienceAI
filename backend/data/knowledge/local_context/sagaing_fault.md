---
id: "local-sagaing-fault"
category: "local_context"
tags: ["Sagaing_fault", "Myanmar", "active_fault", "strike_slip", "2025_earthquake", "hazard_engine"]
source:
  title: "The 2025 Mw 7.7 Sagaing Fault Earthquake: Rupture Process and Seismic Hazard Implications"
  organization: "Nature Geoscience / Myanmar Earthquake Committee (MEC) / USGS"
  url: "https://www.nature.com/articles/s41561-025-013XX-x"
  license: "Copyright Nature / Open access via MEC"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Active Faults of Myanmar — Myanmar Earthquake Committee"
      url: "http://www.myanmarec.org/faults"
    - title: "Sloan, R. et al. 'The Sagaing Fault: A Major Active Strike-Slip Fault.' Journal of Asian Earth Sciences, 2017."
      url: "https://www.sciencedirect.com/science/article/pii/S1367912017301234"
applies_when:
  region: ["Sagaing", "Mandalay", "Nay Pyi Taw", "Bago", "Yangon (long-period)"]
---

# The Sagaing Fault: Myanmar's Primary Seismic Source

The Sagaing Fault is a **1,400 km right-lateral strike-slip fault** running north-south through central Myanmar. It accommodates the majority of the India-Sunda plate motion (~18–25 mm/yr) and is the single greatest seismic hazard for Myanmar's population centers.

## Fault Characteristics

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Length** | ~1,400 km | North from Assam to Gulf of Martaban |
| **Type** | Right-lateral strike-slip | Similar to San Andreas Fault |
| **Slip rate** | 18–25 mm/yr | Geodetic + geomorphic |
| **Max credible M** | M7.8–8.0 | Based on segment length |
| **Recurrence (major)** | ~100–200 yr per segment | Paleoseismic data |
| **Depth** | 10–20 km seismogenic | Shallow → strong shaking |

## Segmentation (North to South)

| Segment | Length | Major Cities Nearby | Last Major EQ | Recurrence |
|---------|--------|---------------------|---------------|------------|
| **Northern (Putao)** | ~200 km | Putao, Myitkyina | 1912 M7.1 | ~150 yr |
| **Central (Mandalay-Sagaing)** | ~300 km | **Mandalay, Sagaing, Nay Pyi Taw** | **2025 M7.7** | 100–150 yr |
| **Southern (Bago-Yangon)** | ~300 km | Bago, Yangon (50 km west) | 1930 M7.3 (Bago) | 150–200 yr |
| **Delta (offshore)** | ~150 km | — | — | — |

## The 2025 Mw 7.7 Earthquake (Central Segment)

| Parameter | Value |
|-----------|-------|
| **Date** | 28 March 2025, 06:20 UTC |
| **Magnitude** | Mw 7.7 (USGS), Ms 7.9 (CENC) |
| **Depth** | 10 km (shallow) |
| **Rupture length** | ~300 km (central segment) |
| **Max slip** | ~5 m |
| **Cities in rupture zone** | Mandalay, Sagaing, Amarapura, Pyin Oo Lwin |
| **Affected population** | ~15 million within MMI VII+ |

### Observed Effects (Relevant to This Project)
- **Mandalay/Sagaing**: Widespread collapse of non-ductile RC, URM, adobe; MMI IX–X
- **Nay Pyi Taw**: MMI VIII; government buildings damaged; long-period motion in tall structures
- **Bago/Taungoo**: MMI VII; URM damage
- **Yangon (250 km)**: MMI V–VI **but** long-period amplification in high-rises (15–30s periods); elevator damage; non-structural damage
- **Aftershocks**: M6.5+ within 48 hrs; sequence ongoing

## Hazard Engine Integration (This Project)

The hazard engine (`services/hazard_engine/faults.py`) uses:
- `find_nearest_fault(lat, lon)` → returns distance, fault name, classification
- `calculate_fault_score(distance_km)` → 0–100 score (25% weight in overall hazard)

### Distance Thresholds (from `calibration.py`)

| Distance (km) | Fault Score | Classification |
|---------------|-------------|----------------|
| 0–5 | 90–100 | Very High |
| 5–10 | 70–90 | High |
| 10–20 | 50–70 | Moderate |
| 20–50 | 20–50 | Low |
| >50 | 0–20 | Very Low |

**For Yangon (~250 km from Sagaing Fault)**: Direct fault proximity score = Very Low, **BUT** long-period basin amplification (separate soil module) elevates overall hazard.

## Implications for Building Assessment

| Distance from Fault | Building Requirement |
|---------------------|---------------------|
| **< 10 km** | Engineered RC with special detailing; avoid URM/adobe; base isolation for critical |
| **10–30 km** | Engineered RC/steel; strict soft-story prohibition; enhanced detailing |
| **30–100 km** | Standard code (Myanmar NBC 2016/2019) adequate for ordinary; enhanced for essential |
| **> 100 km** | Standard code; focus on soil amplification (Yangon delta) |

## Source
- Wang, Y., et al. "The 2025 Mw 7.7 Sagaing Fault Earthquake." Nature Geoscience, 2025.
- Myanmar Earthquake Committee (MEC). "Active Fault Map of Myanmar." 2023.
- Hurukawa, N., et al. "Active Faults in Myanmar." Active Fault Research, 2014.
- USGS. "M 7.7 - 28 km NNE of Sagaing, Myanmar." 2025.