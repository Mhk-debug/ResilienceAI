/**
 * TypeScript Implementation of the Modular Earthquake Hazard Engine
 * Mirrors the exact physical models, weights, calibrations, and fallbacks of the Python codebase.
 */

import {
  HazardReport,
  HazardInput,
  ProcessedEvent,
  HazardStatistics,
  Indicators
} from "../src/types";

// --- Scientific Parameters & Constants ---
const DECAY_DISTANCE_KM = 50.0;
const DECAY_DEPTH_KM = 35.0;
const MAGNITUDE_DAMAGE_COEFF = 1.2;
const DECAY_AGE_YEARS = 15.0;

const FAULT_VERY_HIGH_LIMIT = 10.0;
const FAULT_HIGH_LIMIT = 30.0;
const FAULT_MODERATE_LIMIT = 75.0;

const MAJOR_FAULTS: Record<string, [number, number][]> = {
  "San Andreas Fault System": [
    [32.5, -115.5], [33.5, -116.5], [34.5, -118.0], [35.5, -119.5],
    [37.0, -121.8], [38.0, -122.8], [40.0, -124.3]
  ],
  "Alpine Fault (New Zealand)": [
    [-46.0, 166.5], [-45.0, 168.0], [-44.0, 169.5], [-43.0, 171.0], [-41.8, 172.5]
  ],
  "Anatolian Fault (Turkey)": [
    [40.5, 26.5], [40.7, 30.0], [40.8, 33.0], [40.9, 36.5], [39.8, 40.0], [39.5, 42.0]
  ],
  "Himalayan Main Frontal Thrust": [
    [27.0, 88.0], [27.5, 85.0], [28.5, 82.0], [29.5, 79.0], [31.0, 77.0], [33.0, 74.0]
  ],
  "Japan Trench (Subduction Zone)": [
    [34.0, 141.5], [36.0, 142.5], [38.0, 143.0], [40.0, 143.5], [42.0, 144.0]
  ],
  "Cascadia Subduction Zone (Pacific NW)": [
    [40.5, -124.5], [42.0, -125.0], [44.0, -125.2], [46.0, -125.0],
    [48.0, -125.5], [50.0, -127.0]
  ],
  "Peru-Chile Trench (Andean Subduction)": [
    [-40.0, -74.5], [-35.0, -73.0], [-30.0, -72.0], [-25.0, -71.0],
    [-20.0, -71.5], [-15.0, -76.0], [-10.0, -79.0], [-5.0, -81.5], [0.0, -81.0]
  ],
  "Mariana Subduction Trench": [
    [11.0, 142.0], [13.0, 144.0], [15.0, 146.0], [18.0, 147.0], [20.0, 147.5]
  ],
  "Sumatra Subduction Zone (Sunda Megathrust)": [
    [-6.5, 103.0], [-5.0, 101.5], [-3.0, 99.5], [-1.0, 97.5], [1.5, 96.0], [4.0, 94.0]
  ],
  "South Island Hope Fault (NZ)": [
    [-42.8, 171.8], [-42.5, 172.5], [-42.3, 173.2], [-42.1, 173.9]
  ],
};

// --- Helper Utilities ---

export function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371.0088;
  const phi1 = (lat1 * Math.PI) / 180.0;
  const phi2 = (lat2 * Math.PI) / 180.0;
  const dPhi = ((lat2 - lat1) * Math.PI) / 180.0;
  const dLambda = ((lon2 - lon1) * Math.PI) / 180.0;

  let a = Math.sin(dPhi / 2.0) ** 2 +
          Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2.0) ** 2;
  a = Math.min(1.0, Math.max(0.0, a));

  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a));
  return R * c;
}

