import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from terrain import calculate_slope_and_aspect

def test_nodata_is_preserved(tmp_path):
    dem_path = os.path.join(tmp_path, 'dem.tif')
    slope_path = os.path.join(tmp_path, 'slope.tif')
    aspect_path = os.path.join(tmp_path, 'aspect.tif')
    
    dem = np.ones((10, 10), dtype=np.float32) * 100
    dem[0, 0] = -9999  # NoData pixel
    
    transform = from_origin(0, 100, 10, 10)
    
    with rasterio.open(
        dem_path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=dem.dtype, crs='EPSG:32610', transform=transform, nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    slope, aspect = calculate_slope_and_aspect(dem_path, slope_path, aspect_path)
    
    assert slope[0, 0] == -9999, "NoData should be preserved in slope"
    assert aspect[0, 0] == -9999, "NoData should be preserved in aspect"
    assert slope[5, 5] != -9999, "Valid pixels should not be NoData"
