from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "SAIS | Sovereign Ag-Infrastructure Stack" in response.text

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
        "zone_id": "zone-a1",
        "timestamp": "2026-05-02T12:00:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.10,
        "source": {"type": "sensor", "depth_cm": 30}
    }
    response = client.post("/api/observations", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    response = client.get("/api/cards")
    cards = response.json()["cards"]
    assert len(cards) > 0
    latest = cards[0]
    # It should have updated to watch because moisture is < 0.25
    assert latest["status"] in ["watch", "ok_with_warning"]
