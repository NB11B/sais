import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

# Setup DB path override BEFORE importing main
db_path = "test_sais_grazing.sqlite"
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
    field = Field(id="field-a", farm_id="local", name="North Field")
    # Paddock with 30-day rest target
    paddock = Paddock(id="paddock-1", field_id="field-a", name="Paddock 1", rest_target_days=30)
    
    graph.add_node(farm)
    graph.add_node(field)
    graph.add_node(paddock)
    graph.add_edge(farm.id, "CONTAINS", field.id)
    graph.add_edge(field.id, "CONTAINS", paddock.id)
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_log_grazing_event(client):
    # 1. Log a grazing event that happened 10 days ago
    ten_days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    payload = {
        "schema": "sais.grazing_event.v1",
        "event_id": "event-1",
        "farm_id": "local",
        "field_id": "field-a",
        "paddock_id": "paddock-1",
        "started_at": ten_days_ago,
        "animal_count": 50,
        "notes": "Test grazing"
    }
    r = client.post("/api/grazing/events", json=payload)
    assert r.status_code == 200
    
    # 2. Verify GrazingReadinessCard status is 'not_ready' (10 < 30)
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    grazing_cards = [c for c in cards if c["card_type"] == "GrazingReadinessCard"]
    assert len(grazing_cards) == 1
    assert grazing_cards[0]["status"] == "action"
    assert "Days since last graze: 10" in grazing_cards[0]["evidence"]

def test_grazing_ready_state(client):
    # 1. Log an event 40 days ago (40 > 30 target)
    forty_days_ago = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    payload = {
        "schema": "sais.grazing_event.v1",
        "event_id": "event-2",
        "farm_id": "local",
        "field_id": "field-a",
        "paddock_id": "paddock-1",
        "started_at": forty_days_ago,
        "animal_count": 50,
        "notes": "Old grazing"
    }
    client.post("/api/grazing/events", json=payload)
    
    # 2. Verify status is 'ok'
    r = client.get("/api/cards")
    card = [c for c in r.json()["cards"] if c["card_type"] == "GrazingReadinessCard"][0]
    assert card["status"] == "ok"
    assert "Paddock appears recovered" in card["farmer_meaning"]

def test_grazing_watch_state_heat(client):
    # 1. Log event 40 days ago
    forty_days_ago = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-3", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": forty_days_ago
    })
    
    # 2. Add high heat weather observation (38C)
    client.post("/api/observations", json={
        "schema": "sais.observation.v1", "node_id": "weather-1", "farm_id": "local",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurement_id": "weather.air_temperature", "layer": "Weather", "value": 38.0
    })
    
    # Trigger card update (normally happens on event post, or periodic)
    # We'll post a dummy event to re-trigger for this paddock in the test
    client.post("/api/grazing/events", json={
        "schema": "sais.grazing_event.v1", "event_id": "ev-trigger", "farm_id": "local",
        "field_id": "field-a", "paddock_id": "paddock-1", "started_at": forty_days_ago
    })
    
    # 3. Verify status is 'watch' due to heat stress
    r = client.get("/api/cards")
    card = [c for c in r.json()["cards"] if c["card_type"] == "GrazingReadinessCard"][0]
    assert card["status"] == "watch"
    assert any("High heat stress detected" in e for e in card["evidence"])

def test_insufficient_data(client):
    # 1. Post weather to trigger card engine (optional, but good to test)
    # If no grazing event, should be insufficient_data
    # In main.py, cards are generated on grazing event post. 
    # Let's test the query directly via a trigger or just check the state.
    
    from farm_twin.graph import FarmGraph
    from farm_twin.cards import generate_grazing_readiness_card
    
    os.environ["SAIS_DB_PATH"] = "test_insufficient.sqlite"
    if os.path.exists("test_insufficient.sqlite"): os.remove("test_insufficient.sqlite")
    graph = get_graph()
    graph.add_node(Paddock(id="paddock-1", field_id="field-a", name="Paddock 1", rest_target_days=30))
    # Paddock with NO history
    generate_grazing_readiness_card(graph, "local", "paddock-1")
    
    cursor = graph.storage.conn.cursor()
    cursor.execute("SELECT payload_json FROM cards WHERE card_type = 'GrazingReadinessCard'")
    card = json.loads(cursor.fetchone()[0])
    assert card["status"] == "insufficient_data"
    assert any("No grazing history recorded" in e for e in card["evidence"])
