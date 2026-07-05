from owslib.wcs import WebCoverageService


wcs = WebCoverageService('http://maps.isric.org/mapserv?map=/map/soc.map', version='1.0.0') # request for soil carbon


# The link to request can be found by entering the request name in
# 'http://maps.isric.org/mapserv?map=/map/{request name}.map'.
# https://maps.isric.org/?utm_source=chatgpt.com has the request names of all the datas.


# print([op.name for op in wcs.operations]) # returns the available operation that can be done on this request
# print(list(wcs.contents)) # returns the name of the coverages available. ex. soc_0-5cm_mean

name = "soc_0-5cm_mean"

# a = wcs.contents[name] # returns the coverage object corresponding to the name
# print("crs --", a.supportedCRS, "\n") # returns the supported coordinate reference system.
# Use the epsg 4326 as we only have to enter the lattitude and longitude.

# print("formats --", a.supportedFormats, "\n") # returns supported format
# print("box --", a.boundingboxes) # returns the full area of bbox available

# EXAMPLE
response = wcs.getCoverage(
    identifier= name,
    crs= 'urn:ogc:def:crs:EPSG::4326',
    bbox= (95.90, 16.60, 96.40, 17.20), #bbox of yangon using lati- and longi-
    resx=0.01, resy=0.01, # the lower it is the higher the detail but may overload the file
    format= 'GEOTIFF_INT16'
)

with open("Yangon_soc_0-5_mean.tif", 'wb') as file:
    file.write(response.read())