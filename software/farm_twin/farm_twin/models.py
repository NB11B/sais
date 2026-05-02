from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json

class GraphEntity:
    def to_json(self) -> str:
        return json.dumps(asdict(self))

@dataclass
class Farm(GraphEntity):
    id: str
    name: str
    boundary_geojson: Optional[dict] = None

@dataclass
class Field(GraphEntity):
    id: str
    farm_id: str
    name: str
    boundary_geojson: Optional[dict] = None

@dataclass
class ManagementZone(GraphEntity):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[dict] = None

@dataclass
class Paddock(GraphEntity):
    id: str
    field_id: str
    name: str
    boundary_geojson: Optional[dict] = None
    rest_target_days: Optional[int] = None

@dataclass
class GrazingEvent(GraphEntity):
    id: str
    farm_id: str
    paddock_id: str
    started_at: str
    ended_at: Optional[str] = None
    animal_count: int = 0
    notes: Optional[str] = None

@dataclass
class LivestockObservation(GraphEntity):
    id: str
    farm_id: str
    paddock_id: str
    timestamp: str
    bcs: Optional[float] = None
    manure_score: Optional[int] = None
    activity_level: Optional[str] = "normal"
    health_notes: Optional[str] = None

@dataclass
class WaterAsset(GraphEntity):
    id: str
    farm_id: str
    asset_type: str # tank, pump, valve, trough
    name: str
    field_id: Optional[str] = None
    paddock_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    capacity_liters: Optional[float] = None
    boundary_geojson: Optional[Dict[str, Any]] = None

@dataclass
class PlantObservation(GraphEntity):
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

@dataclass
class SoilObservation(GraphEntity):
    id: str
    farm_id: str
    timestamp: str
    paddock_id: Optional[str] = None
    zone_id: Optional[str] = None
    infiltration_mm_hr: Optional[float] = None
    organic_matter_pct: Optional[float] = None
    soil_temp_c: Optional[float] = None
    biological_activity_score: Optional[int] = None # 1-5
    notes: Optional[str] = None

@dataclass
class InfrastructureAsset(GraphEntity):
    id: str
    farm_id: str
    asset_type: str # Fence, Gate, Road, Pump, Solar
    name: str
    status: str # ok, broken, open, closed, unknown
    location_geojson: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

@dataclass
class SoilMapUnit(GraphEntity) :
    id: str
    farm_id: str
    name: str
    boundary_geojson: Optional[dict] = None

@dataclass
class GeospatialLayer(GraphEntity):
    id: str
    farm_id: str
    layer_type: str
    path: str
    units: Optional[str] = None
    assumptions: List[str] = field(default_factory=list)

@dataclass
class GeospatialCell(GraphEntity):
    id: str
    layer_id: str
    value: Any

@dataclass
class SensorNode(GraphEntity):
    id: str
    farm_id: str
    node_type: str
    field_id: Optional[str] = None
    zone_id: Optional[str] = None
    location: Optional[dict] = None

@dataclass
class Measurement(GraphEntity):
    id: str
    farm_id: str
    layer: str

@dataclass
class Observation(GraphEntity):
    id: str
    farm_id: str
    node_id: str
    timestamp: str
    measurement_id: str
    layer: str
    value: Any
    basis: str
    confidence: str
    source: Dict[str, Any]
    unit: Optional[str] = None
    pfkr_id: Optional[str] = None

@dataclass
class DerivedIndicator(GraphEntity):
    id: str
    farm_id: str
    name: str

@dataclass
class FarmerDecision(GraphEntity):
    id: str
    farm_id: str
    decision: str

@dataclass
class Intervention(GraphEntity):
    id: str
    farm_id: str
    intervention: str

@dataclass
class AuditRecord(GraphEntity):
    id: str
    farm_id: str
    record_hash: str
