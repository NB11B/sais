"""
WP25: Security test suite for SAIS Dashboard API.

Tests cover:
1. Unauthorized mutation rejection (401 on all mutating routes without token)
2. Authorized mutation success (with valid token)
3. Pending node quarantine (observation from unaccepted node is quarantined)
4. Schema validation (malformed IDs, future timestamps, oversized payloads)
5. Node hello open access (no token required)
"""

import os
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Set a known test token before importing the app
os.environ["SAIS_ADMIN_TOKEN"] = "test-admin-token-wp25"
os.environ["SAIS_DB_PATH"] = "test_sais_security.sqlite"

import sys
sais_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(sais_root, 'software', 'farm_twin'))

from main import app
from auth import ADMIN_TOKEN

client = TestClient(app, raise_server_exceptions=False)

VALID_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
NODE_HEADERS = {"Authorization": f"Bearer {os.environ.get('SAIS_NODE_TOKEN', ADMIN_TOKEN)}"}

# --- Test Data ---

def _make_observation(node_id="test-node-001", value=0.25):
    return {
        "schema": "sais.observation.v1",
        "node_id": node_id,
        "farm_id": "local",
        "field_id": "field-a",
        "zone_id": "zone-a1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": value,
        "unit": "m3/m3",
        "measurement_basis": "direct",
        "confidence": "medium",
        "sequence": 100,
        "payload_hash": "hash-123"
    }

def _make_farm():
    return {"id": "test-farm", "name": "Test Farm"}

def _make_field():
    return {"id": "test-field", "farm_id": "test-farm", "name": "Test Field"}

def _make_node_hello(node_id="hello-node-001"):
    return {"id": node_id, "farm_id": "local", "firmware_version": "0.1.0"}


# --- Fixtures ---

@pytest.fixture(autouse=True)
def clean_db():
    """Remove test database before each test."""
    db_path = os.environ.get("SAIS_DB_PATH", "test_sais_security.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
    yield
    if os.path.exists(db_path):
        os.remove(db_path)


# --- 1. Unauthorized Mutation Rejection ---

class TestUnauthorizedAccess:
    """All mutating routes must return 401 without a valid token."""

    MUTATING_ROUTES = [
        ("POST", "/api/observations"),
        ("PUT", "/api/farm/profile"),
        ("POST", "/api/farm/fields"),
        ("POST", "/api/farm/zones"),
        ("POST", "/api/farm/paddocks"),
        ("POST", "/api/grazing/events"),
        ("POST", "/api/livestock/observations"),
        ("POST", "/api/farm/sensor-nodes"),
        ("POST", "/api/plant/observations"),
        ("POST", "/api/soil/observations"),
        ("POST", "/api/infrastructure/status"),
        ("POST", "/api/infrastructure/asset"),
        ("POST", "/api/infrastructure/water"),
        ("POST", "/api/nodes/test-node/accept"),
        ("POST", "/api/nodes/test-node/reject"),
        ("PUT", "/api/nodes/test-node/assignment"),
        ("POST", "/api/cards/test-card/action"),
    ]

    @pytest.mark.parametrize("method,path", MUTATING_ROUTES)
    def test_401_without_token(self, method, path):
        """Mutating endpoint returns 401 without Authorization header."""
        if method == "POST":
            resp = client.post(path, json={})
        else:
            resp = client.put(path, json={})
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}, expected 401"

    @pytest.mark.parametrize("method,path", MUTATING_ROUTES)
    def test_401_with_bad_token(self, method, path):
        """Mutating endpoint returns 401 with wrong token."""
        bad_headers = {"Authorization": "Bearer wrong-token-12345"}
        if method == "POST":
            resp = client.post(path, json={}, headers=bad_headers)
        else:
            resp = client.put(path, json={}, headers=bad_headers)
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}, expected 401"


# --- 2. Authorized Mutation Success ---

