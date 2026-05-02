from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class NodeRole:
    name: str
    capabilities: List[str]
    pfkr_domains: List[str]
    interval_seconds: int
    required_fields: List[str]

ROLE_TEMPLATES = {
    "soil_probe": NodeRole(
        name="Soil Health Probe",
        capabilities=["soil.moisture.vwc", "soil.temperature"],
        pfkr_domains=["PFKR-3", "PFKR-1"],
        interval_seconds=3600,
        required_fields=["zone_id", "depth_cm"]
    ),
    "weather_station": NodeRole(
        name="Micro-Climate Station",
        capabilities=["weather.rainfall.hourly", "weather.air_temperature", "weather.relative_humidity"],
        pfkr_domains=["PFKR-7"],
        interval_seconds=1800,
        required_fields=["location"]
    ),
    "tank_level": NodeRole(
        name="Water Storage Monitor",
        capabilities=["water.tank.level_percent"],
        pfkr_domains=["PFKR-1"],
        interval_seconds=900,
        required_fields=["asset_id"]
    ),
    "gate_status": NodeRole(
        name="Infrastructure Security Sensor",
        capabilities=["infra.gate.status"],
        pfkr_domains=["PFKR-6"],
        interval_seconds=300,
        required_fields=["asset_id"]
    )
}

def get_role_template(role_id: str) -> Optional[NodeRole]:
    return ROLE_TEMPLATES.get(role_id)

def get_all_roles() -> Dict[str, NodeRole]:
    return ROLE_TEMPLATES
