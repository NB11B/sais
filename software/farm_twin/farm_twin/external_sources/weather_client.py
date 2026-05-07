"""Open-Meteo weather client for SAIS external context ingestion."""

from __future__ import annotations

import json
from typing import Any, Dict
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoClient:
    """Small stdlib-only client for Open-Meteo forecast/current weather data."""

    def __init__(self, base_url: str = OPEN_METEO_FORECAST_URL, timeout_seconds: int = 15):
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    def fetch_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch current weather values for a farm location.

        Returned raw payload is intentionally not SAIS-specific. Normalization is
        handled in weather_normalizer.py so tests can mock raw provider data.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure",
            ]),
            "timezone": "UTC",
        }
        url = f"{self.base_url}?{urlencode(params)}"
        with urlopen(url, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
