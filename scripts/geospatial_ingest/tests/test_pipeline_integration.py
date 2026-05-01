import os
import sys
import pytest
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Polygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline import run_pipeline

def test_full_pipeline_integration(tmp_path):
    dem_path = os.path.join(tmp_path, 'dem.tif')
    soil_path = os.path.join(tmp_path, 'soils.geojson')
    
    dem = np.zeros((10, 10), dtype=np.float32)
    for i in range(10): dem[:, i] = 100 - i * 10
    transform = from_origin(0, 100, 10, 10)
    with rasterio.open(
        dem_path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=dem.dtype, crs='EPSG:32610', transform=transform, nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    gdf = gpd.GeoDataFrame({'hydrologic_group': ['B'], 'geometry': [poly]}, crs='EPSG:32610')
    gdf.to_file(soil_path, driver='GeoJSON')
    
    run_pipeline(str(tmp_path), str(tmp_path))
    
    assert os.path.exists(os.path.join(tmp_path, 'slope.tif'))
    assert os.path.exists(os.path.join(tmp_path, 'aspect.tif'))
    assert os.path.exists(os.path.join(tmp_path, 'flow_accumulation.tif'))
    assert os.path.exists(os.path.join(tmp_path, 'soils_hydrologic_group.tif'))
    assert os.path.exists(os.path.join(tmp_path, 'runoff_risk.tif'))
    
    manifest_path = os.path.join(tmp_path, 'manifest.json')
    assert os.path.exists(manifest_path)
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        assert manifest["farm_id"] == "local"
        assert "slope" in manifest["derived_layers"]
        assert "runoff_risk" in manifest["derived_layers"]
