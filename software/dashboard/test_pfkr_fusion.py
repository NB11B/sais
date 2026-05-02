import pytest
import os
import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Setup DB path override
db_path = "test_sais_fusion.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm, Paddock

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_teardown(request):
    test_db = f"test_{request.node.name}.sqlite"
    os.environ["SAIS_DB_PATH"] = test_db
    
    if os.path.exists(test_db):
        os.remove(test_db)
    
    graph = get_graph()
    farm = Farm(id="local", name="Test Farm")
    paddock = Paddock(id="paddock-1", field_id="field-a", name="Paddock 1", rest_target_days=30)
    graph.add_node(farm)
    graph.add_node(paddock)
    
    # Add a grazing event 40 days ago (so it's recovered)
    started_at = "2024-01-01T12:00:00Z"
    graph.storage.add_grazing_event(
        event_id="graze-1", farm_id="local", field_id="field-a", paddock_id="paddock-1",
        started_at=started_at, ended_at="2024-01-02T12:00:00Z", animal_count=100, notes="", payload={}
    )
    
    graph.storage.conn.close()
    yield
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass

def test_soil_aware_recovery_fusion(client):
    # 1. Paddock should be OK initially (rest target met)
    client.post("/api/plant/observations", json={
        "id": "p-1", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": "2024-05-01T12:00:00Z",
        "forage_mass_kg_ha": 2000, "height_cm": 20, "recovery_score": 5
    })
    
    r = client.get("/api/cards")
    recovery_card = [c for c in r.json()["cards"] if c["card_type"] == "PlantRecoveryCard"][0]
    assert recovery_card["status"] == "ok"

    # 2. Add a weak infiltration test (5 mm/hr)
    client.post("/api/soil/observations", json={
        "id": "s-1", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": "2024-05-02T12:00:00Z",
        "infiltration_mm_hr": 5.0
    })
    
    # 3. Verify PlantRecoveryCard now reflects the fusion (downgraded to watch)
    r = client.get("/api/cards")
    recovery_card = [c for c in r.json()["cards"] if c["card_type"] == "PlantRecoveryCard"][0]
    assert recovery_card["status"] == "watch"
    assert "low infiltration detected" in recovery_card["evidence"][-1].lower()

def test_water_aware_livestock_fusion(client):
    # 1. Add livestock check
    client.post("/api/livestock/observations", json={
        "id": "ls-1", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": "2024-05-01T12:00:00Z",
        "bcs": 3.0, "manure_score": 3
    })
    
    r = client.get("/api/cards")
    ls_card = [c for c in r.json()["cards"] if c["card_type"] == "LivestockConditionCard"][0]
    assert ls_card["status"] == "ok"

    # 2. Add a Water Alert (Pump broken)
    client.post("/api/infrastructure/status", json={
        "id": "pump-1", "farm_id": "local", "asset_type": "Pump", "status": "alert"
    })
    
    # 3. Post a fresh observation to trigger the updated card
    client.post("/api/livestock/observations", json={
        "id": "ls-2", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": "2024-05-02T12:00:00Z",
        "bcs": 3.0, "manure_score": 3
    })
    
    # 4. Verify LivestockConditionCard reflects the infrastructure alert fusion
    r = client.get("/api/cards")
    ls_card = [c for c in r.json()["cards"] if c["card_type"] == "LivestockConditionCard"][0]
    assert ls_card["status"] == "action"
    assert "CRITICAL: Water system infrastructure alert active" in ls_card["evidence"]

def test_ranch_health_card_aggregation(client):
    # 1. Start clean
    client.post("/api/plant/observations", json={
        "id": "p-2", "farm_id": "local", "paddock_id": "paddock-1", "timestamp": "2024-05-01T12:00:00Z",
        "forage_mass_kg_ha": 2000, "height_cm": 20, "recovery_score": 5
    })
    
    r = client.get("/api/cards")
    health_card = [c for c in r.json()["cards"] if c["card_type"] == "RanchHealthCard"][0]
    assert health_card["status"] == "ok"
    
    # 2. Add an INFRA ALERT
    client.post("/api/infrastructure/status", json={
        "id": "gate-1", "farm_id": "local", "asset_type": "Gate", "status": "open"
    })
    
    # 3. Verify RanchHealthCard is now ALERT
    r = client.get("/api/cards")
    health_card = [c for c in r.json()["cards"] if c["card_type"] == "RanchHealthCard"][0]
    assert health_card["status"] == "alert"
    assert health_card["scorecard"]["PFKR-6 (Infra)"] == "alert"
