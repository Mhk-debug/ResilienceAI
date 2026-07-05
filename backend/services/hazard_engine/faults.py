"""
hazard_engine/faults.py
"""
import math
from typing import Dict, Any
from .utils import haversine_distance, distance_to_line_segment
from .constants import (
    FAULT_VERY_HIGH_LIMIT,
    FAULT_HIGH_LIMIT,
    FAULT_MODERATE_LIMIT
)

MAJOR_FAULTS = {
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
    ]
}

def find_nearest_fault(lat: float, lon: float) -> Dict[str, Any]:
    closest_fault_name = "Unknown Regional Active Fault"
    min_distance = 9999.0
    
    for fault_name, vertices in MAJOR_FAULTS.items():
        if not vertices:
            continue
            
        if len(vertices) == 1:
            dist = haversine_distance(lat, lon, vertices[0][0], vertices[0][1])
            if dist < min_distance:
                min_distance = dist
                closest_fault_name = fault_name
            continue
            
        for i in range(len(vertices) - 1):
            start = vertices[i]
            end = vertices[i+1]
            dist = distance_to_line_segment(lat, lon, start[0], start[1], end[0], end[1])
            if dist < min_distance:
                min_distance = dist
                closest_fault_name = fault_name
                
    classification = "Low Proximity"
    color = "green"
    
    if min_distance <= FAULT_VERY_HIGH_LIMIT:
        classification = "Very High Proximity"
        color = "red"
    elif min_distance <= FAULT_HIGH_LIMIT:
        classification = "High Proximity"
        color = "red"
    elif min_distance <= FAULT_MODERATE_LIMIT:
        classification = "Moderate Proximity"
        color = "yellow"
        
    if min_distance > 150.0:
        background_est = min(min_distance, 120.0)
        return {
            "fault_name": "Unmapped Local Crustal Fault",
            "distance_km": background_est,
            "classification": "Low Proximity",
            "color": "green"
        }
        
    return {
        "fault_name": closest_fault_name,
        "distance_km": round(min_distance, 2),
        "classification": classification,
        "color": color
    }
