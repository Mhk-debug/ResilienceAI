---
id: "local-yangon-soft-soil"
category: "local_context"
tags: ["Yangon", "soft_soil", "alluvial", "liquefaction", "basin_effect", "amplification", "hazard_engine"]
source:
  title: "Seismic Hazard Assessment for Yangon City — UN-Habitat Myanmar / MEC / JICA"
  organization: "UN-Habitat Myanmar / Myanmar Earthquake Committee / JICA"
  url: "https://unhabitat.org/myanmar"
  license: "UN publication / Government of Myanmar"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Maung, T. et al. 'Seismic Hazard Assessment for Yangon City.' J. Earthquake Eng., 2017."
      url: "https://doi.org/10.1080/13632469.2017.1324567"
    - title: "Myanmar National Building Code (2016, 2019) — Site Classification"
      url: "https://www.moc.gov.mm/"
applies_when:
  region: ["Yangon", "Ayeyarwady Delta", "Bago", "Thanlyin", "Syriam"]
---

# Yangon Soft Soil and Basin Amplification

Yangon sits on the **Irrawaddy (Ayeyarwady) Delta** — a thick sequence of young alluvial sediments overlying bedrock. This geology creates severe site amplification and liquefaction risk, making soil effects the dominant hazard factor for Yangon (more than direct fault proximity).

## Geology

| Layer | Depth | Description | Vs30 (m/s) |
|-------|-------|-------------|------------|
| **Topsoil / Fill** | 0–3 m | Silt, clay, anthropogenic fill | 100–180 |
| **Young Alluvium** | 3–30 m | Soft clay, silty clay, organic layers | 150–250 |
| **Old Alluvium** | 30–100+ m | Stiff clay, dense sand, gravel lenses | 250–400 |
| **Bedrock** | 100–500+ m | Tertiary sandstone/shale | >800 |

**Typical Vs30 in central Yangon**: 150–250 m/s → **NEHRP Class E (Soft Clay)**

## Amplification Effects

### 1. **PGA Amplification**
| Soil Class | Bedrock PGA | Surface PGA | Factor |
|------------|-------------|-------------|--------|
| Rock (A/B) | 0.20g | 0.20–0.24g | 1.0–1.2 |
| Class C | 0.20g | 0.26–0.34g | 1.3–1.7 |
| Class D | 0.20g | 0.36–0.50g | 1.8–2.5 |
| **Class E (Yangon)** | **0.20g** | **0.50–1.00g** | **2.5–5.0** |

### 2. **Period-Dependent Amplification**
- **Short period (0.1–0.3s)**: 2–3x (affects low-rise, stiff buildings)
- **Mid period (0.5–1.5s)**: **4–6x** (affects 5–15 story buildings — resonance with typical RC frame periods)
- **Long period (2–5s)**: 3–4x (affects tall buildings 20+ stories)

### 3. **Basin Effect (Irrawaddy Delta)**
- Deep sedimentary basin traps surface waves
- **Duration**: 2–3x longer than rock sites
- **Late-arriving surface waves** cause cumulative damage to tall buildings

## Liquefaction Susceptibility

| Area | Susceptibility | Evidence |
|------|----------------|----------|
| **Downtown (Sule, Pabedan)** | Very High | 1930 Bago EQ: sand boils, building tilting |
| **Riverfront (Strand Rd, Botataung)** | Very High | Saturated sand at 5–10m depth |
| **New Townships (Hlaing Tharyar, Shwepyitha)** | High | Rapid development on soft fill |
| **Airport (Mingaladon)** | Moderate | Older alluvium, deeper water table |

## Hazard Engine Integration (This Project)

The hazard engine (`services/hazard_engine/soil.py`) uses **SoilGrids 250m** to estimate:
- `soil_class` (A–E) → NEHRP class
- `vs30_estimate` (m/s)
- `liquefaction_susceptibility` (LSI score)
- `amplification_multiplier` applied to bedrock PGA/MMI

### For Yangon Coordinates (typical):
```json
{
  "soil_class": "E",
  "vs30_estimate": 180,
  "liquefaction_susceptibility": "High",
  "amplification_multiplier": 3.2,
  "soil_risk_classification": "Very High"
}
```

### Impact on Overall Hazard Score
| Component | Weight | Typical Yangon Value |
|-----------|--------|---------------------|
| Event score (historical) | 40% | Moderate (distant Sagaing events) |
| **Soil score** | **25%** | **Very High (80–100)** |
| Fault proximity | 25% | Low (250 km to Sagaing) |
| Recurrence | 10% | Moderate |
| **Overall** | | **Moderate–High** |

**Key insight**: Yangon's hazard is **soil-dominated**, not fault-dominated. A building that would be "Low Risk" on rock becomes "High Risk" on Yangon soft clay.

## Building Implications for Yangon

| Building Type | Risk on Yangon Soil | Mitigation Priority |
|---------------|---------------------|---------------------|
| **Pre-1995 RC (non-ductile)** | **Extreme** | Immediate evaluation; retrofit or replace |
| **URM / Adobe** | **Extreme** | Not recommended for occupancy |
| **Engineered RC (post-2016 NBC)** | Moderate | Verify soil-structure interaction design |
| **Steel moment frame** | Low–Moderate | Verify connection ductility |
| **Base-isolated** | Very Low | Recommended for critical facilities |

## Myanmar National Building Code (NBC) 2016/2019 Provisions

| Provision | Requirement for Yangon (Class E) |
|-----------|----------------------------------|
| **Site Class** | E (Vs30 < 180 m/s) — requires site-specific study for >3 stories |
| **Seismic Zone** | Zone 3 (Sagaing Fault influence) + Local amplification |
| **Importance Factor** | 1.5 for essential facilities on Class E |
| **Site-Specific Response** | **Required** for: >3 stories, essential facilities, irregular structures |
| **Liquefaction Analysis** | Required for Class E sites with GW < 10m |

## 2025 M7.7 Sagaing EQ Observations in Yangon

- **MMI V–VI** (moderate shaking) but **long duration** (>60 sec strong motion)
- **High-rise damage**: Non-structural (partitions, ceilings, facades); elevator rope damage; some structural cracking in pre-2000 buildings
- **Resonance**: 8–20 story buildings experienced peak response (period match)
- **Liquefaction**: Minor sand boils in reclaimed areas (Dala, Thilawa)

## Source
- UN-Habitat Myanmar. "Seismic Hazard Assessment for Yangon City." 2018.
- Maung, T., et al. "Seismic Hazard Assessment for Yangon City." Journal of Earthquake Engineering, 2017.
- Myanmar National Building Code (2016, 2019) — Part 6: Seismic Design.
- JICA. "The Study on Earthquake Disaster Risk Management for Yangon City." 2014.
- MEC. "Yangon Seismic Microzonation Study." 2022.