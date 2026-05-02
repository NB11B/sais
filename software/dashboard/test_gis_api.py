import pytest
import os
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_get_gis_assets(client):
    r = client.get("/api/gis/assets")
    assert r.status_code == 200
    data = r.json()
    assert "assets" in data
    assert len(data["assets"]) > 0
    
    asset = data["assets"][0]
    assert "id" in asset
    assert "style" in asset
    assert "color" in asset["style"]

def test_get_gis_data(client):
    # Get ID from asset list
    r = client.get("/api/gis/assets")
    asset_id = r.json()["assets"][0]["id"]
    
    r = client.get(f"/api/gis/data/{asset_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data

def test_get_missing_gis_data(client):
    r = client.get("/api/gis/data/non-existent")
    assert r.status_code == 404
