import os
import json
import pytest
from farm_twin.graph import FarmGraph
from farm_twin.ingest_observation import ingest_sensor_observation

def test_multiple_sensors_same_measurement(tmp_path):
    graph = FarmGraph()
    
    obs1 = {
        "schema": "sais.observation.v1",
        "node_id": "sensor-A",
        "farm_id": "local",
        "timestamp": "2026-05-01T10:00:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.20,
        "source": {"type": "sensor"}
    }
    
    obs2 = {
        "schema": "sais.observation.v1",
        "node_id": "sensor-B",
        "farm_id": "local",
        "timestamp": "2026-05-01T10:05:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.22,
        "source": {"type": "sensor"}
    }
    
    # Write to temp files
    path1 = os.path.join(tmp_path, "obs1.json")
    path2 = os.path.join(tmp_path, "obs2.json")
    with open(path1, 'w') as f: json.dump(obs1, f)
    with open(path2, 'w') as f: json.dump(obs2, f)
        
    ingest_sensor_observation(graph, path1)
    ingest_sensor_observation(graph, path2)
    
    # Both sensors should have a MEASURES edge to the same measurement node
    edges_A = graph.get_edges(source_id="sensor-A", edge_type="MEASURES")
    assert any(e["target_id"] == "soil.moisture.vwc" for e in edges_A)
    
    edges_B = graph.get_edges(source_id="sensor-B", edge_type="MEASURES")
    assert any(e["target_id"] == "soil.moisture.vwc" for e in edges_B)
