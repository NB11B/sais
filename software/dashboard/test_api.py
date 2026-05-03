import pytest
import os
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Setup DB path override and admin token BEFORE importing main
db_path = "test_sais_api.sqlite"
os.environ["SAIS_DB_PATH"] = db_path
os.environ["SAIS_ADMIN_TOKEN"] = "test-api-token"

from main import app, get_graph
from farm_twin.models import Farm, Field, ManagementZone
from auth import ADMIN_TOKEN

client = TestClient(app)
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize schema and seed data
    graph = get_graph()
    farm = Farm(id="local", name="Test Farm")
    field = Field(id="field-a", farm_id="local", name="Test Field")
    zone = ManagementZone(id="zone-a1", field_id="field-a", name="Test Zone")
    
    graph.add_node(farm)
    graph.add_node(field)
    graph.add_node(zone)
    graph.add_edge(farm.id, "CONTAINS", field.id)
    graph.add_edge(field.id, "CONTAINS", zone.id)
    # Add runoff_risk layer to trigger 'watch' status in get_zone_water_risk_summary
    graph.add_edge(farm.id, "HAS_LAYER", "local:runoff_risk")
    
    # WP19: Node must be accepted to be trusted
    graph.storage.update_node_registry(node_id="live-sensor-1", status="accepted", farm_id="local")
    
    graph.storage.conn.close()
    
    yield
    
    # Teardown
    if os.path.exists(db_path):
        os.remove(db_path)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "SAIS | Command Dashboard" in response.text

def test_read_cards():
    response = client.get("/api/cards")
    assert response.status_code == 200
    assert "cards" in response.json()

def test_read_observations():
    response = client.get("/api/observations")
    assert response.status_code == 200
    assert "observations" in response.json()

def test_read_graph():
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "counts" in data

def test_post_observation():
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "live-sensor-1",
        "farm_id": "local",
        "field_id": "field-a",
        "zone_id": "zone-a1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.10,
        "source": {"type": "sensor", "depth_cm": 30}
    }
    response = client.post("/api/observations", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get("/api/cards")
    cards = response.json()["cards"]
    assert len(cards) > 0
    # Find the water_retention card specifically (ranch_health may also be generated)
    water_cards = [c for c in cards if c.get("card_type") == "WaterRetentionCard"]
    assert len(water_cards) > 0, f"No WaterRetentionCard found. Card types: {[c.get('card_type') for c in cards]}"
    # It should have updated to watch because moisture is 0.10 < 0.25 AND runoff_risk layer is present
    assert water_cards[0]["status"] == "watch"
