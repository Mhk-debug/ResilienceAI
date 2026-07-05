import rasterio
ph = rasterio.open("C:/Users/LENOVO/3D Objects/STI/AI Competition/Soilgrids/Yangon_soc_0-5_mean.tif", driver="GTiff")
from rasterio import plot

plot.show(ph, title='Mean soc between 0 and 5 cm deep in Yangon', cmap='gist_ncar')