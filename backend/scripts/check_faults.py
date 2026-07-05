import sys
sys.path.insert(0, r"d:\Work\Projects\ResillienceAI\backend")
from services.hazard_engine.faults import find_nearest_fault
from services.hazard_engine.utils import distance_to_line_segment
from services.hazard_engine.constants import MAJOR_FAULTS

cities = {"Singapore": (1.3521, 103.8198), "Bangkok": (13.7563, 100.5018)}
for name, (lat, lon) in cities.items():
    f = find_nearest_fault(lat, lon)
    print(name, f)
    for fname, verts in MAJOR_FAULTS.items():
        md = min(distance_to_line_segment(lat, lon, verts[i][0], verts[i][1], verts[i+1][0], verts[i+1][1]) for i in range(len(verts)-1))
        print(f"  {fname}: {md:.1f} km")
