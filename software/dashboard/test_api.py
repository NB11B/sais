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
