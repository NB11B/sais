import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Setup DB path override
db_path = "test_sais_plant.sqlite"
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
    # Paddock with area placeholder or real area
    paddock = Paddock(
        id="paddock-1", 
        field_id="field-a", 
        name="Paddock 1",
        boundary_geojson={"type": "Polygon", "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]}
    )
    graph.add_node(farm)
    graph.add_node(paddock)
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_forage_balance_logic(client):
    # 1. Post a grazing event to create demand (100 animals)
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-1", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": now, "animal_count": 100
    })
    
    # 2. Post a high forage mass reading (3000 kg DM/ha)
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-1", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": now, "forage_mass_kg_ha": 3000.0
    })
    
    # 3. Check card
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    fb_card = [c for c in cards if c["card_type"] == "ForageBalanceCard"][0]
    
    # Supply: 3000, Residual: 1200, Area: 10ha => 18000 kg usable
    # Demand: 100 animals * 18kg = 1800kg/day
    # Days: 10.0
    assert fb_card["status"] == "ok"
    assert "10.0" in fb_card["observation"]

def test_forage_shortage_alert(client):
    now = datetime.now(timezone.utc).isoformat()
    # 1. High demand
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-1", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": now, "animal_count": 500
    })
    
    # 2. Low supply (1300 kg/ha - barely above 1200 residual)
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-2", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": now, "forage_mass_kg_ha": 1300.0
    })
    
    r = client.get("/api/cards")
    fb_card = [c for c in r.json()["cards"] if c["card_type"] == "ForageBalanceCard"][0]
    # Usable supply: 100 * 10 = 1000kg
    # Demand: 500 * 18 = 9000kg/day
    # Days: ~0.1
    assert fb_card["status"] == "alert"

def test_plant_recovery_quality(client):
    now = datetime.now(timezone.utc).isoformat()
    # Post a low recovery score
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-3", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": now, "recovery_score": 1, "height_cm": 5
    })
    
    r = client.get("/api/cards")
    pr_card = [c for c in r.json()["cards"] if c["card_type"] == "PlantRecoveryCard"][0]
    assert pr_card["status"] == "action"
    assert "Regrowth height: 5.0 cm" in pr_card["context"]
