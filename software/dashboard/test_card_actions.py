import pytest
import os
import json
from fastapi.testclient import TestClient

# Setup DB path override
db_path = "test_card_actions.sqlite"
os.environ["SAIS_DB_PATH"] = db_path

from main import app, get_graph
from farm_twin.models import Farm, Field, ManagementZone

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def setup_teardown(request):
    # Setup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize schema and seed data
    graph = get_graph()
    farm = Farm(id="local", name="Test Farm")
    graph.add_node(farm)
    
    # Create a card manually
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    graph.storage.add_card("card-1", now, "WaterRetentionCard", "watch", {"test": "payload"})
    
    graph.storage.conn.close()
    
    yield
    
    # Teardown
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

def test_get_cards_includes_action_fields(client):
    r = client.get("/api/cards")
    data = r.json()
    assert len(data["cards"]) >= 1
    card = next(c for c in data["cards"] if c["id"] == "card-1")
    assert "action_status" in card
    assert card["action_status"] == "pending"
    assert "notes" in card
    assert card["notes"] is None

def test_update_card_action_status(client):
    # 1. Update status
    payload = {"status": "resolved"}
    r = client.post("/api/cards/card-1/action", json=payload)
    assert r.status_code == 200
    
    # 2. Verify
    r = client.get("/api/cards")
    card = next(c for c in r.json()["cards"] if c["id"] == "card-1")
    assert card["action_status"] == "resolved"
    assert card["updated_at"] is not None

def test_update_card_notes(client):
    # 1. Update notes
    payload = {"notes": "Inspected field, looks dry but fine."}
    r = client.post("/api/cards/card-1/action", json=payload)
    assert r.status_code == 200
    
    # 2. Verify
    r = client.get("/api/cards")
    card = next(c for c in r.json()["cards"] if c["id"] == "card-1")
    assert card["notes"] == "Inspected field, looks dry but fine."
