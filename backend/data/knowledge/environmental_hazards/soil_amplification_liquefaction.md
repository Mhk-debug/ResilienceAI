---
id: "env-soil-amplification-liquefaction"
category: "environmental_hazards"
tags: ["soil", "liquefaction", "amplification", "site_effects", "hazard_engine"]
source:
  title: "USGS Ground Motion and Soil Amplification Guidelines"
  organization: "US Geological Survey (USGS)"
  url: "https://earthquake.usgs.gov/hazards/soil/"
  license: "Public domain (US Government)"
  retrieved: "2026-07-20"
  supplementary:
    - title: "FEMA P-750 NEHRP Provisions — Site Classification"
      url: "https://www.fema.gov/emergency-managers/risk-management/earthquake/nehrp"
    - title: "Idriss & Boulanger (2008) — Soil Liquefaction During Earthquakes"
      organization: "Earthquake Engineering Research Institute (EERI)"

applies_when:
  soil_classes: ["D", "E", "F", "liquefiable"]
---

# Soil Amplification and Liquefaction in Earthquakes

Soil conditions dramatically modify ground motion. The same earthquake can produce 2-5x different shaking intensity depending on local soil.

## Site Classification (NEHRP / FEMA P-750 / VS30)

| Class | Description | VS30 (m/s) | Amplification Factor |
|-------|-------------|------------|---------------------|
| **A** | Hard rock | >1500 | 1.0 (reference) |
| **B** | Rock | 760–1500 | 1.1–1.3 |
| **C** | Very dense soil / soft rock | 360–760 | 1.3–1.6 |
| **D** | Stiff soil | 180–360 | 1.6–2.4 |
| **E** | Soft clay soil | <180 | 2.0–3.5+ |
| **F** | Special soils (peat, thick soft clay, liquefiable) | — | Site-specific analysis required |

## Amplification Mechanism

```
Bedrock motion (input)
        ↓
Soil column resonance (f = Vs/4H for fundamental mode)
        ↓
Surface motion = Bedrock × Amplification(frequency)
```

- **Soft soils amplify long-period motions** (affecting tall/flexible buildings)
- **Stiff soils amplify short-period motions** (affecting short/stiff buildings)
- **Resonance** occurs when building period ≈ soil column period

## Liquefaction

### What It Is
Saturated, loose, granular soils (sands, silts) lose strength during cyclic loading. Pore water pressure builds up until effective stress → 0. Soil behaves like a heavy liquid.

### Required Conditions (All Must Be Present)
1. **Saturated** — Below groundwater table
2. **Loose to medium dense** — SPT N₁₆₀ < 15 (sands), < 10 (silts)
3. **Cyclic loading** — Earthquake magnitude ≥ M5.5, duration ≥ 10 sec
4. **Susceptible grain size** — Clean sands, low-plasticity silts (PI < 10)

### Consequences
| Effect | Description |
|--------|-------------|
| **Flow failure** | Entire soil mass moves laterally (gentle slopes) |
| **Lateral spread** | Blocks of soil move on liquefied layer |
| **Bearing capacity loss** | Foundations sink/tilt (settlements 0.3–3m observed) |
| **Sand boils** | Water + sand ejected at surface |
| **Buoyancy** | Buried structures (tanks, pipes) float up |

## Richter Dataset / Hazard Engine Mapping

The hazard engine (`services/hazard_engine/soil.py`) returns:
- `soil_class` — NEHRP class (A–F
- `lsi_score` — Liquefaction Severity Index
- `classification` — "Low"/"Moderate"/"High"/"Very High"
- `amplification_multiplier` — Ground motion amplification factor

## Liquefaction Susceptibility by Region (Myanmar Context)

| Region | Soil Type | Liquefaction Risk |
|--------|-----------|-------------------|
| **Yangon** | Thick alluvial deposits (Ayeyarwady delta) | **Very High** — soft clays, high water table |
| **Mandalay** | Alluvial fans, river terraces | **High** — sandy layers, variable GW |
| **Ayeyarwady Delta** | Young marine/fluvial deposits | **Very High** — saturation at shallow depth |
| **Shan Plateau** | Residual soils, weathered rock | **Low to Moderate** |

## Mitigation

| Approach | Effectiveness | Cost |
|----------|---------------|------|
| **Ground improvement** (stone columns, compaction grouting) | High | High |
| **Deep foundations** (piles to bearing layer) | High | High |
| **Drainage** (gravel drains, wick drains) | Moderate | Moderate |
| **Lightweight structures** (reduce demand) | Moderate | Low |
| **Avoidance** (don't build there) | 100% | N/A |

## Source
- USGS National Seismic Hazard Model — Site Amplification
- FEMA P-750 NEHRP Recommended Seismic Provisions (2020) — Chapter 11 Site Effects
- Idriss, I.M., Boulanger, R.W. "Soil Liquefaction During Earthquakes." EERI MNO-12, 2008.
- Seed, R.B., et al. "Recent Advances in Soil Liquefaction Engineering." 5th ICLEE, 2013.