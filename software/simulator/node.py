import random
import time
import math
from datetime import datetime, timezone

class BaseSimulatedNode:
    def __init__(self, node_id: str, farm_id: str, zone_id: str = None):
        self.node_id = node_id
        self.farm_id = farm_id
        self.zone_id = zone_id

    def tick(self):
        pass

    def get_observations(self):
        return []

class SoilMoistureNode(BaseSimulatedNode):
    def __init__(self, node_id: str, farm_id: str, zone_id: str, depth_cm: int = 30, drying_rate: float = 0.01):
        super().__init__(node_id, farm_id, zone_id)
        self.depth_cm = depth_cm
        self.drying_rate = drying_rate
        self.moisture = 0.35 # Start at 35%

    def tick(self):
        # Gradual drying
        decay = random.uniform(self.drying_rate * 0.5, self.drying_rate * 1.5)
        self.moisture = max(0.05, self.moisture - (decay * 0.1)) # Scaled for 5s ticks

    def rain_event(self, amount_mm: float):
        # Rain increases moisture proportional to amount
        increase = min(0.3, amount_mm * 0.02)
        self.moisture = min(0.6, self.moisture + increase)

    def get_observations(self):
        return [{
            "measurement_id": "soil.moisture.vwc",
            "layer": "SoilPhysics",
            "value": round(self.moisture, 3),
            "unit": "m3/m3",
            "source": {"type": "simulator", "depth_cm": self.depth_cm}
        }]

class WeatherStationNode(BaseSimulatedNode):
    def __init__(self, node_id: str, farm_id: str):
        super().__init__(node_id, farm_id)
        self.base_temp = 20.0
        self.rain_acc = 0.0

    def tick(self):
        # Diurnal cycle simulation for temperature
        # 24h period = 86400 seconds
        now_ts = time.time()
        hour_of_day = (now_ts % 86400) / 3600
        # Peak temp at 2pm (14:00), Min at 4am (04:00)
        temp_cycle = math.sin((hour_of_day - 8) * math.pi / 12) * 5
        self.current_temp = self.base_temp + temp_cycle + random.uniform(-0.5, 0.5)
        
        # Stochastic rain (1% chance per tick)
        if random.random() < 0.01:
            self.rain_acc = random.uniform(1.0, 5.0)
        else:
            self.rain_acc = 0.0

    def get_observations(self):
        obs = [
            {
                "measurement_id": "weather.air_temperature",
                "layer": "Weather",
                "value": round(self.current_temp, 1),
                "unit": "C",
                "source": {"type": "simulator"}
            }
        ]
        if self.rain_acc > 0:
            obs.append({
                "measurement_id": "weather.rainfall.hourly",
                "layer": "Weather",
                "value": round(self.rain_acc, 1),
                "unit": "mm",
                "source": {"type": "simulator"}
            })
        return obs
