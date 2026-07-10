"""

hazard_engine/soil.py

"""

import logging

from typing import Dict, Any



logger = logging.getLogger(__name__)



import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def fetch_soilgrids_data(lat: float, lon: float) -> Dict[str, Any]:
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    properties = ["clay", "sand", "silt", "bdod", "cfvo", "ocd"]
    
    params = {
        "lon": lon,
        "lat": lat,
        "property": properties,
        "value": "mean"
    }
    
    # Configure an HTTP transport layer that automatically retries dropped connections
    transport = httpx.AsyncHTTPTransport(retries=3)
    
    # Extended timeout configuration:
    # 5.0s to connect, 15.0s to wait for SoilGrids to finish its heavy database read
    timeout = httpx.Timeout(timeout=15.0, connect=5.0)

    try:
        async with httpx.AsyncClient(transport=transport, timeout=timeout) as client:
            # Send an asynchronous, non-blocking GET request
            response = await client.get(
                url, 
                params=params, 
                headers={"User-Agent": "EarthquakeHazardEngine/1.0"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return parse_soilgrids_json(data)
            else:
                logger.warning(f"SoilGrids API returned status code {response.status_code}")
                
    except httpx.TimeoutException:
        logger.warning(f"SoilGrids API request timed out after 15 seconds for coordinates ({lat}, {lon})")
    except Exception as e:
        logger.warning(f"Failed to fetch SoilGrids API: {str(e)}")
        
    # Safely hit your fallback strategy if the API is down or timing out
    return get_fallback_soil_properties(lat, lon)



def parse_soilgrids_json(data: Dict[str, Any]) -> Dict[str, Any]:

    raw_properties = {}

    try:

        layers = data.get("properties", {}).get("layers", [])

        for layer in layers:

            name = layer.get("name")

            depths = layer.get("depths", [])

            values = []

            for d in depths:

                label = d.get("label", "")

                if label in ["0-5cm", "5-15cm", "15-30cm"]:

                    mean_val = d.get("values", {}).get("mean")

                    if mean_val is not None:

                        values.append(mean_val)

            if values:

                avg_val = sum(values) / len(values)

                raw_properties[name] = avg_val

    except Exception as e:

        logger.error(f"Error parsing SoilGrids JSON: {str(e)}")



    sand_pct = raw_properties.get("sand", 400.0) / 10.0

    clay_pct = raw_properties.get("clay", 250.0) / 10.0

    silt_pct = raw_properties.get("silt", 350.0) / 10.0

    bulk_density = raw_properties.get("bdod", 1350.0) / 1000.0

    coarse_frags = raw_properties.get("cfvo", 100.0) / 10.0

    org_carbon = raw_properties.get("ocd", 150.0) / 1000.0

   

    total_frac = sand_pct + clay_pct + silt_pct

    if total_frac > 0:

        sand_pct = (sand_pct / total_frac) * 100.0

        clay_pct = (clay_pct / total_frac) * 100.0

        silt_pct = (silt_pct / total_frac) * 100.0



    return {

        "sand_pct": sand_pct,

        "clay_pct": clay_pct,

        "silt_pct": silt_pct,

        "bulk_density": bulk_density,

        "coarse_fragments_pct": coarse_frags,

        "organic_carbon_pct": org_carbon,

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

