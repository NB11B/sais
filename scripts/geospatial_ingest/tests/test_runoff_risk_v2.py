import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from intelligence import compute_runoff_risk

def create_mock_raster(path, data, nodata=-9999):
    transform = from_origin(0, 100, 10, 10)
    with rasterio.open(
        path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=data.dtype, crs='EPSG:32610', transform=transform, nodata=nodata
    ) as dst:
        dst.write(data, 1)

def test_runoff_risk_bounds(tmp_path):
    slope_path = os.path.join(tmp_path, 'slope.tif')
    soil_path = os.path.join(tmp_path, 'soil.tif')
    flow_path = os.path.join(tmp_path, 'flow.tif')
    out_risk_path = os.path.join(tmp_path, 'risk.tif')
    
    # 1. Slope: Extreme 90 degrees
    slope = np.ones((10, 10), dtype=np.float32) * 90.0
    create_mock_raster(slope_path, slope)
    
    # 2. Soil: Highly impermeable (4.0)
    soil = np.ones((10, 10), dtype=np.float32) * 4.0
    create_mock_raster(soil_path, soil)
    
    # 3. Flow accumulation: Extreme high values
    flow = np.ones((10, 10), dtype=np.float32) * 1000000.0
    create_mock_raster(flow_path, flow)
    
    risk = compute_runoff_risk(slope_path, soil_path, flow_path, out_risk_path)
    
    # Risk should not exceed 100
    assert np.max(risk) <= 100.0, f"Max risk should be <= 100, got {np.max(risk)}"
    assert np.min(risk) >= 0.0, f"Min risk should be >= 0, got {np.min(risk)}"
