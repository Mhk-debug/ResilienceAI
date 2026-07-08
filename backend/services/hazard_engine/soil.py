"""

hazard_engine/soil.py

"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any
from owslib.wcs import WebCoverageService
import tempfile
import rasterio
import numpy as np


logger = logging.getLogger(__name__)


properties_names = ["clay", "sand", "silt", "bdod", "cfvo", "soc"]
delta = 0.01 # Increasing this lowers the accuracy of the fallback average soil properties
value = 'mean'
depths = ["0-5cm", "5-15cm", "15-30cm"]

def fetch_soilgrids_data(lat: float, lon: float) -> Dict[str, Any]:
    try:
        rasters = _download_all_layers(lat, lon)
        values = _sample_all_layers(rasters, lat, lon)

        return _convert_to_features(values)

    except Exception as e:
        logger.warning(f"WCS soil fetch failed: {e}")
        return get_fallback_soil_properties(lat, lon)


def _download_all_layers(lat: float, lon: float) -> Dict[str, str]:
    
    params = {
        "crs": 'urn:ogc:def:crs:EPSG::4326',
        "format": 'GEOTIFF_INT16',
        "resx":0.001,
        "resy":0.001,
        "bbox": (lon-delta, lat-delta, lon+delta, lat+delta),
    }

    files = {}

    for i in range(len(properties_names)):
        files[properties_names[i]] = []

        for depth in depths:
            try:
                properties = f"{properties_names[i]}_{depth}_{value}"
                url = f"http://maps.isric.org/mapserv?map=/map/{properties_names[i]}.map"

                wcs = WebCoverageService(url, version='1.0.0')
                response = wcs.getCoverage(
                    identifier = properties[i],
                    crs = params["crs"],
                    bbox = params["bbox"],
                    resx = params["resx"],
                    resy = params["resy"],
                    format = params["format"]
                )

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tif")
                tmp.write(response.read())
                tmp.close()

                files[properties_names[i]].append(tmp.name)

            except Exception as e:
                logger.warning(f"Failed to fetch SoilGrids API: {str(e)}")

    return files


def _sample_all_layers(files: Dict[str, list[str]], lat: float, lon: float) -> Dict[str, float]:
    results = {}

    for prop, layers in files.items():
        layer_values = []

        for path in layers:
            try:
                with rasterio.open(path) as src:

                    # Try sampling the requested location first
                    point_val = next(src.sample([(lon, lat)]))[0]

                    nodata = src.nodata

                    # If the sampled point is valid, use it
                    if nodata is None or point_val != nodata:
                        layer_values.append(float(point_val))
                        continue

                    # Otherwise, fall back to averaging all valid pixels
                    band = src.read(1)

                    if nodata is not None:
                        valid = band[band != nodata]
                    else:
                        valid = band.flatten()

                    if valid.size > 0:
                        layer_values.append(float(np.mean(valid)))

            except Exception as e:
                logger.warning(f"Sampling failed for {prop}: {e}")

        # Average the 0–5, 5–15 and 15–30 cm layers
        if layer_values:
            results[prop] = float(np.mean(layer_values))

    return results


def _convert_to_features(v: Dict[str, float]) -> Dict[str, Any]:

    sand = v.get("sand", 400) / 10.0
    clay = v.get("clay", 250) / 10.0
    silt = v.get("silt", 350) / 10.0

    bdod = v.get("bdod", 1300) / 1000.0
    cfvo = v.get("cfvo", 100) / 10.0
    soc = v.get("soc", 150) / 1000.0

    # normalize texture
    total = sand + clay + silt
    if total > 0:
        sand = sand / total * 100
        clay = clay / total * 100
        silt = silt / total * 100

    return {
        "sand_pct": sand,
        "clay_pct": clay,
        "silt_pct": silt,

        "bulk_density": bdod,
        "coarse_fragments_pct": cfvo,
        "organic_carbon_pct": soc,

        "source": "SoilGrids API"
    }

def get_fallback_soil_properties(lat: float, lon: float) -> Dict[str, Any]:

    is_delta = False

    deltas = [

        {"name": "Mississippi Delta / New Orleans", "lat": (29.0, 31.0), "lon": (-91.0, -89.0)},

        {"name": "Ganges Delta / Bangladesh", "lat": (21.0, 24.0), "lon": (88.0, 91.0)},

        {"name": "Tokyo Bay / Soft alluvial", "lat": (35.2, 35.8), "lon": (139.5, 140.2)},

        {"name": "San Francisco Bay mud", "lat": (37.4, 38.0), "lon": (-122.5, -122.1)},

        {"name": "Bangkok Chao Phraya mud", "lat": (13.5, 14.1), "lon": (100.2, 100.8)},

    ]

   

    for d in deltas:

        lat_range = d["lat"]

        lon_range = d["lon"]

        if lat_range[0] <= lat <= lat_range[1] and lon_range[0] <= lon <= lon_range[1]:

            is_delta = True

            break

           

    if is_delta:

        return {

            "sand_pct": 72.0,

            "clay_pct": 8.0,

            "silt_pct": 20.0,

            "bulk_density": 1.15,

            "coarse_fragments_pct": 2.0,

            "organic_carbon_pct": 2.5,

            "source": "Deterministic Coastal/Alluvial Heuristic (Fallback)"

        }

   

    return {

        "sand_pct": 42.0,

        "clay_pct": 24.0,

        "silt_pct": 34.0,

        "bulk_density": 1.42,

        "coarse_fragments_pct": 12.0,

        "organic_carbon_pct": 1.1,

        "source": "Deterministic Regional Loam (Fallback)"

    }



def classify_soil_texture(sand: float, clay: float, silt: float) -> str:

    if sand >= 85.0:

        return "Sand"

    elif sand >= 70.0 and clay <= 15.0:

        return "Loamy Sand"

    elif clay >= 40.0:

        return "Clay"

    elif clay >= 35.0 and sand >= 45.0:

        return "Sandy Clay"

    elif clay >= 27.0 and silt >= 28.0:

        return "Clay Loam"

    elif silt >= 80.0:

        return "Silt"

    elif silt >= 50.0:

        return "Silt Loam"

    else:

        return "Loam"



def evaluate_liquefaction_risk(soil_props: Dict[str, Any]) -> Dict[str, Any]:

    sand = soil_props["sand_pct"]

    clay = soil_props["clay_pct"]

    density = soil_props["bulk_density"]

    coarse = soil_props["coarse_fragments_pct"]

   

    sand_factor = min(1.0, max(0.0, (sand - 30.0) / 45.0))

    clay_factor = min(1.0, max(0.0, (30.0 - clay) / 20.0))

    density_factor = min(1.0, max(0.0, (1.6 - density) / 0.45))

    coarse_factor = min(1.0, max(0.0, (25.0 - coarse) / 20.0))

   

    lsi = sand_factor * clay_factor * density_factor * coarse_factor

   

    if lsi >= 0.55:

        risk = "High"

        color = "red"

        amp_multiplier = 1.45

    elif lsi >= 0.25:

        risk = "Moderate"

        color = "yellow"

        amp_multiplier = 1.15

    else:

        risk = "Low"

        color = "green"

        amp_multiplier = 0.85

       

    soil_class = classify_soil_texture(sand, clay, soil_props["silt_pct"])

   

    return {

        "lsi_score": lsi,

        "classification": f"{risk} Liquefaction Risk",

        "color": color,

        "soil_class": soil_class,

        "amplification_multiplier": amp_multiplier,

        "assumptions": [

            "Inferred purely from shallow soil texture fractions (0-30cm) and bulk density.",

            "Assumes fully saturated water table conditions (typical conservative engineering baseline).",

            "Does not account for local piling, artificial fill, or engineered structural foundations."

        ]

    } 

