"""Normalize external weather provider payloads into SAIS observations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


OPEN_METEO_FIELD_MAP = {
    "temperature_2m": ("weather.air_temperature", "degC"),
    "relative_humidity_2m": ("weather.relative_humidity", "%"),
    "precipitation": ("weather.rainfall.hourly", "mm"),
    "wind_speed_10m": ("weather.wind_speed", "km/h"),
    "wind_direction_10m": ("weather.wind_direction", "deg"),
    "surface_pressure": ("weather.surface_pressure", "hPa"),
}


def normalize_open_meteo_current(
    raw: Dict[str, Any],
    farm_id: str,
    node_id: str = "external.open_meteo.weather",
    field_id: Optional[str] = None,
    zone_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Convert an Open-Meteo `current` response into sais.observation.v1 payloads."""

    current = raw.get("current") or {}
    units = raw.get("current_units") or {}
    timestamp = current.get("time") or datetime.now(timezone.utc).isoformat()
    if timestamp.endswith("Z"):
        normalized_time = timestamp
    elif "+" in timestamp:
        normalized_time = timestamp
    else:
        normalized_time = f"{timestamp}+00:00"

    observations: List[Dict[str, Any]] = []
    for provider_key, (measurement_id, default_unit) in OPEN_METEO_FIELD_MAP.items():
        if provider_key not in current or current[provider_key] is None:
            continue

        obs = {
            "schema": "sais.observation.v1",
            "node_id": node_id,
            "farm_id": farm_id,
            "timestamp": normalized_time,
            "measurement_id": measurement_id,
            "layer": "Weather",
            "value": float(current[provider_key]),
            "unit": units.get(provider_key, default_unit),
            "measurement_basis": "estimated",
            "confidence": "medium",
            "source": {
                "type": "external_api",
                "provider": "open_meteo",
                "source_tier": "external",
                "provider_key": provider_key,
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
            },
        }
        if field_id:
            obs["field_id"] = field_id
        if zone_id:
            obs["zone_id"] = zone_id
        observations.append(obs)

    return observations
