import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

# Setup DB path override
db_path = "test_sais_water.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm, Field, Paddock

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
    paddock = Paddock(id="paddock-1", field_id="field-a", name="Paddock 1")
    graph.add_node(farm)
    graph.add_node(paddock)
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_water_system_card_logic(client):
    # 1. Post a low tank level (25% = 'action')
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "tank-1", "farm_id": "local",
        "timestamp": now, "measurement_id": "water.tank.level_percent", "layer": "Water", "value": 25.0
    })
    
    # 2. Trigger via some event to refresh cards (we'll manually trigger the card gen for the test)
    graph = get_graph()
    from farm_twin.cards import generate_water_system_card
    generate_water_system_card(graph, "local")
    
    r = client.get("/api/cards")
    card = [c for c in r.json()["cards"] if c["card_type"] == "WaterSystemCard"][0]
    assert card["status"] == "action"
    assert "Tank tank-1: 25.0%" in card["evidence"]

def test_water_demand_fusion(client):
    # If THI is high AND herd is present, demand warning should trigger
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Active Grazing
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-1", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": now, "animal_count": 100
    })
    
    # 2. High THI (35C, 80% RH)
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "st-1", "farm_id": "local",
        "timestamp": now, "measurement_id": "weather.air_temperature", "layer": "Weather", "value": 35.0
    })
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "st-2", "farm_id": "local",
        "timestamp": now, "measurement_id": "weather.relative_humidity", "layer": "Weather", "value": 80.0
    })
    
    # 3. Check demand index via internal query (or card if we added it)
    # The WaterSystemCard evidence should show demand factors if we update it
    # For now, let's just check if the WaterSystemCard exists and carries the status.
    graph = get_graph()
    from farm_twin.queries import get_water_demand_index
    demand = get_water_demand_index(graph, "local", "paddock-1")
    assert demand["status"] == "watch"
    assert "Active grazing: 100 animals" in demand["evidence"]

def test_stale_sensor_detection(client):
    # 1. Post a reading from 10 hours ago
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "tank-1", "farm_id": "local",
        "timestamp": stale_time, "measurement_id": "water.tank.level_percent", "layer": "Water", "value": 80.0
    })
    
    # 2. Generate health card
    graph = get_graph()
    from farm_twin.cards import generate_water_source_health_card
    generate_water_source_health_card(graph, "local")
    
    r = client.get("/api/cards")
    health_card = [c for c in r.json()["cards"] if c["card_type"] == "WaterSourceHealthCard"][0]
    assert health_card["status"] == "stale_data"
    assert "Last reading: 10.0h ago" in health_card["evidence"]
