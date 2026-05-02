import asyncio
import httpx
from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200

def test_missing_fields_rejection():
    payload = {
        "value": 10
    }
    resp = client.post("/api/observations", json=payload)
    assert resp.status_code == 422

def test_invalid_types():
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "test-node",
        "farm_id": "local",
        "timestamp": "now",
        "measurement_id": "moisture",
        "layer": "SoilPhysics",
        "value": "not-a-number"
    }
    resp = client.post("/api/observations", json=payload)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_concurrent_post():
    payload = {
        "schema": "sais.observation.v1",
        "node_id": "concurrent-sensor",
        "farm_id": "local",
        "zone_id": "zone-a1",
        "timestamp": "2026-05-02T13:00:00Z",
        "measurement_id": "soil.moisture.vwc",
        "layer": "SoilPhysics",
        "value": 0.12,
        "source": {"type": "sensor", "depth_cm": 30}
    }
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        tasks = [ac.post("/api/observations", json=payload) for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        for r in results:
            assert r.status_code == 200
            
    resp = client.get("/api/observations")
    obs = resp.json()["observations"]
    concurrent_obs = [o for o in obs if o.get("node_id") == "concurrent-sensor"]
    assert len(concurrent_obs) == 1
