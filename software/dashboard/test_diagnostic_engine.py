import os
import json
os.environ["SAIS_ADMIN_TOKEN"] = "dev-admin-token"
os.environ["SAIS_ENV"] = "development"

import pytest
from datetime import datetime, timedelta, timezone
from farm_twin.graph import FarmGraph
from farm_twin.diagnostic_engine import FarmDiagnosticEngine, FarmSignal

import tempfile
import shutil

@pytest.fixture
def engine():
    db_dir = tempfile.mkdtemp()
    db_path = os.path.join(db_dir, "test_sais.sqlite")
    graph = FarmGraph(db_path)
    engine_instance = FarmDiagnosticEngine(graph)
    yield engine_instance
    # Ensure all connections are closed before deleting the directory (vital on Windows)
    graph.storage.conn.close()
    shutil.rmtree(db_dir)

def test_signal_collection_from_observations(engine):
    graph = engine.graph
    farm_id = "farm-1"
    node_id = "node-1"
    zone_id = "zone-A"
    
    # Add an observation
    now = datetime.now(timezone.utc).isoformat()
    graph.storage.conn.execute(
        "INSERT INTO observations (id, node_id, timestamp, farm_id, zone_id, measurement_id, value, layer, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("obs-1", node_id, now, farm_id, zone_id, "soil.moisture.vwc", 0.15, "SoilPhysics", '{"unit": "vwc", "confidence": "high"}')
    )
    
    signals = engine.collect_observation_signals(farm_id, None, zone_id, datetime.now(timezone.utc) - timedelta(hours=1))
    
    assert len(signals) == 1
    assert signals[0].name == "soil.moisture.vwc"
    assert signals[0].value == 0.15
    assert signals[0].domain == "soil" # Mapped by domain_from_measurement

def test_attention_aggregate_water_capture_gap(engine):
    # Setup signals for "Water capture gap"
    # Rule: ["low_soil_moisture", "recent_rainfall", "runoff_context"]
    
    signals = [
        FarmSignal(domain="soil", name="soil.moisture.vwc", value=0.15), # low_soil_moisture (< 0.25)
        FarmSignal(domain="weather", name="rainfall_mm", value=15.0),         # recent_rainfall (> 1.0)
        FarmSignal(domain="geospatial", name="layer.runoff_risk", value=1)    # runoff_context
    ]
    
    section = {"field_id": "field-1", "zone_id": "zone-A", "paddock_id": None, "asset_id": None}
    
    aggregates = engine.compute_attention_aggregates(signals, section)
    
    # Check if "Water capture gap" is in the results
    titles = [agg.title for agg in aggregates]
    assert "Water capture gap" in titles
    
    # Find the specific aggregate and check its score/priority
    water_gap = next(agg for agg in aggregates if agg.title == "Water capture gap")
    assert water_gap.score >= 0.42
    assert "low soil moisture detected" in " ".join(water_gap.supporting_evidence)
    assert "recent rainfall detected" in " ".join(water_gap.supporting_evidence)

def test_diagnostic_interpretation_drought_stress(engine):
    # Setup signals for drought stress
    # Rule requirements: ["soil.moisture", "rainfall"]
    # Evidence terms: low_soil_moisture, high_drydown_weather
    
    signals = [
        FarmSignal(domain="soil", name="soil.moisture.vwc", value=0.10),
        FarmSignal(domain="weather", name="rainfall_mm", value=0.0),
        FarmSignal(domain="weather", name="air_temperature", value=35.0), # high_drydown_weather
        FarmSignal(domain="weather", name="relative_humidity", value=20.0) # high_drydown_weather
    ]
    
    section = {"field_id": "field-1", "zone_id": "zone-A", "paddock_id": None, "asset_id": None}
    
    interpretations = engine.interpret_signals(signals, section)
    
    # Find drought stress
    drought = next(interp for interp in interpretations if interp.interpretation_id == "soil_water_drought_stress")
    assert drought.score > 0.3
    assert "low soil moisture detected" in " ".join(drought.supporting_evidence)
    assert "high temperature" in " ".join(drought.supporting_evidence)

