---
id: "local-myanmar-building-code"
category: "local_context"
tags: ["Myanmar_NBC", "building_code", "seismic_design", "regulation", "compliance", "hazard_engine"]
source:
  title: "Myanmar National Building Code (2016, 2019) — Seismic Provisions"
  organization: "Ministry of Construction (MOC), Myanmar / Myanmar Engineering Council (MEC)"
  url: "https://www.moc.gov.mm/"
  license: "Government of Myanmar"
  retrieved: "2026-07-20"
  supplementary:
    - title: "Myanmar National Building Code 2016 (Part 6: Seismic Design)"
      url: "https://www.moc.gov.mm/sites/default/files/MNBC_2016_Part6.pdf"
    - title: "Myanmar National Building Code 2019 Update"
      url: "https://www.moc.gov.mm/sites/default/files/MNBC_2019_Update.pdf"
    - title: "JICA. 'Review of Myanmar National Building Code.' 2020."
      url: "https://www.jica.go.jp/myanmar/english/activities/activity_03.html"
applies_when:
  region: ["Myanmar"]
---

# Myanmar National Building Code (NBC) — Seismic Provisions

The Myanmar National Building Code (MNBC) is the primary regulatory framework for seismic design in Myanmar. The 2016 edition (updated 2019) is the current legal standard, though enforcement varies.

## Code Structure (Seismic-Relevant Parts)

| Part | Title | Seismic Relevance |
|------|-------|-------------------|
| **Part 1** | General Requirements | Scope, definitions, load combinations |
| **Part 3** | Design Loads | Dead, live, wind, **seismic** (Ch. 3.4) |
| **Part 6** | **Seismic Design** | **Core seismic provisions** |
| **Part 7** | Concrete Structures | Ductile detailing (Ch. 7.5) |
| **Part 8** | Steel Structures | Seismic detailing (Ch. 8.4) |
| **Part 9** | Masonry Structures | URM, confined masonry (Ch. 9.3) |
| **Part 10** | Timber/Bamboo | Traditional construction (Ch. 10.2) |

## Seismic Design Philosophy (Part 6)

| Concept | MNBC Approach |
|---------|---------------|
| **Design basis** | Force-based (equivalent lateral force) |
| **Performance objective** | Life Safety for design basis earthquake (DBE) |
| **DBE return period** | 475 years (10% in 50 years) |
| **MCE return period** | 2,475 years (2% in 50 years) — for essential facilities |
| **Importance factors** | I = 1.0 (ordinary), 1.25 (essential), 1.5 (critical) |

## Seismic Zoning Map (MNBC 2016)

| Zone | Zone Factor (Z) | Regions |
|------|----------------|---------|
| **Zone 1 (Low)** | 0.10 | Southern Shan, parts of Tanintharyi |
| **Zone 2 (Moderate)** | 0.16 | Ayeyarwady, Bago (west), Yangon (north) |
| **Zone 3 (High)** | 0.24 | **Sagaing, Mandalay, Nay Pyi Taw, Bago (east), Kachin** |
| **Zone 4 (Very High)** | 0.36 | **Sagaing Fault corridor (central Myanmar)** |

**Yangon**: Zone 2 (Z=0.16) **but** soil amplification raises effective hazard significantly.

## Site Classification (MNBC Table 6.2 / NEHRP)

| Class | Description | Vs30 (m/s) | Amplification Factor (Fa, Fv) |
|-------|-------------|------------|-------------------------------|
| **A** | Hard rock | >1,500 | Fa=0.8, Fv=0.8 |
| **B** | Rock | 760–1,500 | Fa=1.0, Fv=1.0 |
| **C** | Very dense soil/soft rock | 360–760 | Fa=1.2, Fv=1.6 |
| **D** | Stiff soil | 180–360 | Fa=1.6, Fv=2.4 |
| **E** | **Soft clay soil** | **<180** | **Fa=2.5, Fv=3.5** |
| **F** | Special study required | — | Site-specific |

**Yangon downtown = Class E** → Requires site-specific study for buildings >3 stories or essential facilities.

## Design Base Shear (Equivalent Lateral Force)

```
V = (Z * I * C * W) / R
```
Where:
- Z = Zone factor (0.10–0.36)
- I = Importance factor (1.0, 1.25, 1.5)
- C = Seismic coefficient (function of period, soil, zone)
- W = Seismic weight
- R = Response modification factor (ductility)

| System Type | R (MNBC) | Typical Use |
|-------------|----------|-------------|
| **Special RC Moment Frame** | 8 | High-rise, essential |
| **Intermediate RC Moment Frame** | 5 | Mid-rise |
| **Ordinary RC Moment Frame** | 3 | Low-rise (pre-2016) |
| **Special Steel Moment Frame** | 8 | High-rise |
| **RC Shear Wall** | 6 | Mid/high-rise |
| **URM Bearing Wall** | 1.5–2 | Existing only; not for new |

## Key Ductile Detailing Requirements (Part 6, 7, 8)

### RC Moment Frames (Special)
| Requirement | MNBC 2016/2019 |
|-------------|----------------|
| **Column confinement** | Hoops @ d/4 spacing in plastic hinge zone (2h from joint) |
| **Hoop spacing** | ≤ d/4 and ≤ 100mm; 135° hooks + 10d extension |
| **Beam longitudinal steel** | Top & bottom continuous through joint |
| **Beam-column joint** | Joint shear check per §6.7; transverse reinforcement |
| **Strong column/weak beam** | ΣMcol ≥ 1.2 ΣMbeam at joint |

### Masonry (Confined)
| Requirement | MNBC 2016 |
|-------------|-----------|
| **Confining elements** | RC tie columns + beams at wall intersections |
| **Tie column spacing** | ≤ 3m (10 ft) |
| **Tie beam spacing** | ≤ 3m vertically |
| **Wall reinforcement** | Horizontal @ 400mm; vertical @ 600mm |

### Existing Building Evaluation (MNBC Appendix / ASCE 41)
| Tier | Method | Use Case |
|------|--------|----------|
| **Tier 1** | Checklists | Rapid screening |
| **Tier 2** | Simplified analysis (linear) | Deficiency identification |
| **Tier 3** | Detailed analysis (nonlinear) | Final retrofit design |

## Enforcement Reality (2026 Context)

| Aspect | Status |
|--------|--------|
| **Legal mandate** | MNBC 2016 gazetted; 2019 update issued |
| **Permit process** | YCDC/MCDC require structural drawings + calculations |
| **Plan review** | Often cursory; focus on architectural, not structural |
| **Inspection** | Rare during construction; final inspection only |
| **Existing buildings** | No mandatory retrofit ordinance (as of 2026) |
| **Professional liability** | Engineer of record signs; limited post-construction accountability |

**Competition context**: The AI Innovation Competition judges will expect you to reference MNBC. Cite specific sections (e.g., "MNBC Part 6 §6.5.2") when making regulatory recommendations.

## Source
- Ministry of Construction, Myanmar. "Myanmar National Building Code 2016 (Part 6: Seismic Design)." 2016.
- Ministry of Construction, Myanmar. "Myanmar National Building Code 2019 Update." 2019.
- Myanmar Engineering Council (MEC). "Guidelines for Seismic Design per MNBC." 2020.
- JICA. "Technical Cooperation Project for Review of Myanmar National Building Code." 2020.
- UN-Habitat Myanmar. "Building Regulatory Capacity Assessment: Myanmar." 2018.