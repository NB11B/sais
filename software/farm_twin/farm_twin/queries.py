import json
from datetime import datetime, timedelta, timezone
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
    # We use the observation timestamp to filter.
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    cursor.execute("""
        SELECT payload_json FROM observations
        WHERE farm_id = ? AND measurement_id = 'weather.rainfall.hourly'
        AND timestamp > ?
        ORDER BY timestamp DESC LIMIT 1
    """, (farm_id, yesterday))
    rain_row = cursor.fetchone()
    if rain_row:
        rain_obs = json.loads(rain_row[0])
        val = rain_obs.get("value", 0)
        try:
            val_float = float(val)
            if val_float > 0:
                evidence.append(f"recent rainfall detected (last 24h): {val_float}mm")
        except (ValueError, TypeError):
            pass
    
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
    # We look for nodes with layer='Weather' or 'Atmosphere'
    query = """
        SELECT payload_json FROM observations
        WHERE farm_id = ? AND layer IN ('Weather', 'Atmosphere')
        ORDER BY timestamp DESC LIMIT 10
    """
    cursor.execute(query, (farm_id,))
    rows = cursor.fetchall()
    
    weather_data = {}
    for row in rows:
        obs = json.loads(row[0])
        m_id = obs.get("measurement_id")
        if m_id and m_id not in weather_data:
            # Check for staleness (e.g. > 12 hours)
            try:
                obs_time = datetime.fromisoformat(obs["timestamp"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - obs_time > timedelta(hours=12):
                    continue
                
                # Type safety for value
                val = obs.get("value")
                if val is not None:
                    weather_data[m_id] = obs
                    evidence.append(f"latest {m_id}: {val} {obs.get('unit', '')}")
            except (ValueError, KeyError, TypeError):
                continue
            
    if not weather_data:
        return {
            "status": "no_data",
            "evidence": ["no recent weather telemetry found"],
            "summary": "Weather station offline or not yet configured.",
            "rainfall_mm": 0,
            "temp_c": None
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

def get_paddock_grazing_readiness(graph: FarmGraph, farm_id: str, paddock_id: str):
    """
    Evaluates grazing readiness for a paddock based on rest period and environmental stress.
    PFKR-2: Grazing Readiness and Recovery
    """
    evidence = []
    
    # 1. Get Paddock Node (for rest target)
    paddock_node = graph.get_node(paddock_id)
    if not paddock_node:
        return {
            "status": "insufficient_data", 
            "evidence": [f"Paddock {paddock_id} not found"],
            "farmer_meaning": "Paddock configuration missing.",
            "suggested_inspection": "Register paddock in Admin.",
            "confidence": "low"
        }
    
    p_payload = paddock_node["payload"]
    rest_target = p_payload.get("rest_target_days")
    evidence.append(f"Rest target: {rest_target if rest_target else 'unspecified'} days")
    
    # 2. Get Latest Grazing Event
    latest_event = graph.storage.get_latest_grazing_event(paddock_id)
    if not latest_event:
        return {
            "status": "insufficient_data",
            "evidence": evidence + ["No grazing history recorded for this paddock"],
            "days_since_graze": None,
            "farmer_meaning": "Paddock status is unknown due to missing grazing history.",
            "suggested_inspection": "Log a past grazing event or perform a visual recovery check.",
            "confidence": "low"
        }
    
    started_at = datetime.fromisoformat(latest_event["started_at"].replace("Z", "+00:00"))
    days_since = (datetime.now(timezone.utc) - started_at).days
    evidence.append(f"Days since last graze: {days_since}")
    
    # 3. Environmental Context (Moisture/Temp)
    # Check for low moisture in the parent field/zones
    # For now, we query general farm weather as a proxy if zone moisture is missing
    weather = get_zone_weather_summary(graph, farm_id, paddock_id)
    temp_stress = False
    if weather["temp_c"] and weather["temp_c"] > 35:
        temp_stress = True
        evidence.append(f"High heat stress detected: {weather['temp_c']}C")
        
    # 4. Status Logic
    status = "ok"
    meaning = "Paddock appears recovered and ready for grazing."
    inspection = "Perform a standard visual check before moving herd."
    
    if rest_target:
        if days_since < rest_target:
            status = "not_ready"
            meaning = f"Paddock has only rested for {days_since} of {rest_target} target days."
            inspection = "Delay grazing to allow further plant recovery."
        elif days_since >= rest_target and temp_stress:
            status = "watch"
            meaning = "Rest target met, but high heat stress may limit actual regrowth."
            inspection = "Verify plant vigor and soil moisture before entry."
    else:
        status = "ok_with_warning"
        meaning = "Rest target not set, but grazing history exists."
        inspection = "Set a rest target in Admin for more precise readiness alerts."
        
    return {
        "paddock_id": paddock_id,
        "status": status,
        "evidence": evidence,
        "days_since_graze": days_since,
        "farmer_meaning": meaning,
        "suggested_inspection": inspection,
        "confidence": "high" if rest_target else "medium"
    }

def get_livestock_health_summary(graph: FarmGraph, paddock_id: str):
    """
    Summarizes recent livestock condition observations (BCS, Manure).
    PFKR-5: Livestock Health, Distribution, and Pressure
    """
    evidence = []
    obs = graph.storage.get_livestock_observations(paddock_id, limit=5)
    
    if not obs:
        return {
            "status": "insufficient_data",
            "evidence": ["No recent health observations found for this paddock"],
            "summary": "Health status indeterminate.",
            "confidence": "low"
        }
        
    latest = obs[0]
    bcs = latest.get("bcs")
    manure = latest.get("manure_score")
    
    if bcs: evidence.append(f"Latest BCS: {bcs}")
    if manure: evidence.append(f"Latest Manure Score: {manure}")
    
    status = "ok"
    if bcs and bcs < 2.5: 
        status = "watch"
        evidence.append("BCS is below optimal threshold (2.5)")
    if manure and manure < 3:
        status = "watch"
        evidence.append("Manure score indicates nutritional imbalance")
        
    return {
        "status": status,
        "evidence": evidence,
        "summary": f"Latest health check shows {status} condition." if status == "ok" else "Health warning detected.",
        "confidence": "medium"
    }

def get_livestock_heat_stress(graph: FarmGraph, farm_id: str, paddock_id: str):
    """
    Calculates Temperature-Humidity Index (THI) for livestock heat stress.
    PFKR-5/PFKR-7 Fusion
    """
    evidence = []
    weather = get_zone_weather_summary(graph, farm_id, paddock_id)
    
    temp = weather["temp_c"]
    # We need RH. Let's look for it specifically.
    rh = None
    cursor = graph.storage.conn.cursor()
    cursor.execute("""
        SELECT payload_json FROM observations 
        WHERE farm_id = ? AND measurement_id = 'weather.relative_humidity'
        ORDER BY timestamp DESC LIMIT 1
    """, (farm_id,))
    row = cursor.fetchone()
    if row:
        rh = json.loads(row[0]).get("value")
        
    if temp is None or rh is None:
        return {
            "status": "insufficient_data",
            "evidence": ["Missing temp or humidity for THI calculation"],
            "thi": None
        }
        
    # THI = (1.8 * T + 32) - (0.55 - 0.0055 * RH) * (1.8 * T - 26)
    thi = (1.8 * temp + 32) - (0.55 - 0.0055 * rh) * (1.8 * temp - 26)
    evidence.append(f"Temp: {temp}C, RH: {rh}%")
    evidence.append(f"Calculated THI: {round(thi, 1)}")
    
    status = "ok"
    if thi > 89: status = "alert"
    elif thi > 78: status = "action"
    elif thi > 71: status = "watch"
    
    return {
        "status": status,
        "evidence": evidence,
        "thi": thi,
        "farmer_meaning": "Livestock at risk of heat stress." if status != "ok" else "Atmospheric comfort is adequate.",
        "suggested_inspection": "Ensure water access and shade." if status != "ok" else "Standard monitoring."
    }

