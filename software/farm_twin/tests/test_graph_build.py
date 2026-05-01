import os
import pytest
from farm_twin.graph import FarmGraph
from farm_twin.ingest_geospatial import ingest_geospatial_manifest
from farm_twin.ingest_observation import ingest_farm_profile, ingest_sensor_observation
from farm_twin.cards import generate_water_retention_card

@pytest.fixture
def example_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
    return {
        "profile": os.path.join(base_dir, 'farm_profile.example.json'),
        "manifest": os.path.join(base_dir, 'geospatial_manifest.example.json'),
        "observation": os.path.join(base_dir, 'observation.example.json')
    }

@pytest.fixture
def graph():
    # Use in-memory SQLite database
    return FarmGraph(":memory:")

def test_farm_profile_builds_graph(graph, example_paths):
    farm_id = ingest_farm_profile(graph, example_paths["profile"])
    
    assert farm_id == "local"
    assert graph.get_node("local") is not None
    assert graph.get_node("field-a") is not None
    assert graph.get_node("zone-a1") is not None
    
    # Check edges
    edges = graph.get_edges(source_id="local", edge_type="CONTAINS")
    assert any(e["target_id"] == "field-a" for e in edges)

def test_manifest_adds_geospatial_layers(graph, example_paths):
    layers = ingest_geospatial_manifest(graph, example_paths["manifest"])
    
    assert "runoff_risk" in layers
    
    node = graph.get_node("local:runoff_risk")
    assert node is not None
    assert node["type"] == "GeospatialLayer"
    
    # Verify link to ontology
    edges = graph.get_edges(source_id="local:runoff_risk", edge_type="INFORMS")
    assert any(e["target_id"] == "ontology:WaterCycle" for e in edges)

def test_observation_links_to_zone_and_layer(graph, example_paths):
    obs_id = ingest_sensor_observation(graph, example_paths["observation"])
    
    # Verify observation was persisted
    cursor = graph.storage.conn.cursor()
    cursor.execute("SELECT * FROM observations WHERE id = ?", (obs_id,))
    assert cursor.fetchone() is not None
    
    # Verify sensor node was created and deployed
    sensor = graph.get_node("node-soil-001")
    assert sensor is not None
    edges = graph.get_edges(source_id="node-soil-001", edge_type="DEPLOYED_IN")
    assert any(e["target_id"] == "zone-a1" for e in edges)
    
def test_water_retention_card_generates_from_risk_and_moisture(graph, example_paths):
    # Setup state
    ingest_farm_profile(graph, example_paths["profile"])
    ingest_geospatial_manifest(graph, example_paths["manifest"])
    ingest_sensor_observation(graph, example_paths["observation"])
    
    # The observation value is 0.23, which is < 0.25, and there is a runoff_risk layer
    card = generate_water_retention_card(graph, "local", "field-a", "zone-a1")
    
    assert card["card_type"] == "WaterRetentionCard"
    assert card["status"] == "watch"
    assert "runoff_risk layer exists" in card["evidence"]
    assert "soil moisture at 30cm is 0.23" in card["evidence"]

def test_missing_geospatial_layer_degrades_gracefully(graph, example_paths):
    # Setup state WITHOUT manifest (so no runoff risk layer)
    ingest_farm_profile(graph, example_paths["profile"])
    ingest_sensor_observation(graph, example_paths["observation"])
    
    # The card should generate, but status should be 'ok' because we don't have enough risk evidence
    card = generate_water_retention_card(graph, "local", "field-a", "zone-a1")
    
    assert card["status"] == "ok"
    assert "runoff_risk layer exists" not in card["evidence"]
