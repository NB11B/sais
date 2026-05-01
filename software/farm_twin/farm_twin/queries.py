import json
from .graph import FarmGraph

def get_zone_water_risk_summary(graph: FarmGraph, farm_id: str, zone_id: str):
    """
    Query 1: Evaluates water risk for a given management zone.
    Returns the evidence chain needed to build a WaterRetentionCard.
    """
    evidence = []
    
    # 1. Check for geospatial layers on the farm
    has_runoff_risk = False
    layers = graph.get_edges(source_id=farm_id, edge_type="HAS_LAYER")
    for edge in layers:
        layer_id = edge["target_id"]
        if "runoff_risk" in layer_id:
            has_runoff_risk = True
            evidence.append("runoff_risk layer available for farm")
            
    # 2. Get latest moisture observation for this zone directly from the observations table
    latest_moisture = None
    is_valid_moisture = False
    
    cursor = graph.storage.conn.cursor()
    query = """
        SELECT payload_json FROM observations
        WHERE zone_id = ? AND measurement_id LIKE '%vwc%'
        ORDER BY timestamp DESC LIMIT 1
    """
    cursor.execute(query, (zone_id,))
    row = cursor.fetchone()
    
    if row:
        obs = json.loads(row[0])
        raw_val = obs.get("value")
        depth = obs.get("source", {}).get("depth_cm", "unknown")
        
        try:
            if raw_val is not None:
                latest_moisture = float(raw_val)
                is_valid_moisture = True
                evidence.append(f"soil moisture at {depth}cm is {latest_moisture}")
            else:
                evidence.append(f"soil moisture at {depth}cm is missing")
        except (ValueError, TypeError):
            evidence.append(f"soil moisture observation is non-numeric: {raw_val}")
    else:
        evidence.append("no soil moisture observations found for zone")
    
    # 3. Analyze status with explicit boundaries
    status = "ok"
    
    if not is_valid_moisture:
        if row:
            if raw_val is None:
                status = "insufficient_data"
            else:
                status = "invalid_data"
        else:
            status = "insufficient_data"
    elif not has_runoff_risk:
        if latest_moisture < 0.25:
            status = "ok_with_warning"
            evidence.append("moisture is low, but no spatial risk context available")
        else:
            status = "insufficient_context"
            evidence.append("moisture is ok, but no spatial risk context available")
    else:
        # We have both risk layer and valid moisture
        # Since we don't do spatial intersection yet, we just say it's available.
        # If we did intersection, we'd say "zone belongs to high-risk terrain class".
        if latest_moisture < 0.25:
            status = "watch"
            evidence.append("farm has risk layer and zone moisture is low (< 0.25)")
        elif latest_moisture == 0.25:
            status = "watch"
            evidence.append("farm has risk layer and zone moisture is exactly at threshold (0.25)")
        else:
            status = "ok"
            evidence.append("moisture is adequate (> 0.25)")
        
    return {
        "zone_id": zone_id,
        "risk_type": "water_retention",
        "status": status,
        "evidence": evidence,
        "farmer_meaning": "Water may not be entering or staying in the root zone." if "watch" in status else "Status is adequate or indeterminate.",
        "suggested_inspection": "Check for runoff, crusting, bare soil, or compaction." if "watch" in status else "Ensure sensors are online and spatial layers are ingested.",
        "confidence": "medium" if is_valid_moisture else "low"
    }
