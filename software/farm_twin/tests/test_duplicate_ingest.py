import os
import pytest
from farm_twin.graph import FarmGraph
from farm_twin.ingest_geospatial import ingest_geospatial_manifest
from farm_twin.ingest_observation import ingest_farm_profile

@pytest.fixture
def example_paths():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
    return {
        "profile": os.path.join(base_dir, 'farm_profile.example.json'),
        "manifest": os.path.join(base_dir, 'geospatial_manifest.example.json')
    }

def test_duplicate_farm_profile_ingest(example_paths):
    graph = FarmGraph()
    # Ingest twice
    ingest_farm_profile(graph, example_paths["profile"])
    ingest_farm_profile(graph, example_paths["profile"])
    
    # Should not duplicate edges
    edges = graph.get_edges(source_id="local", edge_type="CONTAINS")
    assert len(edges) == 1, "Duplicate ingest should be idempotent and not create duplicate edges"

def test_duplicate_manifest_ingest(example_paths):
    graph = FarmGraph()
    # Ingest twice
    ingest_geospatial_manifest(graph, example_paths["manifest"])
    ingest_geospatial_manifest(graph, example_paths["manifest"])
    
    # Should not duplicate layers
    edges = graph.get_edges(source_id="local", edge_type="HAS_LAYER")
    # In the example manifest, there are 5 derived layers
    assert len(edges) == 5, "Duplicate manifest ingest should be idempotent"
