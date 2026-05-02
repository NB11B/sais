import random

class SimulatedNode:
    def __init__(self, node_id: str, farm_id: str, zone_id: str, initial_moisture: float = 0.35):
        self.node_id = node_id
        self.farm_id = farm_id
        self.zone_id = zone_id
        self.moisture = initial_moisture
        
    def tick(self):
        """Simulates environmental decay."""
        # Decay by a small random amount between 0.005 and 0.015 (representing drying)
        decay = random.uniform(0.005, 0.015)
        self.moisture = max(0.0, self.moisture - decay)
        
    def rain_event(self):
        """Simulates a rainfall event, spiking the moisture."""
        self.moisture = min(0.60, self.moisture + random.uniform(0.15, 0.25))

    def get_observation(self):
        return {
            "measurement_id": "soil.moisture.vwc",
            "layer": "SoilPhysics",
            "value": round(self.moisture, 3),
            "source": {"type": "simulator", "depth_cm": 30}
        }
