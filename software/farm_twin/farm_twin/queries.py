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

    # 2b. Check for recent rainfall (last 24h context)
    cursor.execute("""
        SELECT payload_json FROM observations
        WHERE farm_id = ? AND measurement_id = 'weather.rainfall.hourly'
        ORDER BY timestamp DESC LIMIT 1
    """, (farm_id,))
    rain_row = cursor.fetchone()
    if rain_row:
        rain_obs = json.loads(rain_row[0])
        val = rain_obs.get("value", 0)
        if val > 0:
            evidence.append(f"recent rainfall detected: {val}mm")
    
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

def get_zone_weather_summary(graph: FarmGraph, farm_id: str, zone_id: str):
    """
    Evaluates latest weather context for a given zone.
    """
    evidence = []
    cursor = graph.storage.conn.cursor()
    
    # Query latest weather observations (Rainfall, Temp, Humidity, Wind)
    # We look for nodes with layer='Weather'
    query = """
        SELECT payload_json FROM observations
        WHERE farm_id = ? AND layer = 'Weather'
        ORDER BY timestamp DESC LIMIT 5
    """
    cursor.execute(query, (farm_id,))
    rows = cursor.fetchall()
    
    weather_data = {}
    for row in rows:
        obs = json.loads(row[0])
        m_id = obs.get("measurement_id")
        if m_id not in weather_data:
            weather_data[m_id] = obs
            evidence.append(f"latest {m_id}: {obs.get('value')} {obs.get('unit', '')}")
            
    if not weather_data:
        return {
            "status": "no_data",
            "evidence": ["no recent weather telemetry found"],
            "summary": "Weather station offline or not yet configured."
        }
        
    # Simple logic for WeatherContextCard
    # Example: rainfall > 0 in last hour?
    rainfall = weather_data.get("weather.rainfall.hourly", {}).get("value", 0)
    temp = weather_data.get("weather.air_temperature", {}).get("value")
    
    status = "ok"
    if rainfall > 10: status = "action" # Heavy rain
    elif rainfall > 0: status = "ok_with_warning" # Rain detected
    
    summary_text = "Standard conditions."
    if rainfall > 0:
        summary_text = f"Rainfall detected ({rainfall}mm). Soil moisture expected to rise."
        
    return {
        "status": status,
        "evidence": evidence,
        "summary": summary_text,
        "rainfall_mm": rainfall,
        "temp_c": temp
    }

