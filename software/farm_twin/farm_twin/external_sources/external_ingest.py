"""Internal external-source ingestion helpers for SAIS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from farm_twin.graph import FarmGraph
from farm_twin.ingest_observation import ingest_sensor_observation_payload
from farm_twin.external_sources.weather_client import OpenMeteoClient
from farm_twin.external_sources.weather_normalizer import normalize_open_meteo_current


DEFAULT_OPEN_METEO_NODE_ID = "external.open_meteo.weather"


def ensure_external_weather_source(
    graph: FarmGraph,
    farm_id: str,
    node_id: str = DEFAULT_OPEN_METEO_NODE_ID,
    provider: str = "open_meteo",
) -> None:
    """Register or update the external weather source as source_tier=external."""
    graph.storage.update_node_registry(
        node_id=node_id,
        status="accepted",
        source_tier="external",
        farm_id=farm_id,
        role="external_weather_context",
        payload={
            "id": node_id,
            "farm_id": farm_id,
            "provider": provider,
            "source_tier": "external",
            "role": "external_weather_context",
        },
    )


def ingest_external_observations(
    graph: FarmGraph,
    observations: List[Dict[str, Any]],
) -> List[str]:
    """Ingest already-normalized external observations directly into FarmGraph."""
    obs_ids: List[str] = []
    for obs in observations:
        obs_ids.append(ingest_sensor_observation_payload(graph, obs))
    return obs_ids


def ingest_open_meteo_current_weather(
    graph: FarmGraph,
    farm_id: str,
    latitude: float,
    longitude: float,
    node_id: str = DEFAULT_OPEN_METEO_NODE_ID,
    field_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    client: Optional[OpenMeteoClient] = None,
) -> List[str]:
    """Fetch, normalize, register, and ingest Open-Meteo current weather data."""
    ensure_external_weather_source(graph, farm_id=farm_id, node_id=node_id)
    weather_client = client or OpenMeteoClient()
    raw = weather_client.fetch_current_weather(latitude=latitude, longitude=longitude)
    observations = normalize_open_meteo_current(
        raw,
        farm_id=farm_id,
        node_id=node_id,
        field_id=field_id,
        zone_id=zone_id,
    )
    return ingest_external_observations(graph, observations)
