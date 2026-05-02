from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

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

class FarmPayload(BaseModel):
    id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class FieldPayload(BaseModel):
    id: str
    farm_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class ZonePayload(BaseModel):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class PaddockPayload(BaseModel):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[Dict[str, Any]] = None

class SensorNodePayload(BaseModel):
    id: str
    farm_id: str
    node_type: str
    field_id: Optional[str] = None
    zone_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
