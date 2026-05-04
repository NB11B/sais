import json
from .graph import FarmGraph
from .models import Farm, Field, ManagementZone, Paddock, SensorNode, Measurement, Observation

def ingest_farm_profile(graph: FarmGraph, profile_path: str):
    """
    Parses a farm profile JSON to construct the spatial hierarchy:
    Farm -> Field -> Zone / Paddock
    """
    with open(profile_path, 'r') as f:
        data = json.load(f)
        
    farm_id = data.get("farm_id")
    
    farm = Farm(id=farm_id, name=data.get("name", farm_id), boundary_geojson=data.get("boundary_geojson"))
    graph.add_node(farm)
    
    # Add Fields
    for field_data in data.get("fields", []):
        field = Field(id=field_data["id"], farm_id=farm_id, name=field_data["name"], boundary_geojson=field_data.get("boundary_geojson"))
        graph.add_node(field)
        graph.add_edge(farm_id, "CONTAINS", field.id)
        
        # Add Zones
        for zone_data in field_data.get("zones", []):
            zone = ManagementZone(id=zone_data["id"], field_id=field.id, name=zone_data["name"], boundary_geojson=zone_data.get("boundary_geojson"))
            graph.add_node(zone)
            graph.add_edge(field.id, "CONTAINS", zone.id)
            
        # Add Paddocks
        for pad_data in field_data.get("paddocks", []):
            pad = Paddock(id=pad_data["id"], field_id=field.id, name=pad_data["name"], boundary_geojson=pad_data.get("boundary_geojson"))
            graph.add_node(pad)
            graph.add_edge(field.id, "CONTAINS", pad.id)
            
    return farm_id


def ingest_sensor_observation(graph: FarmGraph, obs_path: str):
    """
    Parses a 'sais.observation.v1' JSON file and maps it into the FarmGraph.
    """
    with open(obs_path, 'r') as f:
        data = json.load(f)
    return ingest_sensor_observation_payload(graph, data)

def ingest_sensor_observation_payload(graph: FarmGraph, data: dict):
    """
    Ingests an observation payload directly into the FarmGraph.
    Links the sensor to its zone, connects it to the measurement ontology,
    and stores the observation reading.
    """
    node_id = data["node_id"]
    obs_id = f"obs-{data['timestamp']}-{node_id}"
    source = data.get("source") or {}
    
    # WP25.1: Isolation Check
    # If the node is not accepted, store in quarantine ONLY. No graph mutation.
    registry = graph.storage.get_node_registry(node_id)
    node_status = registry["status"] if registry else "pending"
    
    if node_status != "accepted":
        # Isolated storage path
        graph.storage.add_quarantined_observation(
            obs_id, node_id, data["timestamp"], data["farm_id"],
            data["measurement_id"], data["value"], data["layer"], data
        )
        return f"quarantined-{obs_id}"

    # WP25.1: Anti-Replay / Sequence Check
    new_sequence = data.get("sequence")
    if new_sequence is not None:
        last_sequence = registry.get("last_sequence", 0) if registry else 0
        if new_sequence <= last_sequence:
            # Replay or out-of-order
            raise ValueError(f"Sequence replay detected for node {node_id}: {new_sequence} <= {last_sequence}")
        
        # Update last_sequence in registry
        graph.storage.update_node_registry(node_id, last_seen=data["timestamp"])
        # We need a small hack to update last_sequence since update_node_registry doesn't take it yet
        cursor = graph.storage.conn.cursor()
        cursor.execute("UPDATE node_registry SET last_sequence = ? WHERE id = ?", (new_sequence, node_id))
        graph.storage.conn.commit()

    # WP25.1: Payload Hash Check
    payload_hash = data.get("payload_hash")
    if payload_hash:
        cursor = graph.storage.conn.cursor()
        cursor.execute("SELECT id FROM observations WHERE node_id = ? AND payload_hash = ?", (node_id, payload_hash))
        if cursor.fetchone():
            raise ValueError(f"Duplicate payload hash detected for node {node_id}: {payload_hash}")

    # 1. Ensure SensorNode exists
    if not graph.get_node(node_id):
        sensor = SensorNode(
            id=node_id,
            farm_id=data["farm_id"],
            node_type=source.get("type", "sensor"),
            field_id=data.get("field_id"),
            zone_id=data.get("zone_id")
        )
        graph.add_node(sensor)
        
        if sensor.zone_id:
            graph.add_edge(node_id, "DEPLOYED_IN", sensor.zone_id)
        elif sensor.field_id:
            graph.add_edge(node_id, "DEPLOYED_IN", sensor.field_id)
            
    # 2. Ensure Measurement node exists
    meas_id = data["measurement_id"]
    if not graph.get_node(meas_id):
        measurement = Measurement(
            id=meas_id,
            farm_id=data["farm_id"],
            layer=data["layer"]
        )
        graph.add_node(measurement)
        graph.add_edge(meas_id, "INFORMS", f"ontology:{data['layer']}")
        
    # Link sensor to measurement
    graph.add_edge(node_id, "MEASURES", meas_id)
        
    # 3. Add Observation to the graph and the timeseries table
    obs = Observation(
        id=obs_id,
        farm_id=data["farm_id"],
        node_id=data["node_id"],
        timestamp=data["timestamp"],
        measurement_id=meas_id,
        layer=data["layer"],
        value=data["value"],
        unit=data.get("unit"),
        basis=data.get("measurement_basis", "direct"),
        confidence=data.get("confidence", "medium"),
        source=source
    )
    
    # Store in dedicated observation table for easy timeseries querying
    graph.storage.add_observation(
        obs.id, obs.node_id, obs.timestamp, obs.farm_id, 
        data.get("field_id"), data.get("zone_id"), 
        obs.measurement_id, obs.value, obs.layer, data,
        sequence=new_sequence, payload_hash=payload_hash
    )
    
    # Also link it in the graph for traversal
    graph.add_node(obs)
    graph.add_edge(obs.id, "PRODUCES", meas_id)
    
    return obs_id
