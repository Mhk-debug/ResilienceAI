import asyncio
import re
from backend.services import calculate_hazard

CITIES = [
    { "name": "Singapore", "lat": 1.3521, "lon": 103.8198, "expected": "10–25 (Very Low)" },
    { "name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "expected": "20–40 (Low–Moderate)" },
    { "name": "Yangon", "lat": 16.8661, "lon": 96.1951, "expected": "45–60 (Moderate–High boundary)" },
    { "name": "Mandalay", "lat": 21.9588, "lon": 96.0891, "expected": "55–70 (High end of moderate/high)" },
    { "name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "expected": "80–95 (Very High)" },
    { "name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "expected": "75–90 (Very High)" }
]

async def verify():
    print("==================================================")
    print("   VERIFYING RECALIBRATED PYTHON HAZARD SCORES    ")
    print("==================================================")

    all_pass = True

    for city in CITIES:
        try:
            result = await calculate_hazard(
                latitude=city["lat"],
                longitude=city["lon"],
                search_radius_km=100,
                historical_years=50,
                minimum_magnitude=4.5
            )

            score = result["hazard"]["overall_score"]
            level = result["hazard"]["hazard_level"]
            
            # Extract numeric boundaries from expected string
            # e.g. "10–25 (Very Low)" -> min: 10, max: 25
            matches = re.match(r"^(\d+)–(\d+)", city["expected"])
            if not matches:
                raise Exception(f"Failed to parse expected range for {city['name']}")
            
            min_val = int(matches.group(1))
            max_val = int(matches.group(2))

            is_pass = min_val <= score <= max_val
            if not is_pass:
                all_pass = False

            print(f"\n📍 City: {city['name']}")
            print(f"   Coordinates : ({city['lat']}, {city['lon']})")
            print(f"   Expected    : {city['expected']}")
            print(f"   Calibrated  : {score} ({level}) [{'PASS' if is_pass else 'FAIL'}]")
            print(f"   Primary Fault: {result['environmental_context']['faults']['distance_km']:.1f} km")
            print(f"   Soil Class  : {result['environmental_context']['soil']['dominant_soil']} ({result['environmental_context']['soil']['classification']})")
            print(f"   EQ Events   : {result['environmental_context']['historical_activity']['events_within_radius']}")
        except Exception as e:
            print(f"❌ Error verifying {city['name']}: {e}")
            all_pass = False

    print("\n==================================================")
    if all_pass:
        print("  ✅ ALL REGIONAL PYTHON HAZARD SCORES FALL IN EXPECTED BANDS!")
    else:
        print("  ❌ SOME PYTHON SCORES FALL OUTSIDE OF EXPECTED BANDS!")
    print("==================================================")

asyncio.run(verify())
