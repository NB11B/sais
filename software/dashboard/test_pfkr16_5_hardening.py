import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

# Setup DB path override
db_path = "test_sais_hardening.sqlite"
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
    paddock = Paddock(id="paddock-1", field_id="field-a", name="Paddock 1", rest_target_days=45)
    graph.add_node(farm)
    graph.add_node(paddock)
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_grazing_readiness_marginal_forage(client):
    # 1. Paddock has rested for 100 days (Target: 45)
    started_at = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-old", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": started_at, 
        "ended_at": (datetime.now(timezone.utc) - timedelta(days=99)).isoformat(),
        "animal_count": 100
    })
    
    # 2. But forage mass is low (1000 kg/ha)
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-low", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": now, "forage_mass_kg_ha": 1000.0
    })
    
    # 3. Check card - should be 'watch' (marginal), not 'ok'
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    gr_card = [c for c in cards if c["card_type"] == "GrazingReadinessCard"][0]
    
    assert gr_card["status"] == "watch"
    assert "forage supply is marginal" in gr_card["farmer_meaning"]

def test_forage_stale_detection(client):
    # 1. Post a plant reading from 10 days ago
    stale_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-stale", "farm_id": "local",
        "paddock_id": "paddock-1", "timestamp": stale_time, "forage_mass_kg_ha": 2500.0
    })
    
    # 2. Generate card
    graph = get_graph()
    from farm_twin.cards import generate_forage_balance_card
    generate_forage_balance_card(graph, "local", "paddock-1")
    
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    fb_card = [c for c in cards if c["card_type"] == "ForageBalanceCard"][0]
    
    assert fb_card["status"] == "stale_data"
    assert "New check required" in fb_card["evidence"][-1]

def test_paddock_area_missing_insufficient_data(client):
    # 1. Create a paddock WITHOUT boundary_geojson (so area is unknown)
    graph = get_graph()
    graph.add_node(Paddock(id="paddock-no-gis", field_id="field-a", name="No GIS"))
    
    # 2. Post plant observation
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/plant/observations", json={
        "schema": "sais.plant_observation.v1", "id": "pl-area", "farm_id": "local",
        "paddock_id": "paddock-no-gis", "timestamp": now, "forage_mass_kg_ha": 2000.0
    })
    
    # 3. Check card
    r = client.get("/api/cards")
    fb_card = [c for c in r.json()["cards"] if c["card_type"] == "ForageBalanceCard" and c["location"]["paddock_id"] == "paddock-no-gis"][0]
    
    assert fb_card["status"] == "insufficient_data"
    assert "Missing GIS boundary" in fb_card["evidence"][-1]
