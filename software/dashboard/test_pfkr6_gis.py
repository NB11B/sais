import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Setup DB path override
db_path = "test_sais_gis.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_teardown(request):
    test_db = f"test_{request.node.name}.sqlite"
    os.environ["SAIS_DB_PATH"] = test_db
    
    if os.path.exists(test_db):
        os.remove(test_db)
    
    graph = get_graph()
    farm = Farm(id="local", name="Test Farm")
    graph.add_node(farm)
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_register_infrastructure_point(client):
    # 1. Register a Gate (Point)
    client.post("/api/infrastructure/asset", json={
        "id": "gate-1",
        "farm_id": "local",
        "asset_type": "Gate",
        "name": "Front Gate",
        "status": "ok",
        "location_geojson": {"type": "Point", "coordinates": [-104.5, 40.2]}
    })
    
    # 2. Verify graph node
    r = client.get("/api/graph")
    nodes = r.json()["nodes"]
    gate_node = [n for n in nodes if n["id"] == "gate-1"][0]
    
    assert "InfrastructureAsset" in gate_node["labels"]
    assert gate_node["payload"]["status"] == "ok"
    assert gate_node["payload"]["location_geojson"]["type"] == "Point"

def test_register_infrastructure_linestring(client):
    # 1. Register a Fence (LineString)
    client.post("/api/infrastructure/asset", json={
        "id": "fence-1",
        "farm_id": "local",
        "asset_type": "Fence",
        "name": "Boundary Fence",
        "status": "ok",
        "location_geojson": {
            "type": "LineString", 
            "coordinates": [[-104.5, 40.2], [-104.51, 40.21]]
        }
    })
    
    # 2. Verify graph node
    r = client.get("/api/graph")
    nodes = r.json()["nodes"]
    fence_node = [n for n in nodes if n["id"] == "fence-1"][0]
    
    assert "InfrastructureAsset" in fence_node["labels"]
    assert fence_node["payload"]["location_geojson"]["type"] == "LineString"

def test_dynamic_status_update(client):
    # 1. Register asset
    client.post("/api/infrastructure/asset", json={
        "id": "gate-alert",
        "farm_id": "local",
        "asset_type": "Gate",
        "status": "ok",
        "location_geojson": {"type": "Point", "coordinates": [-104.5, 40.2]}
    })
    
    # 2. Update status to 'open'
    client.post("/api/infrastructure/status", json={
        "id": "gate-alert",
        "farm_id": "local",
        "asset_type": "Gate",
        "status": "open"
    })
    
    # 3. Verify graph reflects status change for GIS rendering
    r = client.get("/api/graph")
    gate_node = [n for n in r.json()["nodes"] if n["id"] == "gate-alert"][0]
    assert gate_node["payload"]["status"] == "open"
