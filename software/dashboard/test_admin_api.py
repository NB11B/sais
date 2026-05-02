import pytest
from fastapi.testclient import TestClient
import os
import sqlite3
import json

# Setup DB path override BEFORE importing main
db_path = "test_sais_admin.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm, Field, ManagementZone

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize schema
    graph = get_graph()
    graph.storage.conn.close()
    
    yield
    
    # Teardown
    if os.path.exists(db_path):
        os.remove(db_path)

def test_admin_api_workflow(client):
    # 1. Farm
    farm_geojson = {"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]}
    r = client.put("/api/farm/profile", json={
        "id": "farm-1",
        "name": "Test Farm",
        "boundary_geojson": farm_geojson
    })
    assert r.status_code == 200

    # 2. Field
    r = client.post("/api/farm/fields", json={
        "id": "field-1",
        "farm_id": "farm-1",
        "name": "Test Field"
    })
    assert r.status_code == 200

    # 3. Zone
    r = client.post("/api/farm/zones", json={
        "id": "zone-1",
        "field_id": "field-1",
        "name": "Test Zone"
    })
    assert r.status_code == 200

    # 4. Paddock
    r = client.post("/api/farm/paddocks", json={
        "id": "paddock-1",
        "field_id": "field-1",
        "name": "Test Paddock"
    })
    assert r.status_code == 200

    # 5. Sensor Node
    r = client.post("/api/farm/sensor-nodes", json={
        "id": "sensor-1",
        "farm_id": "farm-1",
        "node_type": "moisture",
        "zone_id": "zone-1",
        "location": {"lat": 1.0, "lng": 2.0}
    })
    assert r.status_code == 200

    # 6. Verify invalid parent rejects request
    r = client.post("/api/farm/fields", json={
        "id": "field-2",
        "farm_id": "nonexistent-farm",
        "name": "Bad Field"
    })
    assert r.status_code == 400

    # 7. Verify path ID mismatch rejects request
    r = client.put("/api/farm/fields/mismatch-path", json={
        "id": "field-1",
        "farm_id": "farm-1",
        "name": "Mismatched Field"
    })
    assert r.status_code == 400

    # 8. Verify boundary_geojson and location persist in /api/graph
    r = client.get("/api/graph")
    assert r.status_code == 200
    data = r.json()
    
    nodes = {n["id"]: n for n in data["nodes"]}
    edges = data["edges"]
    
    assert nodes["farm-1"]["payload"]["boundary_geojson"] == farm_geojson
    assert nodes["sensor-1"]["payload"]["location"] == {"lat": 1.0, "lng": 2.0}
    
    # Check edges
    contains_edges = [(e["source"], e["target"]) for e in edges if e["type"] == "CONTAINS"]
    deployed_edges = [(e["source"], e["target"]) for e in edges if e["type"] == "DEPLOYED_IN"]
    
    assert ("farm-1", "field-1") in contains_edges
    assert ("field-1", "zone-1") in contains_edges
    assert ("field-1", "paddock-1") in contains_edges
    assert ("sensor-1", "zone-1") in deployed_edges
