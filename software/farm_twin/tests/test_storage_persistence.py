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

def test_sqlite_persistence(example_paths, tmp_path):
    db_path = os.path.join(tmp_path, "test_farm.sqlite")
    
    # 1. Create graph and ingest data
    graph1 = FarmGraph(db_path)
    ingest_farm_profile(graph1, example_paths["profile"])
    ingest_geospatial_manifest(graph1, example_paths["manifest"])
    ingest_sensor_observation(graph1, example_paths["observation"])
    generate_water_retention_card(graph1, "local", "field-a", "zone-a1")
    
    # Verify it's there
    assert graph1.get_node("zone-a1") is not None
    
    # Close connection explicitly
    graph1.storage.conn.close()
    del graph1
    
    # 2. Reopen graph
    graph2 = FarmGraph(db_path)
    
    # 3. Query same nodes/edges/cards
    zone = graph2.get_node("zone-a1")
    assert zone is not None
    assert zone["payload"]["name"] == "North Slope"
    
    edges = graph2.get_edges(source_id="local", edge_type="CONTAINS")
    assert any(e["target_id"] == "field-a" for e in edges)
    
    # Check observation
    cursor = graph2.storage.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM observations")
    assert cursor.fetchone()[0] == 1
    
    # Check card
    cursor.execute("SELECT COUNT(*) FROM cards")
    assert cursor.fetchone()[0] == 1
    
    graph2.storage.conn.close()
