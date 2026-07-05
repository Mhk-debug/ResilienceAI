"""
hazard_engine/usgs.py
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from .utils import haversine_distance

logger = logging.getLogger(__name__)

def query_usgs_catalog(
    latitude: float,
    longitude: float,
    search_radius_km: float = 100.0,
    historical_years: float = 50.0,
    min_magnitude: float = 4.0
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[str]]:
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    start_date = datetime.utcnow() - timedelta(days=365.25 * historical_years)
    start_str = start_date.isoformat().split(".")[0]
    
    max_radius_deg = search_radius_km / 111.12
    
    params = {
        "format": "geojson",
        "latitude": latitude,
        "longitude": longitude,
        "maxradius": max_radius_deg,
        "starttime": start_str,
        "minmagnitude": min_magnitude,
        "orderby": "time-asc"
    }
    
    events = []
    status = {"status": "success"}
    warnings = []
    
    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        req = urllib.request.Request(full_url, headers={"User-Agent": "EarthquakeHazardEngine/1.0"})
        with urllib.request.urlopen(req, timeout=6.0) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                data = json.loads(body)
                features = data.get("features", [])
                for feature in features:
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])
                    
                    ev_lon = coords[0]
                    ev_lat = coords[1]
                    ev_depth = coords[2] if len(coords) > 2 else 10.0
                    
                    dist = haversine_distance(latitude, longitude, ev_lat, ev_lon)
                    
                    events.append({
                        "id": feature.get("id", "unknown"),
                        "magnitude": props.get("mag", 0.0),
                        "distance_km": dist,
                        "depth_km": ev_depth,
                        "date": datetime.utcfromtimestamp((props.get("time", 0) / 1000.0)).isoformat() + "Z",
                        "place": props.get("place", "Unknown Event Place"),
                        "max_mmi": props.get("mmi")
                    })
                # Filter events within radius
                events = [e for e in events if e["distance_km"] <= search_radius_km]
            else:
                status = {"status": "error"}
                warnings.append(f"USGS API returned status code {response.status}")
    except urllib.error.URLError as e:
        if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason).lower():
            status = {"status": "timeout"}
            warnings.append("USGS API query timed out.")
        else:
            status = {"status": "failure"}
            warnings.append(f"USGS API query failed: {str(e)}")
    except Exception as e:
        status = {"status": "failure"}
        warnings.append(f"USGS API query failed: {str(e)}")
        
    return events, status, warnings
