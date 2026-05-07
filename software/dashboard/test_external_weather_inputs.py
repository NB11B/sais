import os
import json
import tempfile
import shutil
from datetime import datetime, timezone

os.environ["SAIS_ADMIN_TOKEN"] = "dev-admin-token"
os.environ["SAIS_ENV"] = "development"

from fastapi.testclient import TestClient
from farm_twin.graph import FarmGraph
from farm_twin.external_sources.external_ingest import ensure_external_weather_source
from farm_twin.external_sources.weather_normalizer import normalize_open_meteo_current
from software.dashboard.main import app, get_graph


def _make_graph():
    db_dir = tempfile.mkdtemp()
    db_path = os.path.join(db_dir, "test_sais_external.sqlite")
    graph = FarmGraph(db_path)
    return db_dir, db_path, graph


def _close_cleanup(db_dir, *graphs):
    for graph in graphs:
        try:
            graph.storage.conn.close()
        except Exception:
            pass
    shutil.rmtree(db_dir)
    app.dependency_overrides.clear()


def _mock_open_meteo_response(now: str):
    return {
        "latitude": 27.94,
        "longitude": -82.80,
        "current_units": {
            "time": "iso8601",
            "temperature_2m": "degC",
            "relative_humidity_2m": "%",
            "precipitation": "mm",
            "wind_speed_10m": "km/h",
            "wind_direction_10m": "deg",
            "surface_pressure": "hPa",
        },
        "current": {
            "time": now,
            "temperature_2m": 24.0,
            "relative_humidity_2m": 88.0,
            "precipitation": 16.0,
            "wind_speed_10m": 7.0,
            "wind_direction_10m": 180.0,
            "surface_pressure": 1015.0,
        },
    }


def test_open_meteo_normalizer_outputs_sais_observations():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    raw = _mock_open_meteo_response(now)

    observations = normalize_open_meteo_current(
        raw,
        farm_id="local",
        node_id="external.open_meteo.weather",
    )

    measurement_ids = {obs["measurement_id"] for obs in observations}
    assert "weather.air_temperature" in measurement_ids
    assert "weather.relative_humidity" in measurement_ids
    assert "weather.rainfall.hourly" in measurement_ids
    assert "weather.wind_speed" in measurement_ids
    assert all(obs["schema"] == "sais.observation.v1" for obs in observations)
    assert all(obs["layer"] == "Weather" for obs in observations)
    assert all(obs["measurement_basis"] == "estimated" for obs in observations)
    assert all(obs["source"]["provider"] == "open_meteo" for obs in observations)
    assert all(obs["source"]["source_tier"] == "external" for obs in observations)


def test_external_weather_informs_but_does_not_trigger_cards():
    db_dir, db_path, graph = _make_graph()
    app.dependency_overrides[get_graph] = lambda: FarmGraph(db_path)
    client = TestClient(app)
    admin_token = "dev-admin-token"

    try:
        farm_id = "local"
        zone_id = "zone-A"
        field_id = "field-1"
        external_weather_id = "external.open_meteo.weather"
        soil_node_id = "accepted-soil-zone-a"

        # Register external weather and accepted soil probe.
        ensure_external_weather_source(graph, farm_id=farm_id, node_id=external_weather_id)
        graph.storage.update_node_registry(
            soil_node_id,
            status="accepted",
            source_tier="accepted",
            farm_id=farm_id,
            field_id=field_id,
            zone_id=zone_id,
        )
        graph.add_edge(farm_id, "HAS_LAYER", "runoff_risk")

        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        weather_observations = normalize_open_meteo_current(
            _mock_open_meteo_response(now),
            farm_id=farm_id,
            node_id=external_weather_id,
        )

        # External observations are valid data and should store, but must not trigger cards.
        for obs in weather_observations:
            response = client.post(
                "/api/observations",
                json=obs,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["quarantined"] is False
            assert body["intelligence_triggered"] is False

        verify_graph = FarmGraph(db_path)
        cursor = verify_graph.storage.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM observations WHERE node_id = ?", (external_weather_id,))
        assert cursor.fetchone()[0] >= 3
        cursor.execute("SELECT COUNT(*) FROM cards")
        assert cursor.fetchone()[0] == 0
        verify_graph.storage.conn.close()

        # Accepted soil signal now triggers intelligence. Engine should fuse external rainfall.
        soil_payload = {
            "schema": "sais.observation.v1",
            "node_id": soil_node_id,
            "farm_id": farm_id,
            "field_id": field_id,
            "zone_id": zone_id,
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "measurement_id": "soil.moisture.vwc",
            "value": 0.10,
            "layer": "SoilWater",
            "unit": "vwc",
            "measurement_basis": "direct",
            "confidence": "high",
        }
        response = client.post(
            "/api/observations",
            json=soil_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["quarantined"] is False
        assert body["intelligence_triggered"] is True

        verify_graph = FarmGraph(db_path)
        cursor = verify_graph.storage.conn.cursor()
        cursor.execute("SELECT card_type, payload_json FROM cards")
        rows = cursor.fetchall()
        cards = [json.loads(row[1]) for row in rows]
        titles = [card.get("title") for card in cards]

        assert "Water capture gap" in titles
        assert any(card.get("card_type") == "AttentionCard" for card in cards)
        assert any(card.get("card_type") == "DiagnosticCard" for card in cards)

        water_gap = next(card for card in cards if card.get("title") == "Water capture gap")
        evidence = " ".join(water_gap.get("evidence", []))
        assert "low soil moisture detected" in evidence
        assert "recent rainfall detected" in evidence
        assert "runoff context available" in evidence
        verify_graph.storage.conn.close()

    finally:
        _close_cleanup(db_dir, graph)
