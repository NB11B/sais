import os
import sys
import pytest
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
import geopandas as gpd
from shapely.geometry import Polygon

sais_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(sais_root, 'scripts', 'geospatial_ingest'))
sys.path.insert(0, os.path.join(sais_root, 'software', 'farm_twin'))

from pipeline import run_pipeline
from farm_twin.graph import FarmGraph
from farm_twin.ingest_geospatial import ingest_geospatial_manifest
from farm_twin.ingest_observation import ingest_farm_profile, ingest_sensor_observation
from farm_twin.cards import generate_water_retention_card

def create_mock_data(input_dir):
    dem_path = os.path.join(input_dir, 'dem.tif')
    soil_path = os.path.join(input_dir, 'soils.geojson')
    prof_path = os.path.join(input_dir, 'farm_profile.json')
    obs_path = os.path.join(input_dir, 'obs.json')
    
    os.makedirs(input_dir, exist_ok=True)
    
    dem = np.zeros((10, 10), dtype=np.float32)
    for i in range(10): dem[:, i] = 100 - i * 10
    transform = from_origin(0, 100, 10, 10)
    with rasterio.open(
        dem_path, 'w', driver='GTiff', height=10, width=10, count=1,
        dtype=dem.dtype, crs='EPSG:32610', transform=transform, nodata=-9999
    ) as dst:
        dst.write(dem, 1)
        
    poly = Polygon([(0, 0), (100, 0), (100, 100), (0, 100)])
    gdf = gpd.GeoDataFrame({'hydrologic_group': ['C/D'], 'geometry': [poly]}, crs='EPSG:32610')
    gdf.to_file(soil_path, driver='GeoJSON')
    
    prof = {"farm_id": "local", "name": "E2E Farm", "fields": [{"id": "f1", "name": "F1", "zones": [{"id": "z1", "name": "Z1"}]}]}
    with open(prof_path, 'w') as f: json.dump(prof, f)
    
    obs = {
        "schema": "sais.observation.v1",
        "node_id": "s1",
        "farm_id": "local",
        "zone_id": "z1",
        "timestamp": "2026-05-01T12:00:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.22,
        "source": {"type": "sensor"}
    }
    with open(obs_path, 'w') as f: json.dump(obs, f)
    
    return dem_path, soil_path, prof_path, obs_path

def test_full_sais_stack(tmp_path):
    input_dir = os.path.join(tmp_path, "input")
    output_dir = os.path.join(tmp_path, "output")
    db_path = os.path.join(tmp_path, "sais.sqlite")
    
    dem_path, soil_path, prof_path, obs_path = create_mock_data(input_dir)
    
    run_pipeline(input_dir, output_dir)
    
    graph = FarmGraph(db_path)
    
    ingest_farm_profile(graph, prof_path)
    
    manifest_path = os.path.join(output_dir, 'manifest.json')
    ingest_geospatial_manifest(graph, manifest_path)
    
    ingest_sensor_observation(graph, obs_path)
    
    card = generate_water_retention_card(graph, "local", "f1", "z1")
    
    assert card["status"] == "watch"
    assert "runoff_risk layer available for farm" in card["evidence"]
    
    graph.storage.conn.close()
    del graph
    
    graph2 = FarmGraph(db_path)
    assert graph2.get_node("z1") is not None
    assert graph2.get_node("local:runoff_risk") is not None
    
    cursor = graph2.storage.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cards")
    assert cursor.fetchone()[0] == 1
    
    graph2.storage.conn.close()
