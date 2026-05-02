import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Setup DB path override
db_path = "test_sais_livestock.sqlite"
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

def test_livestock_health_observation(client):
    # 1. Post a poor condition check (BCS 2.0, Manure 2)
    payload = {
        "id": "ls-1",
        "farm_id": "local",
        "paddock_id": "paddock-1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bcs": 2.0,
        "manure_score": 2,
        "health_notes": "Thin animals"
    }
    r = client.post("/api/livestock/observations", json=payload)
    assert r.status_code == 200
    
    # 2. Verify LivestockConditionCard status is 'watch'
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    health_cards = [c for c in cards if c["card_type"] == "LivestockConditionCard"]
    assert len(health_cards) == 1
    assert health_cards[0]["status"] == "watch"
    assert any("BCS is below optimal" in e for e in health_cards[0]["evidence"])

def test_heat_stress_alert(client):
    # THI = (1.8 * T + 32) - (0.55 - 0.0055 * RH) * (1.8 * T - 26)
    # If T=35, RH=80:
    # (1.8*35+32) = 95
    # (0.55 - 0.0055*80) = 0.55 - 0.44 = 0.11
    # (1.8*35-26) = 63-26 = 37
    # THI = 95 - 0.11 * 37 = 95 - 4.07 = 90.93 (Severe Stress / Alert)
    
    # 1. Post weather observations
    now = datetime.now(timezone.utc).isoformat()
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "st-1", "farm_id": "local",
        "timestamp": now, "measurement_id": "weather.air_temperature", "layer": "Weather", "value": 35.0
    })
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "st-2", "farm_id": "local",
        "timestamp": now, "measurement_id": "weather.relative_humidity", "layer": "Weather", "value": 80.0
    })
    
    # 2. Trigger via observation (main.py triggers both health/heat on ls observation)
    client.post("/api/livestock/observations", json={
        "id": "ls-trigger", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": now, "bcs": 5.0
    })
    
    # 3. Verify status is 'alert'
    r = client.get("/api/cards")
    heat_cards = [c for c in r.json()["cards"] if c["card_type"] == "HeatStressCard"]
    assert len(heat_cards) == 1
    assert heat_cards[0]["status"] == "alert"
    assert any("Calculated THI: 90.9" in e for e in heat_cards[0]["evidence"])

def test_livestock_insufficient_data(client):
    # No observations yet
    from farm_twin.graph import FarmGraph
    from farm_twin.cards import generate_livestock_condition_card, generate_heat_stress_card
    
    os.environ["SAIS_DB_PATH"] = "test_ls_insufficient.sqlite"
    if os.path.exists("test_ls_insufficient.sqlite"): os.remove("test_ls_insufficient.sqlite")
    graph = get_graph()
    
    generate_livestock_condition_card(graph, "local", "paddock-1")
    generate_heat_stress_card(graph, "local", "paddock-1")
    
    cursor = graph.storage.conn.cursor()
    cursor.execute("SELECT status FROM cards WHERE card_type = 'LivestockConditionCard'")
    assert cursor.fetchone()[0] == "insufficient_data"
    
    cursor.execute("SELECT status FROM cards WHERE card_type = 'HeatStressCard'")
    assert cursor.fetchone()[0] == "insufficient_data"
