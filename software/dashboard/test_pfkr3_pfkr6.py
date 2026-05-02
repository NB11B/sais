import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Setup DB path override
db_path = "test_sais_soil_infra.sqlite"
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

def test_soil_infiltration_logic(client):
    now = datetime.now(timezone.utc).isoformat()
    # 1. Post a weak infiltration rate (10 mm/hr)
    client.post("/api/soil/observations", json={
        "schema": "sais.soil_observation.v1", "id": "soil-1", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": now, "infiltration_mm_hr": 10.0
    })
    
    # 2. Check card
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    soil_card = [c for c in cards if c["card_type"] == "SoilFunctionCard"][0]
    
    assert soil_card["status"] == "action"
    assert "Soil capture is weak" in soil_card["observation"]

def test_infrastructure_alert_logic(client):
    # 1. Post an open gate status
    client.post("/api/infrastructure/status", json={
        "id": "gate-1", "farm_id": "local", "asset_type": "Gate", "status": "open"
    })
    
    # 2. Check card
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    infra_card = [c for c in cards if c["card_type"] == "InfrastructureAlertCard"][0]
    
    assert infra_card["status"] == "alert"
    assert "Gate 'gate-1' is open" in infra_card["evidence"][0]

def test_infrastructure_secure_logic(client):
    # 1. Post an OK status
    client.post("/api/infrastructure/status", json={
        "id": "fence-1", "farm_id": "local", "asset_type": "Fence", "status": "ok"
    })
    
    # 2. Check card - should be 'ok' status, not alert
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    infra_card = [c for c in cards if c["card_type"] == "InfrastructureAlertCard"][0]
    
    assert infra_card["status"] == "ok"
    assert "All assets secure" in infra_card["observation"]
