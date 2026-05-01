import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from terrain import calculate_slope_and_aspect

def test_geographic_crs_rejection(tmp_path):
    dem_path = os.path.join(tmp_path, 'geo_dem.tif')
    slope_path = os.path.join(tmp_path, 'geo_slope.tif')
    aspect_path = os.path.join(tmp_path, 'geo_aspect.tif')
    
    dem = np.zeros((10, 10), dtype=np.float32)
    transform = from_origin(-120, 45, 0.01, 0.01)
    
    with rasterio.open(
        dem_path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=dem.dtype, crs='EPSG:4326', transform=transform, nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    with pytest.raises(ValueError, match="DEM CRS EPSG:4326 is geographic"):
        calculate_slope_and_aspect(dem_path, slope_path, aspect_path)
