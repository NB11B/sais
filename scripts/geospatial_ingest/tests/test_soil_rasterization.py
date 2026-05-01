import os
import sys
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Polygon

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from soils import rasterize_soils

def create_mock_raster(path):
    transform = from_origin(0, 100, 10, 10)
    data = np.zeros((10, 10), dtype=np.float32)
    with rasterio.open(
        path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=data.dtype, crs='EPSG:32610', transform=transform, nodata=-9999
    ) as dst:
        dst.write(data, 1)

def test_soil_hydrologic_group_mapping(tmp_path):
    raster_path = os.path.join(tmp_path, 'template.tif')
    create_mock_raster(raster_path)
    
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    gdf = gpd.GeoDataFrame({'hydrologic_group': ['C/D'], 'geometry': [poly]}, crs='EPSG:32610')
    
    geojson_path = os.path.join(tmp_path, 'soils.geojson')
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    out_soil_path = os.path.join(tmp_path, 'out_soil.tif')
    rasterized = rasterize_soils(geojson_path, raster_path, out_soil_path)
    
    assert np.all(rasterized == 4), "Dual groups should be treated conservatively (C/D -> 4)"

def test_missing_hydrologic_group_field(tmp_path):
    raster_path = os.path.join(tmp_path, 'template.tif')
    create_mock_raster(raster_path)
    
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    gdf = gpd.GeoDataFrame({'other_field': ['value'], 'geometry': [poly]}, crs='EPSG:32610')
    
    geojson_path = os.path.join(tmp_path, 'soils.geojson')
    gdf.to_file(geojson_path, driver='GeoJSON')
    
    out_soil_path = os.path.join(tmp_path, 'out_soil.tif')
    rasterized = rasterize_soils(geojson_path, raster_path, out_soil_path)
    
    assert np.all(rasterized == 2), "Missing hydrologic group should fallback to moderate value (2)"