function distanceToLineSegment(
  lat: number, lon: number,
  lat_start: number, lon_start: number,
  lat_end: number, lon_end: number
): number {
  const d_start = haversineDistance(lat, lon, lat_start, lon_start);
  const d_end = haversineDistance(lat, lon, lat_end, lon_end);
  const d_segment = haversineDistance(lat_start, lon_start, lat_end, lon_end);

  if (d_segment < 0.001) return d_start;

  const avg_lat = (lat + lat_start + lat_end) / 3.0 * Math.PI / 180.0;
  const cos_lat = Math.cos(avg_lat);

  const x = (lon - lon_start) * 111.13 * cos_lat;
  const y = (lat - lat_start) * 111.13;

  const x2 = (lon_end - lon_start) * 111.13 * cos_lat;
  const y2 = (lat_end - lat_start) * 111.13;

  const segment_len_sq = x2 * x2 + y2 * y2;
  if (segment_len_sq < 0.001) return d_start;

  let t = (x * x2 + y * y2) / segment_len_sq;
  t = Math.min(1.0, Math.max(0.0, t));

  const closest_lat = lat_start + t * (lat_end - lat_start);
  const closest_lon = lon_start + t * (lon_end - lon_start);

  return haversineDistance(lat, lon, closest_lat, closest_lon);
}

function calculateAgeYears(dateStr: string): number {
  try {
    const dt = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - dt.getTime();
    return Math.max(0.0, diffMs / (1000.0 * 60.0 * 60.0 * 24.0 * 365.25));
  } catch {
    return 5.0;
  }
}

// --- Fault Distance Matching ---

function findNearestFault(lat: number, lon: number) {
  let closestFaultName = "Unknown Regional Active Fault";
  let minDistance = 9999.0;

  for (const [faultName, vertices] of Object.entries(MAJOR_FAULTS)) {
    if (!vertices || vertices.length === 0) continue;

    if (vertices.length === 1) {
      const dist = haversineDistance(lat, lon, vertices[0][0], vertices[0][1]);
      if (dist < minDistance) {
        minDistance = dist;
        closestFaultName = faultName;
      }
      continue;
    }

    for (let i = 0; i < vertices.length - 1; i++) {
      const start = vertices[i];
      const end = vertices[i + 1];

      const dist = distanceToLineSegment(lat, lon, start[0], start[1], end[0], end[1]);
      if (dist < minDistance) {
        minDistance = dist;
        closestFaultName = faultName;
      }
    }
  }

  let classification = "Low Proximity";
  let color: "green" | "yellow" | "red" = "green";

  if (minDistance <= FAULT_VERY_HIGH_LIMIT) {
    classification = "Very High Proximity";
    color = "red";
  } else if (minDistance <= FAULT_HIGH_LIMIT) {
    classification = "High Proximity";
    color = "red";
  } else if (minDistance <= FAULT_MODERATE_LIMIT) {
    classification = "Moderate Proximity";
    color = "yellow";
  }

  if (minDistance > 150.0) {
    const backgroundEst = Math.min(minDistance, 120.0);
    return {
      fault_name: "Unmapped Local Crustal Fault",
      distance_km: backgroundEst,
      classification: "Low Proximity",
      color: "green" as const
    };
  }

  return {
    fault_name: closestFaultName,
    distance_km: parseFloat(minDistance.toFixed(2)),
    classification,
    color
  };
}

// --- Soil Grids Mocking and API Query fallback ---

async function fetchSoilGrids(lat: number, lon: number) {
  const url = `https://rest.isric.org/soilgrids/v2.0/properties/query?lon=${lon}&lat=${lat}&property=clay&property=sand&property=silt&property=bdod&property=cfvo&property=ocd&value=mean`;
  
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 4000); // 4 second timeout
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(id);

    if (res.ok) {
      const data = await res.json();
      return parseSoilgrids(data);
    }
  } catch (e) {
    console.warn("SoilGrids API query failed, using deterministic local geological fallback.", e);
  }

  return getFallbackSoil(lat, lon);
}

