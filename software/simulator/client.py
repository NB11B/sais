import httpx
from datetime import datetime, timezone

class TelemetryClient:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        
    def post_observation(self, node_id: str, farm_id: str, zone_id: str, measurement_id: str, layer: str, value: float, source: dict):
        payload = {
            "schema": "sais.observation.v1",
            "node_id": node_id,
            "farm_id": farm_id,
            "zone_id": zone_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "measurement_id": measurement_id,
            "layer": layer,
            "value": value,
            "source": source
        }
        
        try:
            response = httpx.post(self.endpoint_url, json=payload, timeout=5.0)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            return False, str(e)
