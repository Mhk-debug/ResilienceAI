import tempfile
from typing import Any, Dict
import logging
from owslib.wcs import WebCoverageService
import rasterio

logger = logging.getLogger(__name__)

wcs = WebCoverageService('http://maps.isric.org/mapserv?map=/map/soc.map', version='1.0.0') # request for soil carbon


# The link to request can be found by entering the request name in
# 'http://maps.isric.org/mapserv?map=/map/{request name}.map'.
# https://maps.isric.org/?utm_source=chatgpt.com has the request names of all the datas.


# print([op.name for op in wcs.operations]) # returns the available operation that can be done on this request
# print(list(wcs.contents)) # returns the name of the coverages available. ex. soc_0-5cm_mean

# name = "soc_0-5cm_mean"

# a = wcs.contents[name] # returns the coverage object corresponding to the name
# print("crs --", a.supportedCRS, "\n") # returns the supported coordinate reference system.
# # Use the epsg 4326 as we only have to enter the lattitude and longitude.

# print("formats --", a.supportedFormats, "\n") # returns supported format
# print("box --", a.boundingboxes) # returns the full area of bbox available

# EXAMPLE
# response = wcs.getCoverage(
#     identifier= "soc_0-5cm_mean",
#     crs= 'urn:ogc:def:crs:EPSG::4326',
#     bbox= (95.90, 16.60, 96.40, 17.20), #bbox of yangon using lati- and longi-
#     resx=0.01, resy=0.01, # the lower it is the higher the detail but may overload the file
#     format= 'GEOTIFF_INT16'
# )

properties_names = ["clay", "sand", "silt", "bdod", "cfvo", "soc"]
value = 'mean'
depth = '0-5cm'
delta = 0.05
properties = [f"{p}_{depth}_{value}" for p in properties_names]

CITIES = [
    { "name": "Singapore", "lat": 1.3521, "lon": 103.8198, "expected": "10–25 (Very Low)" },
    { "name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "expected": "20–40 (Low–Moderate)" },
    { "name": "Yangon", "lat": 16.8661, "lon": 96.1951, "expected": "45–60 (Moderate–High boundary)" },
    { "name": "Mandalay", "lat": 21.9588, "lon": 96.0891, "expected": "55–70 (High end of moderate/high)" },
    { "name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "expected": "80–95 (Very High)" },
    { "name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "expected": "]75–90 (Very High)" }]

for x in range(len(CITIES)):
    print(CITIES[x]["name"])
    for i in range(len(properties)):
        wcs = WebCoverageService(f"http://maps.isric.org/mapserv?map=/map/{properties_names[i]}.map", version='1.0.0')

        response = wcs.getCoverage(
            identifier= properties[i],
            crs= 'urn:ogc:def:crs:EPSG::4326',
            bbox= (CITIES[x]["lon"]-delta, CITIES[x]["lat"]-delta, CITIES[x]["lon"]+delta, CITIES[x]["lat"]+delta), #bbox of yangon using lati- and longi-
            resx=0.01, resy=0.01, # the lower it is the higher the detail but may overload the file
            format= 'GEOTIFF_INT16'
        )

        with open("map.tif", "wb") as f:
            f.write(response.read())

        results = {}


        try:
            with rasterio.open("map.tif") as src:
                val = next(src.sample([(CITIES[x]["lon"], CITIES[x]["lat"])]))[0]

                if val == src.nodata:
                    print("No data at this location.")
                    continue

                results[properties_names[i]] = float(val)

        except Exception as e:
            logger.warning(f"Sampling failed for {properties_names[i]}: {e}")

        print(results)