function parseSoilgrids(data: any) {
  const rawProps: Record<string, number> = {};

  try {
    const layers = data?.properties?.layers || [];
    for (const layer of layers) {
      const name = layer.name;
      const depths = layer.depths || [];
      const values: number[] = [];

      for (const d of depths) {
        if (["0-5cm", "5-15cm", "15-30cm"].includes(d.label)) {
          const meanVal = d.values?.mean;
          if (meanVal != null) {
            values.push(meanVal);
          }
        }
      }

      if (values.length > 0) {
        rawProps[name] = values.reduce((a, b) => a + b, 0) / values.length;
      }
    }
  } catch (e) {
    console.error("Error parsing soilgrids response:", e);
  }

  let sand = (rawProps["sand"] ?? 400.0) / 10.0;
  let clay = (rawProps["clay"] ?? 250.0) / 10.0;
  let silt = (rawProps["silt"] ?? 350.0) / 10.0;
  const bd = (rawProps["bdod"] ?? 1350.0) / 1000.0;
  const cf = (rawProps["cfvo"] ?? 100.0) / 10.0;
  const oc = (rawProps["ocd"] ?? 150.0) / 1000.0;

  const sum = sand + clay + silt;
  if (sum > 0) {
    sand = (sand / sum) * 100;
    clay = (clay / sum) * 100;
    silt = (silt / sum) * 100;
  }

  return {
    sand_pct: sand,
    clay_pct: clay,
    silt_pct: silt,
    bulk_density: bd,
    coarse_fragments_pct: cf,
    organic_carbon_pct: oc,
    source: "SoilGrids API"
  };
}

function getFallbackSoil(lat: number, lon: number) {
  // Bounding boxes matching Python fallback model
  const isBayArea = lat >= 37.4 && lat <= 38.0 && lon >= -122.5 && lon <= -122.1;
  const isTokyo = lat >= 35.2 && lat <= 35.8 && lon >= 139.5 && lon <= 140.2;
  const isGanges = lat >= 21.0 && lat <= 24.0 && lon >= 88.0 && lon <= 91.0;
  const isNewOrleans = lat >= 29.0 && lat <= 31.0 && lon >= -91.0 && lon <= -89.0;

  if (isBayArea || isTokyo || isGanges || isNewOrleans) {
    return {
      sand_pct: 72.0,
      clay_pct: 8.0,
      silt_pct: 20.0,
      bulk_density: 1.15,
      coarse_fragments_pct: 2.0,
      organic_carbon_pct: 2.5,
      source: "Deterministic Coastal/Alluvial Heuristic (Fallback)"
    };
  }

  return {
    sand_pct: 42.0,
    clay_pct: 24.0,
    silt_pct: 34.0,
    bulk_density: 1.42,
    coarse_fragments_pct: 12.0,
    organic_carbon_pct: 1.1,
    source: "Deterministic Regional Loam (Fallback)"
  };
}

function classifySoilTexture(sand: number, clay: number, silt: number): string {
  if (sand >= 85.0) return "Sand";
  if (sand >= 70.0 && clay <= 15.0) return "Loamy Sand";
  if (clay >= 40.0) return "Clay";
  if (clay >= 35.0 && sand >= 45.0) return "Sandy Clay";
  if (clay >= 27.0 && silt >= 28.0) return "Clay Loam";
  if (silt >= 80.0) return "Silt";
  if (silt >= 50.0) return "Silt Loam";
  return "Loam";
}

function evaluateLiquefaction(soilProps: any) {
  const sand = soilProps.sand_pct;
  const clay = soilProps.clay_pct;
  const density = soilProps.bulk_density;
  const coarse = soilProps.coarse_fragments_pct;

  const sandFactor = Math.min(1.0, Math.max(0.0, (sand - 30.0) / 45.0));
  const clayFactor = Math.min(1.0, Math.max(0.0, (30.0 - clay) / 20.0));
  const densityFactor = Math.min(1.0, Math.max(0.0, (1.6 - density) / 0.45));
  const coarseFactor = Math.min(1.0, Math.max(0.0, (25.0 - coarse) / 20.0));

  const lsi = sandFactor * clayFactor * densityFactor * coarseFactor;

  let risk = "Low";
  let color: "green" | "yellow" | "red" = "green";
  let amp = 0.85;

  if (lsi >= 0.55) {
    risk = "High";
    color = "red";
    amp = 1.45;
  } else if (lsi >= 0.25) {
    risk = "Moderate";
    color = "yellow";
    amp = 1.15;
  }

  const soilClass = classifySoilTexture(sand, clay, soilProps.silt_pct);

  return {
    lsi_score: lsi,
    classification: `${risk} Liquefaction Risk`,
    color,
    soil_class: soilClass,
    amplification_multiplier: amp,
    assumptions: [
      "Inferred purely from shallow soil texture fractions (0-30cm) and bulk density.",
      "Assumes fully saturated water table conditions (typical conservative engineering baseline).",
      "Does not account for local piling, artificial fill, or engineered structural foundations."
    ]
  };
}

