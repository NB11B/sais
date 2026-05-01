import os
import json
import pytest
from farm_twin.graph import FarmGraph
from farm_twin.ingest_geospatial import ingest_geospatial_manifest
from farm_twin.ingest_observation import ingest_farm_profile, ingest_sensor_observation
from farm_twin.queries import get_zone_water_risk_summary

@pytest.fixture
def base_graph(tmp_path):
    graph = FarmGraph()
    # Mock a base farm profile
    farm = {"farm_id": "local", "name": "Test Farm", "fields": [{"id": "field-1", "name": "F1", "zones": [{"id": "zone-1", "name": "Z1"}]}]}
    prof_path = os.path.join(tmp_path, "prof.json")
    with open(prof_path, 'w') as f: json.dump(farm, f)
    ingest_farm_profile(graph, prof_path)
    return graph

def _add_obs(graph, tmp_path, val, idx):
    obs = {
        "schema": "sais.observation.v1",
        "node_id": "s1",
        "farm_id": "local",
        "zone_id": "zone-1",
        "timestamp": f"2026-05-01T10:0{idx}:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": val,
        "source": {"type": "sensor"}
    }
    p = os.path.join(tmp_path, f"obs_{idx}.json")
    with open(p, 'w') as f: json.dump(obs, f)
    ingest_sensor_observation(graph, p)

def _add_manifest(graph, tmp_path):
    man = {
      "schema": "sais.geospatial_manifest.v1",
      "farm_id": "local",
      "derived_layers": {
        "runoff_risk": "runoff_risk.tif"
      }
    }
    p = os.path.join(tmp_path, "man.json")
    with open(p, 'w') as f: json.dump(man, f)
    ingest_geospatial_manifest(graph, p)

def test_card_runoff_and_0_23(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    _add_obs(base_graph, tmp_path, 0.23, 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "watch"

def test_card_runoff_and_0_25(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    _add_obs(base_graph, tmp_path, 0.25, 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "watch"

def test_card_runoff_and_0_30(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    _add_obs(base_graph, tmp_path, 0.30, 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "ok"

def test_card_no_runoff_and_low_moisture(base_graph, tmp_path):
    _add_obs(base_graph, tmp_path, 0.20, 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "ok_with_warning"

def test_card_runoff_and_missing_moisture(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    _add_obs(base_graph, tmp_path, None, 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "insufficient_data"

def test_card_runoff_and_invalid_moisture(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    _add_obs(base_graph, tmp_path, "broken", 1)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "invalid_data"

def test_card_no_observations(base_graph, tmp_path):
    _add_manifest(base_graph, tmp_path)
    summary = get_zone_water_risk_summary(base_graph, "local", "zone-1")
    assert summary["status"] == "insufficient_data"