class TestAuthorizedAccess:
    """Mutating routes should succeed with a valid token (where payload is valid)."""

    def test_put_farm_profile_authorized(self):
        resp = client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_post_observation_authorized(self):
        # First create the farm structure and accept the node
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        resp = client.post("/api/observations", json=_make_observation(), headers=VALID_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_post_observation_node_auth(self):
        """Observation succeeds with node token."""
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        resp = client.post("/api/observations", json=_make_observation(), headers=NODE_HEADERS)
        assert resp.status_code == 200


# --- 3. Pending Node Quarantine ---

class TestNodeQuarantine:
    """Observations from unaccepted nodes should be quarantined."""

    def test_observation_from_unknown_node_is_quarantined(self):
        """Observation from a node not in registry gets quarantined flag."""
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        resp = client.post("/api/observations", json=_make_observation("unknown-node"), headers=VALID_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["quarantined"] is True

    def test_observation_from_pending_node_is_quarantined(self):
        """Node that has said hello but is not accepted gets quarantined."""
        # Node says hello (creates pending entry)
        client.post("/api/nodes/hello", json=_make_node_hello("pending-node"))
        
        # Submit observation for the pending node
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        obs = _make_observation("pending-node")
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["quarantined"] is True

    def test_observation_from_accepted_node_is_not_quarantined(self):
        """Accepted node observations are not quarantined."""
        # Create farm and register+accept node
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        client.post("/api/nodes/hello", json=_make_node_hello("accepted-node"))
        client.post("/api/nodes/accepted-node/accept", headers=VALID_HEADERS)
        
        obs = _make_observation("accepted-node")
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["quarantined"] is False

    def test_quarantined_node_does_not_mutate_graph(self):
        """Data from quarantined nodes does not create nodes in the graph."""
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        obs = _make_observation("unknown-node")
        obs["measurement_id"] = "quarantine.secret.metric"
        
        # Submit observation (gets quarantined)
        client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        
        # Check graph
        resp = client.get("/api/graph")
        graph_data = resp.json()
        node_ids = [n["id"] for n in graph_data["nodes"]]
        assert "unknown-node" not in node_ids
        assert "quarantine.secret.metric" not in node_ids


# --- 4. Node Hello Open Access ---

class TestNodeHelloOpen:
    """Node hello endpoint must NOT require admin token."""

    def test_node_hello_without_token(self):
        resp = client.post("/api/nodes/hello", json=_make_node_hello("open-node"))
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"


# --- 5. Schema Validation ---

class TestSchemaValidation:
    """Pydantic schema hardening rejects malformed inputs."""

    def test_invalid_id_special_chars(self):
        """IDs with special characters are rejected."""
        obs = _make_observation()
        obs["node_id"] = "<script>alert(1)</script>"
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_invalid_id_spaces(self):
        """IDs with spaces are rejected."""
        obs = _make_observation()
        obs["node_id"] = "bad node id"
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_future_timestamp_rejected(self):
        """Timestamp more than 24h in the future is rejected."""
        obs = _make_observation()
        future = datetime.now(timezone.utc) + timedelta(hours=48)
        obs["timestamp"] = future.isoformat()
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_past_timestamp_rejected(self):
        """Timestamp more than 24h in the past is rejected."""
        obs = _make_observation()
        past = datetime.now(timezone.utc) - timedelta(hours=48)
        obs["timestamp"] = past.isoformat()
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_invalid_layer_special_chars(self):
        """Layer with non-alpha characters is rejected."""
        obs = _make_observation()
        obs["layer"] = "Soil_Physics!"
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_value_out_of_bounds(self):
        """Value exceeding bounds is rejected."""
        obs = _make_observation()
        obs["value"] = 2e6  # exceeds 1e6 limit
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_invalid_confidence_enum(self):
        """Invalid confidence value is rejected."""
        obs = _make_observation()
        obs["confidence"] = "very_high"
        resp = client.post("/api/observations", json=obs, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_node_hello_xss_id_rejected(self):
        """Node hello with XSS payload in ID is rejected by schema."""
        hello = {"id": "<img src=x onerror=alert(1)>", "farm_id": "local"}
        resp = client.post("/api/nodes/hello", json=hello)
        assert resp.status_code == 422

    def test_empty_id_rejected(self):
        """Empty string ID is rejected."""
        farm = {"id": "", "name": "Bad Farm"}
        resp = client.put("/api/farm/profile", json=farm, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_oversized_name_rejected(self):
        """Name exceeding 256 chars is rejected."""
        farm = {"id": "test-farm", "name": "A" * 300}
        resp = client.put("/api/farm/profile", json=farm, headers=VALID_HEADERS)
        assert resp.status_code == 422

    def test_invalid_geojson_oversized_rejected(self):
        """Oversized GeoJSON is rejected by schema."""
        farm = _make_farm()
        farm["boundary_geojson"] = {
            "type": "Polygon",
            "coordinates": [[[0,0], [0,1], [1,1], [0,0]]] * 10000 # very large
        }
        resp = client.put("/api/farm/profile", json=farm, headers=VALID_HEADERS)
        assert resp.status_code == 422


# --- 6. Read-Only Routes Remain Open ---

class TestReadOnlyAccess:
    """GET routes should work without authentication."""

    def test_health_no_auth(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_cards_no_auth(self):
        resp = client.get("/api/cards")
        assert resp.status_code == 200

    def test_observations_no_auth(self):
        resp = client.get("/api/observations")
        assert resp.status_code == 200

    def test_graph_no_auth(self):
        resp = client.get("/api/graph")
        assert resp.status_code == 200

    def test_pending_nodes_no_auth(self):
        resp = client.get("/api/nodes/pending")
        assert resp.status_code == 200

    def test_active_nodes_no_auth(self):
        resp = client.get("/api/nodes/active")
        assert resp.status_code == 200


# --- 7. Security Headers ---

class TestSecurityHeaders:
    """Security headers middleware should set expected headers."""

    def test_x_content_type_options(self):
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self):
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self):
        resp = client.get("/health")
        assert resp.headers.get("referrer-policy") == "strict-origin"

    def test_content_security_policy(self):
        resp = client.get("/health")
        csp = resp.headers.get("content-security-policy")
        assert "default-src 'self'" in csp
        assert "script-src 'self' 'unsafe-inline'" in csp

# --- 8. Anti-Replay ---

class TestAntiReplay:
    """Sequence and hash checks prevent duplicate data ingestion."""

    def test_sequence_replay_rejected(self):
        """Lower or equal sequence numbers are rejected."""
        # Register and accept node
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        client.post("/api/nodes/hello", json=_make_node_hello("seq-node"))
        client.post("/api/nodes/seq-node/accept", headers=VALID_HEADERS)
        
        # 1. First observation (seq 100)
        obs1 = _make_observation("seq-node")
        obs1["sequence"] = 100
        resp = client.post("/api/observations", json=obs1, headers=VALID_HEADERS)
        assert resp.status_code == 200
        
        # 2. Replay (seq 100) -> Rejected
        resp = client.post("/api/observations", json=obs1, headers=VALID_HEADERS)
        assert resp.status_code == 400 or resp.status_code == 500 # Depending on how ValueError is handled
        assert "Sequence replay" in resp.text
        
        # 3. Old sequence (seq 99) -> Rejected
        obs2 = _make_observation("seq-node")
        obs2["sequence"] = 99
        resp = client.post("/api/observations", json=obs2, headers=VALID_HEADERS)
        assert "Sequence replay" in resp.text

    def test_hash_replay_rejected(self):
        """Identical payload hashes are rejected."""
        client.put("/api/farm/profile", json=_make_farm(), headers=VALID_HEADERS)
        client.post("/api/nodes/hello", json=_make_node_hello("hash-node"))
        client.post("/api/nodes/hash-node/accept", headers=VALID_HEADERS)
        
        obs1 = _make_observation("hash-node")
        obs1["payload_hash"] = "unique-hash-abc"
        obs1["sequence"] = 10
        resp = client.post("/api/observations", json=obs1, headers=VALID_HEADERS)
        assert resp.status_code == 200
        
        # 2. Duplicate hash -> Rejected
        obs2 = _make_observation("hash-node")
        obs2["payload_hash"] = "unique-hash-abc"
        obs2["sequence"] = 11
        resp = client.post("/api/observations", json=obs2, headers=VALID_HEADERS)
        assert "Duplicate payload hash" in resp.text