// --- Weighting formulas ---

function computeDistanceWeight(d: number) {
  return Math.exp(-Math.max(0.0, d) / DECAY_DISTANCE_KM);
}

function computeDepthWeight(z: number) {
  return Math.exp(-Math.max(0.0, z) / DECAY_DEPTH_KM);
}

function computeMagnitudeWeight(m: number, minM: number) {
  if (m < minM) return 0.0;
  return Math.exp(MAGNITUDE_DAMAGE_COEFF * (m - minM));
}

function computeAgeWeight(t: number) {
  return Math.exp(-Math.max(0.0, t) / DECAY_AGE_YEARS);
}

// --- Gutenberg-Richter Recurrence Relation ---

function calculateGutenbergRichter(magnitudes: number[], catalogSpanYears: number, minMagnitude: number) {
  const valid = magnitudes.filter(m => m >= minMagnitude);
  if (valid.length < 3) {
    return { a_value: null, b_value: null, recurrence_m6_years: null };
  }

  const avgM = valid.reduce((a, b) => a + b, 0) / valid.length;
  const binCorrection = 0.05;
  const bDenom = avgM - (minMagnitude - binCorrection);

  let bValue = 1.0;
  if (bDenom > 0) {
    bValue = Math.log10(Math.E) / bDenom;
  }
  bValue = Math.max(0.5, Math.min(2.0, bValue));

  const annualRate = valid.length / Math.max(0.1, catalogSpanYears);
  const aValueAnnual = Math.log10(annualRate) + bValue * minMagnitude;

  const m6Rate = Math.pow(10, aValueAnnual - bValue * 6.0);
  const recurrenceM6 = m6Rate > 0 ? 1.0 / m6Rate : null;

  return {
    a_value: aValueAnnual + Math.log10(Math.max(1.0, catalogSpanYears)),
    b_value: bValue,
    recurrence_m6_years: recurrenceM6
  };
}

// --- Point-Source Attenuation (ShakeMap Proxy) ---

function estimatePgaG(mag: number, dist: number, depth: number) {
  const c0 = -3.5;
  const c1 = 0.85;
  const c2 = 1.15;
  const c3 = 0.0035;
  const h = 8.5;

  const R = Math.sqrt(dist * dist + depth * depth + h * h);
  const lnPga = c0 + c1 * mag - c2 * Math.log(R) - c3 * R;
  return Math.exp(lnPga);
}

function pgaToMmi(pgaG: number): number {
  if (pgaG <= 0.0017) return 1.0;
  if (pgaG <= 0.014) return 1.0 + 1.5 * (Math.log10(pgaG) - Math.log10(0.0017)) / (Math.log10(0.014) - Math.log10(0.0017));
  if (pgaG <= 0.039) return 3.0 + 1.0 * (Math.log10(pgaG) - Math.log10(0.014)) / (Math.log10(0.039) - Math.log10(0.014));
  if (pgaG <= 0.092) return 4.0 + 1.0 * (Math.log10(pgaG) - Math.log10(0.039)) / (Math.log10(0.092) - Math.log10(0.039));
  if (pgaG <= 0.18) return 5.0 + 1.0 * (Math.log10(pgaG) - Math.log10(0.092)) / (Math.log10(0.18) - Math.log10(0.092));
  if (pgaG <= 0.34) return 6.0 + 1.0 * (Math.log10(pgaG) - Math.log10(0.18)) / (Math.log10(0.34) - Math.log10(0.18));
  if (pgaG <= 0.65) return 7.0 + 1.0 * (Math.log10(pgaG) - Math.log10(0.34)) / (Math.log10(0.65) - Math.log10(0.34));
  return Math.min(12.0, 8.0 + 2.0 * (Math.log10(pgaG) - Math.log10(0.65)));
}

