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
