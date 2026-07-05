"""
hazard_engine/utils.py
"""
import math
from datetime import datetime

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def distance_to_line_segment(
    lat: float, lon: float,
    lat_start: float, lon_start: float,
    lat_end: float, lon_end: float
) -> float:
    d_start = haversine_distance(lat, lon, lat_start, lon_start)
    d_end = haversine_distance(lat, lon, lat_end, lon_end)
    d_segment = haversine_distance(lat_start, lon_start, lat_end, lon_end)
    
    if d_segment < 0.001:
        return d_start
        
    avg_lat = math.radians((lat + lat_start + lat_end) / 3.0)
    cos_lat = math.cos(avg_lat)
    
    x = (lon - lon_start) * 111.13 * cos_lat
    y = (lat - lat_start) * 111.13
    
    x2 = (lon_end - lon_start) * 111.13 * cos_lat
    y2 = (lat_end - lat_start) * 111.13
    
    segment_len_sq = x2 * x2 + y2 * y2
    if segment_len_sq < 0.001:
        return d_start
        
    t = (x * x2 + y * y2) / segment_len_sq
    t = min(1.0, max(0.0, t))
    
    closest_lat = lat_start + t * (lat_end - lat_start)
    closest_lon = lon_start + t * (lon_end - lon_start)
    
    return haversine_distance(lat, lon, closest_lat, closest_lon)

def calculate_age_years(date_str: str) -> float:
    try:
        # Standardize date formats (replace trailing Z with +00:00)
        formatted_date = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(formatted_date)
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        return max(0.0, diff.days / 365.25)
    except Exception:
        return 5.0
