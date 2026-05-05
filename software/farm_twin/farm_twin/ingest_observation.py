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
    Atomic transaction: validates, checks anti-replay, inserts, and updates registry.
    """
    node_id = data["node_id"]
    obs_id = f"obs-{data['timestamp']}-{node_id}"
    source = data.get("source") or {}
    
    # WP25.1: Atomic Transaction Flow
    try:
        with graph.storage.transaction():
            # 1. Isolation & Status Check
            registry = graph.storage.get_node_registry(node_id)
            node_status = registry["status"] if registry else "pending"
            
            if node_status != "accepted":
                # Isolated storage path (still transactional for append-only)
                graph.storage.add_quarantined_observation(
                    obs_id, node_id, data["timestamp"], data["farm_id"],
                    data["measurement_id"], data["value"], data["layer"], data
                )
                return f"quarantined-{obs_id}"

            # 2. Anti-Replay & Sequence Check (Read-only check)
            new_sequence = data.get("sequence")
            if new_sequence is not None:
                last_sequence = registry.get("last_sequence") or 0
                if new_sequence <= last_sequence:
                    raise ValueError(f"Sequence replay detected for node {node_id}: {new_sequence} <= {last_sequence}")

            # 3. Payload Hash Check (Read-only check)
            payload_hash = data.get("payload_hash")
            if payload_hash:
                cursor = graph.storage.conn.cursor()
                cursor.execute("SELECT id FROM observations WHERE node_id = ? AND payload_hash = ?", (node_id, payload_hash))
                if cursor.fetchone():
                    raise ValueError(f"Duplicate payload hash detected for node {node_id}: {payload_hash}")

            # 4. Prepare Observation Model
            meas_id = data["measurement_id"]
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

            # 5. Mutate Storage (Observations table)
            # This is where IntegrityError is most likely to happen.
            graph.storage.add_observation(
                obs.id, obs.node_id, obs.timestamp, obs.farm_id, 
                data.get("field_id"), data.get("zone_id"), 
                obs.measurement_id, obs.value, obs.layer, data,
                sequence=new_sequence, payload_hash=payload_hash
            )

            # 6. Mutate Graph (Nodes and Edges)
            if not graph.get_node(node_id):
                sensor = SensorNode(
                    id=node_id, farm_id=data["farm_id"],
                    node_type=source.get("type", "sensor"),
                    field_id=data.get("field_id"), zone_id=data.get("zone_id")
                )
                graph.add_node(sensor)
                if sensor.zone_id:
                    graph.add_edge(node_id, "DEPLOYED_IN", sensor.zone_id)
                elif sensor.field_id:
                    graph.add_edge(node_id, "DEPLOYED_IN", sensor.field_id)

            if not graph.get_node(meas_id):
                measurement = Measurement(id=meas_id, farm_id=data["farm_id"], layer=data["layer"])
                graph.add_node(measurement)
                graph.add_edge(meas_id, "INFORMS", f"ontology:{data['layer']}")

            graph.add_edge(node_id, "MEASURES", meas_id)
            graph.add_node(obs)
            graph.add_edge(obs.id, "PRODUCES", meas_id)

            # 7. Final State Advancement (Only if everything above succeeded)
            graph.storage.update_node_registry(
                node_id=node_id, 
                last_seen=data["timestamp"],
                last_sequence=new_sequence
            )
            
            return obs_id

    except Exception:
        raise
        
    return obs_id
