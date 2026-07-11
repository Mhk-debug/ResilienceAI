"""

hazard_engine/soil.py

"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import time
import logging
from typing import Dict, Any, Optional, Tuple
from owslib.wcs import WebCoverageService
import rasterio
from rasterio.io import MemoryFile
import numpy as np


logger = logging.getLogger(__name__)


properties_names = ["clay", "sand", "silt", "bdod", "cfvo", "soc"]
delta = 0.01 # Increasing this lowers the accuracy of the fallback average soil properties
value = 'mean'
depths = ["0-5cm", "5-15cm", "15-30cm"]

_SOIL_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
_SOIL_CACHE: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}


def _get_cache_key(lat: float, lon: float) -> Tuple[float, float]:
    return (round(lat, 3), round(lon, 3))

def _get_cached_soil_properties(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    cache_key = _get_cache_key(lat, lon)
    cached_entry = _SOIL_CACHE.get(cache_key)
    if cached_entry is None:
        return None

    cached_at, data = cached_entry
    if time.time() - cached_at > _SOIL_CACHE_TTL_SECONDS:
        _SOIL_CACHE.pop(cache_key, None)
        return None

    return copy.deepcopy(data)

def _cache_soil_properties(lat: float, lon: float, data: Dict[str, Any]) -> None:
    _SOIL_CACHE[_get_cache_key(lat, lon)] = (time.time(), copy.deepcopy(data))


def fetch_soilgrids_data(lat: float, lon: float) -> Dict[str, Any]:
    cached = _get_cached_soil_properties(lat, lon)
    if cached is not None:
        return cached

    try:
        values = _fetch_all_layers(lat, lon)
        result = _convert_to_features(values)
    except Exception as e:
        logger.warning(f"WCS soil fetch failed: {e}")
        result = get_fallback_soil_properties(lat, lon)

    _cache_soil_properties(lat, lon, result)
    return result


def _fetch_all_layers(lat: float, lon: float) -> Dict[str, float]:

    params = {
        "crs": "urn:ogc:def:crs:EPSG::4326",
        "format": "GEOTIFF_INT16",
        "resx": 0.001,
        "resy": 0.001,
        "bbox": (
            lon - delta,
            lat - delta,
            lon + delta,
            lat + delta,
        ),
    }

    results = {}

    for prop in properties_names:

        depth_values = []

        url = f"https://maps.isric.org/mapserv/{prop}"

        wcs = WebCoverageService(url, version="1.0.0")

        for depth in depths:

            identifier = f"{prop}_{depth}_{value}"

            try:

                response = wcs.getCoverage(
                    identifier=identifier,
                    crs=params["crs"],
                    bbox=params["bbox"],
                    resx=params["resx"],
                    resy=params["resy"],
                    format=params["format"],
                )

                data = response.read()

                with MemoryFile(data) as memfile:

                    with memfile.open() as src:

                        point = next(src.sample([(lon, lat)]))[0]

                        nodata = src.nodata

                        if nodata is None or point != nodata:

                            depth_values.append(float(point))

                        else:

                            band = src.read(1)

                            if nodata is not None:
                                valid = band[band != nodata]
                            else:
                                valid = band.flatten()

                            if valid.size > 0:
                                depth_values.append(float(np.mean(valid)))

            except Exception as e:

                logger.warning(f"{identifier}: {e}")

        if depth_values:

            results[prop] = float(np.mean(depth_values))

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