def test_full_diagnose_section_flow(engine):
    graph = engine.graph
    farm_id = "farm-1"
    zone_id = "zone-A"
    now = datetime.now(timezone.utc).isoformat()
    
    # Seed enough signals to pass the minimum requirement (3)
    graph.storage.conn.execute(
        "INSERT INTO observations (id, node_id, timestamp, farm_id, zone_id, measurement_id, value, layer, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("obs-1", "node-1", now, farm_id, zone_id, "soil.moisture.vwc", 0.12, "SoilPhysics", '{"unit": "vwc"}')
    )
    graph.storage.conn.execute(
        "INSERT INTO observations (id, node_id, timestamp, farm_id, zone_id, measurement_id, value, layer, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("obs-2", "node-1", now, farm_id, zone_id, "air_temperature", 38.0, "Weather", '{"unit": "C"}')
    )
    graph.storage.conn.execute(
        "INSERT INTO observations (id, node_id, timestamp, farm_id, zone_id, measurement_id, value, layer, payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("obs-3", "node-1", now, farm_id, zone_id, "relative_humidity", 15.0, "Weather", '{"unit": "%"}')
    )
    
    report = engine.diagnose_section(farm_id, zone_id=zone_id)
    
    assert report.signal_count == 3
    assert report.status != "insufficient_signals"
    assert len(report.attention_aggregates) > 0
    assert len(report.ranked_interpretations) > 0
    
    # Check for Atmospheric drydown pressure
    titles = [agg.title for agg in report.attention_aggregates]
    assert "Atmospheric drydown pressure" in titles

def test_source_trust_gap(engine):
    # Test detecting stale telemetry
    signals = [
        FarmSignal(domain="source_health", name="source.last_seen_minutes", value=300.0), # > 240 mins
        FarmSignal(domain="source_health", name="source.battery_v", value=3.2)            # < 3.5V
    ]
    
    section = {"field_id": "field-1", "zone_id": "zone-A", "paddock_id": None, "asset_id": None}
    
    aggregates = engine.compute_attention_aggregates(signals, section)
    
    trust_gap = next(agg for agg in aggregates if agg.aggregate_id == "attention_source_trust_gap")
    assert trust_gap.score > 0.4
    assert "source telemetry stale" in " ".join(trust_gap.supporting_evidence)
    assert "low battery" in " ".join(trust_gap.supporting_evidence)

def test_e2e_water_capture_gap(engine):
    # This test verifies the full pipeline from API post to card generation
    # based on the "Water capture gap" scenario.
    from fastapi.testclient import TestClient
    from software.dashboard.main import app, get_graph
    
    # Override graph to use engine's graph file
    db_path = engine.graph.storage.db_path
    app.dependency_overrides[get_graph] = lambda: FarmGraph(db_path)
    client = TestClient(app)
    
    farm_id = "local"
    node_id = "test-node-1"
    zone_id = "zone-A"
    field_id = "field-1"
    admin_token = "dev-admin-token" 
    
    # 1. Provision and Accept Node
    setup_graph = FarmGraph(db_path)
    setup_graph.storage.update_node_registry(node_id, farm_id=farm_id, status="accepted", field_id=field_id, zone_id=zone_id)
    
    # 2. Add Runoff Context (Geospatial layer)
    setup_graph.add_edge(farm_id, "HAS_LAYER", "runoff_risk")
    setup_graph.storage.conn.close()
    
    # 3. Submit Recent Rainfall (Signal 1)
    client.post("/api/observations", json={
        "schema": "sais.observation.v1",
        "node_id": "weather-station",
        "farm_id": farm_id,
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "measurement_id": "rainfall_mm",
        "value": 12.5,
        "layer": "Weather"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    
    # 4. Submit High Temperature (Signal 2)
    client.post("/api/observations", json={
        "schema": "sais.observation.v1",
        "node_id": "weather-station",
        "farm_id": farm_id,
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "measurement_id": "air_temperature",
        "value": 25.0,
        "layer": "Weather"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    
    # 5. Submit Low Soil Moisture (Signal 3 - triggers the engine)
    response = client.post("/api/observations", json={
        "schema": "sais.observation.v1",
        "node_id": node_id,
        "farm_id": farm_id,
        "zone_id": zone_id,
        "field_id": field_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurement_id": "soil.moisture.vwc",
        "value": 0.12,
        "layer": "SoilWater"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    
    assert response.status_code == 200
    
    # 6. Verify Cards in Database
    verify_graph = FarmGraph(db_path)
    cursor = verify_graph.storage.conn.cursor()
    cursor.execute("SELECT card_type, status, payload_json FROM cards")
    cards = cursor.fetchall()
    
    types = [c[0] for c in cards]
    payloads = [json.loads(c[2]) for c in cards]
    titles = [p.get("title") for p in payloads]
    
    assert "AttentionCard" in types
    assert "Water capture gap" in titles
    assert "DiagnosticCard" in types
    assert any("Rainfall capture appears weak" in str(t) for t in titles)
    
    # Verify the AttentionCard content specifically
    cursor.execute("SELECT payload_json FROM cards WHERE card_type = 'AttentionCard'")
    rows = cursor.fetchall()
    target_card = None
    for r in rows:
        p = json.loads(r[0])
        if p.get("title") == "Water capture gap":
            target_card = p
            break
            
    assert target_card is not None
    assert "low soil moisture detected" in " ".join(target_card["evidence"])
    assert "recent rainfall detected" in " ".join(target_card["evidence"])
    assert "runoff context available" in " ".join(target_card["evidence"])

    verify_graph.storage.conn.close()
    app.dependency_overrides.clear()
