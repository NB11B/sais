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
            evidence.append("runoff_risk layer exists")
            
    # 2. Get latest moisture observation for this zone directly from the observations table
    latest_moisture = None
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
        latest_moisture = obs.get("value")
        depth = obs.get("source", {}).get("depth_cm", "unknown")
        evidence.append(f"soil moisture at {depth}cm is {latest_moisture}")
    
    # 3. Analyze status (heuristic for MVP)
    status = "ok"
    if has_runoff_risk and latest_moisture is not None and latest_moisture < 0.25:
        status = "watch"
        evidence.append("zone belongs to high-risk terrain class and moisture is low")
        
    return {
        "zone_id": zone_id,
        "risk_type": "water_retention",
        "status": status,
        "evidence": evidence,
        "farmer_meaning": "Water may not be entering or staying in the root zone.",
        "suggested_inspection": "Check for runoff, crusting, bare soil, or compaction.",
        "confidence": "medium"
    }