// --- Main Engine Executor ---

export async function runHazardEngine(input: HazardInput): Promise<HazardReport> {
  const startTime = Date.now();
  const warnings: string[] = [];
  const apiStatus: Record<string, string> = {};

  const { latitude, longitude, search_radius_km, historical_years, minimum_magnitude } = input;

  // 1. Fetch USGS Events circular search
  let usgsEvents: any[] = [];
  const usgsUrl = "https://earthquake.usgs.gov/fdsnws/event/1/query";
  const startDate = new Date();
  startDate.setFullYear(startDate.getFullYear() - historical_years);
  const startStr = startDate.toISOString().split(".")[0];

  const maxRadiusDeg = search_radius_km / 111.12;

  const queryParams = new URLSearchParams({
    format: "geojson",
    latitude: latitude.toString(),
    longitude: longitude.toString(),
    maxradius: maxRadiusDeg.toString(),
    starttime: startStr,
    minmagnitude: minimum_magnitude.toString(),
    orderby: "time-asc"
  });

  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 6000); // 6s timeout
    const res = await fetch(`${usgsUrl}?${queryParams.toString()}`, { signal: controller.signal });
    clearTimeout(id);

    if (res.ok) {
      const data = await res.json();
      usgsEvents = data?.features || [];
      apiStatus["USGS_Catalog"] = "success";
    } else {
      apiStatus["USGS_Catalog"] = "error";
      warnings.push(`USGS API returned status code ${res.status}`);
    }
  } catch (err) {
    apiStatus["USGS_Catalog"] = "failure";
    warnings.push(`USGS API query failed or timed out: ${(err as Error).message}`);
  }

  // Parse USGS features
  const rawEvents = usgsEvents.map(feature => {
    const props = feature.properties || {};
    const coords = feature.geometry?.coordinates || [0, 0, 0];
    const evLon = coords[0];
    const evLat = coords[1];
    const evDepth = coords[2] ?? 10.0;

    const dist = haversineDistance(latitude, longitude, evLat, evLon);

    return {
      id: feature.id || "unknown",
      magnitude: props.mag ?? 0,
      distance_km: dist,
      depth_km: evDepth,
      date: new Date(props.time || 0).toISOString(),
      place: props.place || "Unknown Event Place",
      max_mmi: props.mmi ?? null
    };
  }).filter(e => e.distance_km <= search_radius_km);

  // 2. Fetch SoilGrids Profile
  const soilProps = await fetchSoilGrids(latitude, longitude);
  apiStatus["SoilGrids"] = soilProps.source.includes("API") ? "success" : "fallback";
  if (soilProps.source.includes("Fallback")) {
    warnings.push(`SoilGrids REST API unavailable. Utilized ${soilProps.source}.`);
  }

  const soilEvaluation = evaluateLiquefaction(soilProps);

  // 3. Match Nearest Fault
  const faultMatch = findNearestFault(latitude, longitude);

  // 4. Calculate Seismicity Hazard Contribution
  let rawSeismicContributionSum = 0.0;
  const processedEvents: ProcessedEvent[] = rawEvents.map(ev => {
    const age = calculateAgeYears(ev.date);
    const wDist = computeDistanceWeight(ev.distance_km);
    const wDepth = computeDepthWeight(ev.depth_km);
    const wMag = computeMagnitudeWeight(ev.magnitude, minimum_magnitude);
    const wAge = computeAgeWeight(age);

    const contribution = wDist * wDepth * wMag * wAge;
    rawSeismicContributionSum += contribution;

    return {
      id: ev.id,
      magnitude: ev.magnitude,
      distance_km: parseFloat(ev.distance_km.toFixed(2)),
      depth_km: parseFloat(ev.depth_km.toFixed(1)),
      date: ev.date,
      place: ev.place,
      individual_contribution: parseFloat(contribution.toFixed(4)),
      distance_weight: parseFloat(wDist.toFixed(3)),
      depth_weight: parseFloat(wDepth.toFixed(3)),
      age_weight: parseFloat(wAge.toFixed(3)),
      magnitude_weight: parseFloat(wMag.toFixed(3))
    };
  }).sort((a, b) => b.individual_contribution - a.individual_contribution);

  const event_score = parseFloat(Math.min(50.0, 15.0 * Math.log(1.0 + rawSeismicContributionSum)).toFixed(2));

  // 5. Calculate Independent Component Scores
  const fault_score = 30.0 * Math.exp(-faultMatch.distance_km / 30.0);
  const soil_score = 20.0 * Math.min(1.0, Math.max(0.0, soilEvaluation.lsi_score));

  // 6. Calibrate to Final Index 0-100
  const combinedRaw = event_score + fault_score + soil_score;
  const overall_score = parseFloat(Math.min(100.0, Math.max(0.0, 100.0 * (1.0 - Math.exp(-combinedRaw / 32.0)))).toFixed(1));

  let hazard_level = "Very Low";
  const numScore = overall_score;
  if (numScore < 20.0) hazard_level = "Very Low";
  else if (numScore < 40.0) hazard_level = "Low";
  else if (numScore < 60.0) hazard_level = "Moderate";
  else if (numScore < 80.0) hazard_level = "High";
  else hazard_level = "Very High";

  let confidence = 0.95;
  if (event_score < 1.0) confidence -= 0.25;

  // 7. Recurrence fitting
  const allMags = rawEvents.map(e => e.magnitude);
  const recurrence = calculateGutenbergRichter(allMags, historical_years, minimum_magnitude);

  // 8. Statistics compilation
  const hasEvents = rawEvents.length > 0;
  const largest_eq = hasEvents ? Math.max(...allMags) : null;
  const closest_eq = hasEvents ? Math.min(...rawEvents.map(e => e.distance_km)) : null;
  const avg_depth = hasEvents ? rawEvents.reduce((a, b) => a + b.depth_km, 0) / rawEvents.length : null;
  const avg_mag = hasEvents ? allMags.reduce((a, b) => a + b, 0) / rawEvents.length : null;

  // Sorting magnitudes for median calculation
  let median_mag = null;
  if (hasEvents) {
    const sorted = [...allMags].sort((a, b) => a - b);
    const half = Math.floor(sorted.length / 2);
    median_mag = sorted.length % 2 !== 0 ? sorted[half] : (sorted[half - 1] + sorted[half]) / 2.0;
  }

  const statistics: HazardStatistics = {
    largest_historical_earthquake: largest_eq != null ? parseFloat(largest_eq.toFixed(1)) : null,
    closest_earthquake_km: closest_eq != null ? parseFloat(closest_eq.toFixed(2)) : null,
    average_depth_km: avg_depth != null ? parseFloat(avg_depth.toFixed(2)) : null,
    average_magnitude: avg_mag != null ? parseFloat(avg_mag.toFixed(2)) : null,
    median_magnitude: median_mag != null ? parseFloat(median_mag.toFixed(2)) : null,
    events_analyzed: rawEvents.length,
    catalog_span_years: historical_years,
    nearest_fault_distance_km: faultMatch.distance_km,
    estimated_recurrence_interval_years: recurrence.recurrence_m6_years != null ? parseFloat(recurrence.recurrence_m6_years.toFixed(1)) : null,
    soil_classification: soilEvaluation.soil_class
  };

  // 9. observed Shakemaps checks
  const sigEvents = rawEvents.filter(e => e.magnitude >= 5.5 && e.distance_km <= 80.0);
  let peakPga = 0.0;
  let peakMmi = 1.0;
  if (sigEvents.length > 0) {
    const dominant = sigEvents.sort((a, b) => b.magnitude - a.magnitude)[0];
    const estPga = estimatePgaG(dominant.magnitude, dominant.distance_km, dominant.depth_km);
    peakPga = estPga;
    peakMmi = pgaToMmi(estPga);

    if (dominant.max_mmi != null) {
      const ratio = estPga / estimatePgaG(dominant.magnitude, 1.0, dominant.depth_km);
      peakMmi = Math.max(1.0, Math.min(12.0, dominant.max_mmi * (1.0 - (1.0 - ratio))));
    }
  }

  // Helper indicator level assigner
  const getColors = (score: number, maxVal: number) => {
    const r = score / maxVal;
    if (r < 0.3) return { level: "Low", color: "green" as const };
    if (r < 0.65) return { level: "Moderate", color: "yellow" as const };
    return { level: "High", color: "red" as const };
  };

  const histColorInfo = getColors(event_score, 40.0);
  const faultColorInfo = getColors(fault_score, 25.0);
  const soilColorInfo = getColors(soil_score, 18.0);
  const zoneColorInfo = getColors(event_score * 0.6 + fault_score * 0.4, 35.0);

  const indicators: Indicators = {
    seismic_zone: {
      value: `Zone ${zoneColorInfo.level}`,
      classification: `${zoneColorInfo.level} regional seismic energy buildup`,
      color: zoneColorInfo.color
    },
    historical_activity: {
      value: `${rawEvents.length} events analyzed`,
      classification: `${histColorInfo.level} historical activity density`,
      color: histColorInfo.color
    },
    soil_liquefaction: {
      value: soilEvaluation.soil_class,
      classification: soilEvaluation.classification,
      color: soilEvaluation.color
    },
    fault_proximity: {
      value: `${faultMatch.distance_km} km`,
      classification: `Proximity to ${faultMatch.fault_name} (${faultMatch.classification})`,
      color: faultMatch.color
    }
  };

  // 10. LLM Environmental context summary sentences
  const summarySentences = [
    `The geographic query location has a calibrated overall Seismic Hazard Score of ${overall_score}/100, resulting in a '${hazard_level}' classification.`,
    `Proximity risk is dominated by the ${faultMatch.fault_name} fault system located ${faultMatch.distance_km} km away, representing a '${faultMatch.classification}' rating.`,
    `Local surface soil texture consists of ${soilEvaluation.soil_class} with a loose bulk density of ${soilProps.bulk_density} g/cm³, causing a '${soilEvaluation.classification}' profile with a seismic wave amplification factor of ${soilEvaluation.amplification_multiplier}x.`
  ];

  if (rawEvents.length > 0) {
    summarySentences.push(`Historical earthquake record shows ${rawEvents.length} analyzed events of M${minimum_magnitude}+ within a ${search_radius_km}km radius over the past ${historical_years} years. The largest event registered magnitude M${statistics.largest_historical_earthquake} located ${statistics.closest_earthquake_km}km away.`);
    if (recurrence.recurrence_m6_years) {
      summarySentences.push(`Local Gutenberg-Richter b-value is calculated at ${recurrence.b_value.toFixed(2)}, indicating a statistical M6.0+ recurrence interval of approximately ${recurrence.recurrence_m6_years.toFixed(1)} years.`);
    }
  } else {
    summarySentences.push(`No historical earthquake events of magnitude M${minimum_magnitude}+ were found within ${search_radius_km}km of coordinates in the past ${historical_years} years, indicating a highly stable geological crust.`);
  }

  const executionTime = (Date.now() - startTime) / 1000.0;

  return {
    location: {
      latitude,
      longitude,
      place_name: `Grid Reference [${latitude.toFixed(4)}, ${longitude.toFixed(4)}]`
    },
    hazard: {
      overall_score,
      hazard_level,
      confidence
    },
    indicators,
    statistics,
    environmental_context: {
      hazard_score: overall_score,
      hazard_level,
      historical_activity: {
        classification: histColorInfo.level,
        events_within_radius: rawEvents.length,
        largest_magnitude: statistics.largest_historical_earthquake
      },
      faults: {
        distance_km: faultMatch.distance_km,
        classification: faultMatch.classification
      },
      soil: {
        classification: soilEvaluation.classification,
        dominant_soil: soilEvaluation.soil_class
      },
      ground_motion: {
        estimated_intensity: parseFloat(peakMmi.toFixed(2)),
        confidence
      },
      summary: summarySentences
    },
    events: processedEvents,
    metadata: {
      warnings,
      execution_time_seconds: parseFloat(executionTime.toFixed(4)),
      api_status: apiStatus,
      model_version: "v1.1.2-deterministic"
    }
  };
}
