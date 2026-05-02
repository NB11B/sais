from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List

class ObservationPayload(BaseModel):
    schema_version: str = Field(alias="schema")
    node_id: str
    farm_id: str
    zone_id: Optional[str] = None
    field_id: Optional[str] = None
    timestamp: str
    measurement_id: str
    layer: str
    value: float
    unit: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    measurement_basis: Optional[str] = None
    confidence: Optional[str] = None

class GeoJSONValidator:
    @field_validator("boundary_geojson")
    @classmethod
    def validate_geojson(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        allowed_types = {"Feature", "FeatureCollection", "Polygon", "MultiPolygon", "Point"}
        geom_type = v.get("type")
        if geom_type not in allowed_types:
            raise ValueError(f"Invalid GeoJSON type: {geom_type}. Must be one of {allowed_types}")
        return v

class FarmPayload(BaseModel, GeoJSONValidator):
    id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class FieldPayload(BaseModel, GeoJSONValidator):
    id: str
    farm_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class ZonePayload(BaseModel, GeoJSONValidator):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class PaddockPayload(BaseModel, GeoJSONValidator):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None
    rest_target_days: Optional[int] = None

class GrazingEventPayload(BaseModel):
    schema_version: str = Field(alias="schema")
    event_id: str
    farm_id: str
    field_id: str
    paddock_id: str
    started_at: str
    ended_at: Optional[str] = None
    animal_count: int = 0
    notes: Optional[str] = None

class LivestockObservationPayload(BaseModel):
    id: str
    farm_id: str
    paddock_id: str
    timestamp: str
    bcs: Optional[float] = None
    manure_score: Optional[int] = None
    activity_level: Optional[str] = "normal"
    health_notes: Optional[str] = None

class SensorNodePayload(BaseModel):
    id: str
    farm_id: str
    node_type: str
    field_id: Optional[str] = None
    zone_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        if not isinstance(v, dict) or "lat" not in v or "lng" not in v:
            raise ValueError("Location must be a dict with 'lat' and 'lng'")
        return v

class PlantObservationPayload(BaseModel):
    schema_version: str = Field(alias="schema", default="sais.plant_observation.v1")
    id: str
    farm_id: str
    paddock_id: str
    timestamp: str
    forage_mass_kg_ha: Optional[float] = None
    cover_percent: Optional[float] = None
    height_cm: Optional[float] = None
    recovery_score: Optional[int] = None # 1-5
    ndvi: Optional[float] = None
    brix: Optional[float] = None
    leaf_temperature: Optional[float] = None
    notes: Optional[str] = None
