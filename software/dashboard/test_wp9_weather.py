import pytest
import os
from fastapi.testclient import TestClient

# Setup DB path override BEFORE importing main
db_path = "test_sais_wp9.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm, Field, ManagementZone

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize schema and seed data
    graph = get_graph()
    farm = Farm(id="local", name="Test Farm")
    field = Field(id="field-1", farm_id="local", name="Test Field")
    zone = ManagementZone(id="zone-1", field_id="field-1", name="Test Zone")
    
    graph.add_node(farm)
    graph.add_node(field)
    graph.add_node(zone)
    graph.add_edge(farm.id, "CONTAINS", field.id)
    graph.add_edge(field.id, "CONTAINS", zone.id)
    
    graph.storage.conn.close()
    
    yield
    
    # Teardown
    if os.path.exists(db_path):
        os.remove(db_path)

def test_source_and_layer_registries(client):
    # Check sources
    r = client.get("/api/sources")
    assert r.status_code == 200
    sources = r.json()["sources"]
    ids = [s["id"] for s in sources]
    assert "open_weather" in ids
    assert "direct_sensor" in ids

    # Check layers
    r = client.get("/api/layers")
    assert r.status_code == 200
    layers = r.json()["layers"]
    ids = [l["id"] for l in layers]
    assert "soil_moisture" in ids
    assert "rainfall" in ids

def test_weather_observation_ingest(client):
    # 1. Post weather observation (Rainfall)
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "weather-station-1",
        "farm_id": "local",
        "timestamp": "2026-05-02T14:00:00Z",
        "measurement_id": "weather.rainfall.hourly",
        "layer": "Weather",
        "value": 12.5,
        "unit": "mm",
        "source": {"type": "open_weather"}
    }
    r = client.post("/api/observations", json=payload)
    assert r.status_code == 200
    
    # 2. Verify WeatherContextCard exists
    r = client.get("/api/cards")
    assert r.status_code == 200
    cards = r.json()["cards"]
    weather_cards = [c for c in cards if c["card_type"] == "WeatherContextCard"]
    assert len(weather_cards) > 0
    assert "Rainfall detected (12.5mm)" in weather_cards[0]["observation"]
    assert weather_cards[0]["status"] == "action" # 12.5 > 10

def test_weather_impacts_water_retention(client):
    # 1. Post heavy rain
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "weather-station-1",
        "farm_id": "local",
        "zone_id": "zone-1", # Associate with zone for retention trigger
        "timestamp": "2026-05-02T15:00:00Z",
        "measurement_id": "weather.rainfall.hourly",
        "layer": "Weather",
        "value": 25.0,
        "unit": "mm",
        "source": {"type": "open_weather"}
    }
    r = client.post("/api/observations", json=payload)
    assert r.status_code == 200

    # 2. Check WaterRetentionCard evidence
    r = client.get("/api/cards")
    cards = r.json()["cards"]
    retention_cards = [c for c in cards if c["card_type"] == "WaterRetentionCard"]
    assert len(retention_cards) > 0
    assert any("recent rainfall detected: 25.0mm" in ev for ev in retention_cards[0]["evidence"])
    
def test_weather_registry_visibility(client):
    # 1. Post weather observation
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "weather-station-1",
        "farm_id": "local",
        "timestamp": "2026-05-02T16:00:00Z",
        "measurement_id": "weather.air_temperature",
        "layer": "Weather",
        "value": 22.0,
        "unit": "C",
        "source": {"type": "open_weather"}
    }
    client.post("/api/observations", json=payload)

    # 2. Verify weather observations are in the main list
    r = client.get("/api/observations")
    obs = r.json()["observations"]
    weather_obs = [o for o in obs if o["layer"] == "Weather"]
    assert len(weather_obs) > 0

    # 3. Verify weather station appears in farm profile
    r = client.get("/api/farm/profile")
    profile = r.json()
    sensors = [s for s in profile["SensorNode"] if s["id"] == "weather-station-1"]
    assert len(sensors) == 1
    assert sensors[0]["node_type"] == "open_weather"

