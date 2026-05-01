import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from terrain import calculate_slope_and_aspect, process_hydrology

def create_synthetic_dem(path):
    """
    Creates a 10x10 synthetic DEM sloping evenly from East to West.
    Actually West to East (higher on left, lower on right)
    """
    dem = np.zeros((10, 10), dtype=np.float32)
    for i in range(10):
        dem[:, i] = 100 - i * 10
        
    transform = from_origin(0, 100, 10, 10)
    
    with rasterio.open(
        path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=dem.dtype, crs='EPSG:32610', transform=transform, nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    return dem

def test_synthetic_dem_slope_aspect_flow(tmp_path):
    dem_path = os.path.join(tmp_path, 'synth_dem.tif')
    slope_path = os.path.join(tmp_path, 'synth_slope.tif')
    aspect_path = os.path.join(tmp_path, 'synth_aspect.tif')
    flow_acc_path = os.path.join(tmp_path, 'synth_flow_acc.tif')
    
    create_synthetic_dem(dem_path)
    
    slope, aspect = calculate_slope_and_aspect(dem_path, slope_path, aspect_path)
    
    center_slope = slope[5, 5]
    assert 40 < center_slope < 50, f"Expected slope ~45.0, got {center_slope:.2f}"
    
    center_aspect = aspect[5, 5]
    assert 80 < center_aspect < 100, f"Expected aspect ~90.0, got {center_aspect:.2f}"
    
    acc = process_hydrology(dem_path, flow_acc_path)
    
    max_acc_col = np.argmax(np.sum(acc, axis=0))
    assert max_acc_col == 9, f"Expected flow to accumulate at East column 9, got {max_acc_col}"
