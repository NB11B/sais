import httpx
from datetime import datetime, timezone

class TelemetryClient:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        
    def post_observation(self, node_id: str, farm_id: str, measurement_id: str, layer: str, value: float, source: dict, 
                         zone_id: str = None, field_id: str = None, timestamp: str = None, unit: str = None):
        
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        payload = {
            "schema": "sais.observation.v1",
            "node_id": node_id,
            "farm_id": farm_id,
            "field_id": field_id,
            "zone_id": zone_id,
            "timestamp": timestamp,
            "measurement_id": measurement_id,
            "layer": layer,
            "value": value,
            "unit": unit,
            "source": source
        }
        
        try:
            response = httpx.post(self.endpoint_url, json=payload, timeout=5.0)
            response.raise_for_status()
            return True, response.json()
        except Exception as e:
            return False, str(e)
