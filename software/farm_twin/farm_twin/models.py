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
class SoilMapUnit(GraphEntity):
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
