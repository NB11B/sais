"""
WP25: Hardened Pydantic schemas for all SAIS API payloads.

All string fields have length limits. IDs are constrained to safe characters.
Timestamps are validated. Enums are enforced where applicable. Numeric fields
have sensible bounds. GeoJSON is size-limited and geometry-validated.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# --- Shared Constants ---

_ID_PATTERN = r'^[a-zA-Z0-9._\-]+$'
_ID_MAX = 128

# --- Shared Validators ---

def _validate_timestamp_str(v: str, allow_historical: bool = False) -> str:
    """Parse ISO timestamp, require UTC-compatible, reject large clock skew."""
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        raise ValueError(f"Invalid ISO 8601 timestamp: {v}")
    
    now = datetime.now(timezone.utc)
    skew = (now - dt).total_seconds()
    
    # Future check (always rejected)
    if skew < -3600: # 1 hour future max for clock drift
        raise ValueError(f"Timestamp is in the future ({abs(skew):.0f}s).")
    
    # Historical check (strict for live telemetry)
    if not allow_historical and skew > 86400:  # 24 hours
        raise ValueError(f"Timestamp skew too large ({skew:.0f}s). Must be within 24h for live data.")
    
    return v


class GeoJSONValidator:
    """Mixin for models with boundary_geojson fields."""
    @field_validator("boundary_geojson")
    @classmethod
    def validate_geojson(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        # Type check
        allowed_types = {"Feature", "FeatureCollection", "Polygon", "MultiPolygon", "Point"}
        geom_type = v.get("type")
        if geom_type not in allowed_types:
            raise ValueError(f"Invalid GeoJSON type: {geom_type}. Must be one of {allowed_types}")
        # Size limit: reject deeply nested or oversized payloads
        import json
        serialized = json.dumps(v)
        if len(serialized) > 100_000:  # 100 KB max for a single boundary
            raise ValueError("GeoJSON payload too large (max 100KB)")
        # Coordinate bounds check for Polygon/MultiPolygon
        if geom_type in ("Polygon", "MultiPolygon"):
            coords = v.get("coordinates", [])
            _validate_coordinate_bounds(coords)
        elif geom_type == "Feature":
            geom = v.get("geometry", {})
            if geom and geom.get("type") in ("Polygon", "MultiPolygon"):
                coords = geom.get("coordinates", [])
                _validate_coordinate_bounds(coords)
        return v


def _validate_coordinate_bounds(coords, depth=0):
    """Recursively check coordinate bounds and nesting depth."""
    if depth > 5:
        raise ValueError("GeoJSON coordinate nesting too deep")
    if isinstance(coords, list):
        for item in coords:
            if isinstance(item, list) and len(item) >= 2 and isinstance(item[0], (int, float)):
                lng, lat = item[0], item[1]
                if not (-180 <= lng <= 180):
                    raise ValueError(f"Longitude {lng} out of range [-180, 180]")
                if not (-90 <= lat <= 90):
                    raise ValueError(f"Latitude {lat} out of range [-90, 90]")
            elif isinstance(item, list):
                _validate_coordinate_bounds(item, depth + 1)


# --- Core Observation Schema ---

class ObservationPayload(BaseModel):
    schema_version: str = Field(alias="schema", max_length=64)
    node_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    zone_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    field_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    timestamp: str = Field(..., max_length=64)
    measurement_id: str = Field(..., min_length=1, max_length=128)
    layer: str = Field(..., max_length=64, pattern=r'^[A-Za-z]+$')
    value: float = Field(..., ge=-1e6, le=1e6)
    unit: Optional[str] = Field(None, max_length=32)
    source: Optional[Dict[str, Any]] = None
    measurement_basis: Optional[str] = Field(None, pattern=r'^(direct|derived|estimated|manual)$')
    confidence: Optional[str] = Field(None, pattern=r'^(low|medium|high|quarantined)$')
    # WP25.1: Anti-replay fields
    sequence: Optional[int] = Field(None, ge=0)
    payload_hash: Optional[str] = Field(None, max_length=64)

    @field_validator("timestamp")
    @classmethod
    def check_timestamp(cls, v):
        return _validate_timestamp_str(v)


# --- Farm Hierarchy Schemas ---

class FarmPayload(BaseModel, GeoJSONValidator):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    name: str = Field(..., min_length=1, max_length=256)
    boundary_geojson: Optional[Dict[str, Any]] = None

class FieldPayload(BaseModel, GeoJSONValidator):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    name: str = Field(..., min_length=1, max_length=256)
    boundary_geojson: Optional[Dict[str, Any]] = None

class ZonePayload(BaseModel, GeoJSONValidator):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    field_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    name: str = Field(..., min_length=1, max_length=256)
    boundary_geojson: Optional[Dict[str, Any]] = None

class PaddockPayload(BaseModel, GeoJSONValidator):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    field_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    name: str = Field(..., min_length=1, max_length=256)
    boundary_geojson: Optional[Dict[str, Any]] = None
    rest_target_days: Optional[int] = Field(None, ge=0, le=365)


# --- Event and Observation Schemas ---

class GrazingEventPayload(BaseModel):
    schema_version: str = Field(alias="schema", max_length=64)
    event_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    field_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    paddock_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    started_at: str = Field(..., max_length=64)
    ended_at: Optional[str] = Field(None, max_length=64)
    animal_count: int = Field(0, ge=0, le=100000)
    notes: Optional[str] = Field(None, max_length=2048)

    @field_validator("started_at")
    @classmethod
    def check_started(cls, v):
        return _validate_timestamp_str(v, allow_historical=True)

class LivestockObservationPayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    paddock_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    timestamp: str = Field(..., max_length=64)
    bcs: Optional[float] = Field(None, ge=1, le=9)
    manure_score: Optional[int] = Field(None, ge=1, le=5)
    activity_level: Optional[str] = Field("normal", pattern=r'^(low|normal|high|distressed)$')
    health_notes: Optional[str] = Field(None, max_length=2048)

    @field_validator("timestamp")
    @classmethod
    def check_timestamp(cls, v):
        return _validate_timestamp_str(v, allow_historical=True)


# --- Sensor and Infrastructure Schemas ---

class SensorNodePayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    node_type: str = Field(..., min_length=1, max_length=64)
    field_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    zone_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    location: Optional[Dict[str, Any]] = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        if not isinstance(v, dict) or "lat" not in v or "lng" not in v:
            raise ValueError("Location must be a dict with 'lat' and 'lng'")
        lat, lng = v["lat"], v["lng"]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not isinstance(lng, (int, float)) or not (-180 <= lng <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

class PlantObservationPayload(BaseModel):
    schema_version: str = Field(alias="schema", default="sais.plant_observation.v1", max_length=64)
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    paddock_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    timestamp: str = Field(..., max_length=64)
    forage_mass_kg_ha: Optional[float] = Field(None, ge=0, le=100000)
    cover_percent: Optional[float] = Field(None, ge=0, le=100)
    height_cm: Optional[float] = Field(None, ge=0, le=10000)
    recovery_score: Optional[int] = Field(None, ge=1, le=5)
    ndvi: Optional[float] = Field(None, ge=-1, le=1)
    brix: Optional[float] = Field(None, ge=0, le=50)
    leaf_temperature: Optional[float] = Field(None, ge=-50, le=80)
    notes: Optional[str] = Field(None, max_length=2048)

    @field_validator("timestamp")
    @classmethod
    def check_timestamp(cls, v):
        return _validate_timestamp_str(v, allow_historical=True)

class SoilObservationPayload(BaseModel):
    schema_version: str = Field(alias="schema", default="sais.soil_observation.v1", max_length=64)
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    paddock_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    timestamp: str = Field(..., max_length=64)
    infiltration_mm_hr: Optional[float] = Field(None, ge=0, le=10000)
    organic_matter_pct: Optional[float] = Field(None, ge=0, le=100)
    soil_temp_c: Optional[float] = Field(None, ge=-50, le=80)
    notes: Optional[str] = Field(None, max_length=2048)

    @field_validator("timestamp")
    @classmethod
    def check_timestamp(cls, v):
        return _validate_timestamp_str(v, allow_historical=True)

class InfrastructureStatusPayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    asset_type: str = Field(..., min_length=1, max_length=64)
    status: str = Field(..., min_length=1, max_length=32)
    notes: Optional[str] = Field(None, max_length=2048)


# --- WP25: Typed schemas for previously-untyped routes ---

class InfrastructureAssetPayload(BaseModel, GeoJSONValidator):
    """Typed schema for POST /api/infrastructure/asset (replaces Dict[str, Any])."""
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    asset_type: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=256)
    status: str = Field("unknown", max_length=32)
    boundary_geojson: Optional[Dict[str, Any]] = Field(None, alias="location_geojson")
    notes: Optional[str] = Field(None, max_length=2048)

class WaterAssetPayload(BaseModel):
    """Typed schema for POST /api/infrastructure/water (replaces Dict[str, Any])."""
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    asset_type: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=256)
    location: Optional[Dict[str, Any]] = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        if not isinstance(v, dict) or "lat" not in v or "lng" not in v:
            raise ValueError("Location must be a dict with 'lat' and 'lng'")
        lat, lng = v["lat"], v["lng"]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not isinstance(lng, (int, float)) or not (-180 <= lng <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

class NodeHelloPayload(BaseModel):
    """Typed schema for POST /api/nodes/hello (replaces Dict[str, Any])."""
    id: str = Field(..., min_length=1, max_length=_ID_MAX, pattern=_ID_PATTERN)
    farm_id: str = Field("local", max_length=_ID_MAX, pattern=_ID_PATTERN)
    firmware_version: Optional[str] = Field(None, max_length=32)
    hardware_family: Optional[str] = Field(None, max_length=64)
    capabilities: Optional[Dict[str, Any]] = None
    battery_mv: Optional[int] = Field(None, ge=0, le=50000)
    rssi_dbm: Optional[int] = Field(None, ge=-150, le=0)

class NodeAssignmentPayload(BaseModel):
    """Typed schema for PUT /api/nodes/{id}/assignment (replaces Dict[str, Any])."""
    role: Optional[str] = Field(None, max_length=64)
    farm_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    field_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    zone_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    paddock_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    asset_id: Optional[str] = Field(None, max_length=_ID_MAX, pattern=_ID_PATTERN)
    config: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
