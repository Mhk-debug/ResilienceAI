---
id: "env-soil-amplification"
category: "environmental_hazards"
tags: ["soil", "amplification", "site_effects", "shear_wave_velocity", "Vs30", "NEHRP"]
source:
  title: "NEHRP Recommended Seismic Provisions (FEMA P-1050) / USGS National Seismic Hazard Model"
  organization: "FEMA / USGS / BSSC"
  url: "https://www.fema.gov/emergency-managers/risk-management/earthquake/nehrp"
  license: "Public domain (US Government)"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Building Seismic Safety Council (BSSC) — Site Classification"
      url: "https://www.nibs.org/bssc"
    - title: "Boore, J., et al. 'Site Amplification Factors for NGA Models.' PEER Report 2013/05."
      url: "https://peer.berkeley.edu/"

---

# Soil Amplification and Site Effects

Local soil conditions can amplify ground motion by **2–10x** compared to rock, making site classification a critical component of seismic hazard assessment.

## NEHRP / Vs30 Site Classification

| Class | Description | Vs30 (m/s) | Amplification Factor (Typical) |
|-------|-------------|------------|-------------------------------|
| **A** | Hard rock | >1,500 | 1.0 (reference) |
| **B** | Rock | 760–1,500 | 1.0–1.2 |
| **C** | Very dense soil / soft rock | 360–760 | 1.2–1.7 |
| **D** | Stiff soil | 180–360 | 1.5–2.5 |
| **E** | Soft clay soil | <180 | 2.0–5.0+ |
| **F** | Special soils (liquefiable, peat, thick soft clay) | — | Site-specific required |

**Vs30** = Average shear-wave velocity in top 30 meters

## Amplification Mechanisms

### 1. **Impedance Contrast**
Seismic waves slow down and amplify when passing from stiff material (rock) to soft material (soil).
```
Amplification ≈ √(ρ₁V₁ / ρ₂V₂)  (for normal incidence)
```
Where ρ = density, V = shear velocity. Typical rock-to-soil contrast: 5–10x impedance ratio → 2–3x motion amplification.

### 2. **Resonance**
Soil column has natural period: `Tₛ = 4H / Vs`
- H = soil depth
- Vs = average shear velocity
If `Tₛ` matches dominant period of incoming motion → resonance → **5–10x amplification** at that period.

### 3. **Basin Effects**
Deep sedimentary basins trap and amplify surface waves (e.g., Los Angeles, Mexico City, Yangon). Long-duration shaking, long-period amplification.

## Hazard Engine Implementation (This Project)

The hazard engine (`services/hazard_engine/soil.py`) uses **SoilGrids 250m** data to estimate:
- **Soil class** (A–E via Vs30 proxy)
- **Liquefaction Susceptibility Index (LSI)**
- **Amplification multiplier** applied to bedrock PGA/MMI

```python
# Simplified logic from soil.py
soil_class = classify_vs30(vs30_estimate)
amp_factor = AMPLIFICATION_FACTORS[soil_class]  # e.g., 2.3 for Class E
pga_surface = pga_bedrock * amp_factor
```

## Amplification Factors Used (Default)

| Soil Class | PGA Amp | MMI Amp | Period Range of Peak Amp |
|------------|---------|---------|-------------------------|
| A (Rock) | 1.0 | 0 | N/A |
| B | 1.1 | +0.1 | — |
| C | 1.3 | +0.3 | 0.2–0.5s |
| D | 1.8 | +0.6 | 0.4–1.0s |
| E (Soft clay) | 2.5 | +1.0 | 0.6–2.0s |

## Liquefaction Susceptibility

| Soil Type | Liquefaction Potential | LSI Range |
|-----------|----------------------|-----------|
| Clean sand, low fines | Very High | >15 |
| Silty sand | High | 10–15 |
| Sandy silt | Moderate | 5–10 |
| Clayey silt / clay | Low / None | <5 |

**Trigger**: PGA > 0.1g + saturated sandy soil + shallow groundwater (<10m)

## Myanmar Context: Yangon Soft Soils

- **Yangon** sits on **deep alluvial deposits** (Irrawaddy delta) — Class D/E soils common
- **Vs30 estimates**: 150–250 m/s in central Yangon
- **Amplification**: 2–3x bedrock motion typical
- **Liquefaction**: Documented in 1930 Bago (M7.3) and 2025 Sagaing (M7.7) earthquakes
- **Basin effect**: Irrawaddy basin traps long-period energy → long-duration shaking for tall buildings

## Source
- FEMA P-1050-1 (2020) — NEHRP Recommended Seismic Provisions, Chapter 11: Site Effects
- USGS National Seismic Hazard Model (2023) — Site amplification methodology
- Boore, J., et al. "Site Amplification Factors for NGA Models." PEER Report 2013/05.
- Borcherdt, R.D. "Estimates of Site-Dependent Response Spectra for Design." USGS OFR 94-526, 1994.
- **Myanmar-specific**: UN-Habitat Myanmar. "Myanmar National Urban Profile — Yangon." 2018.
- Maung, T., et al. "Seismic Hazard Assessment for Yangon City." J. Earthquake Eng., 2017.