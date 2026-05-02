from datetime import datetime, timezone
from .graph import FarmGraph
from .queries import get_zone_water_risk_summary

def generate_water_retention_card(graph: FarmGraph, farm_id: str, field_id: str, zone_id: str):
    """
    Generates a farmer-facing intelligence card regarding water retention.
    Saves the card to the database and returns the payload.
    """
    # Run the underlying intelligence query
    summary = get_zone_water_risk_summary(graph, farm_id, zone_id)
    
    # Build the card payload
    card = {
        "card_type": "WaterRetentionCard",
        "pfkr_id": "PFKR-1",
        "pfkr_domain": "Water Status and Movement",
        "title": f"Zone {zone_id}: Rainfall capture appears weak" if summary["status"] == "watch" else f"Zone {zone_id}: Water retention stable",
        "status": summary["status"],
        "location": {
            "farm_id": farm_id,
            "field_id": field_id,
            "zone_id": zone_id
        },
        "observation": "Soil moisture reading indicates potential runoff or poor infiltration." if summary["status"] == "watch" else "Soil moisture is adequate.",
        "context": summary["evidence"],
        "farmer_meaning": summary["farmer_meaning"],
        "suggested_inspection": summary["suggested_inspection"],
        "possible_interventions": [
            "Increase soil armor",
            "Delay grazing",
            "Add deep-rooting cover crop"
        ],
        "evidence": summary["evidence"],
        "confidence": summary["confidence"]
    }
    
    now = datetime.now(timezone.utc)
    card_id = f"card-water-{zone_id}"
    
    # Persist the card
    graph.storage.add_card(
        card_id=card_id,
        created_at=now.isoformat(),
        card_type=card["card_type"],
        status=card["status"],
        payload=card
    )
    
    return card

def generate_weather_context_card(graph: FarmGraph, farm_id: str, field_id: str, zone_id: str):
    """
    Generates a card summarizing weather conditions for the farm.
    """
    from .queries import get_zone_weather_summary
    
    summary = get_zone_weather_summary(graph, farm_id, zone_id)
    
    card = {
        "card_type": "WeatherContextCard",
        "pfkr_id": "PFKR-7",
        "pfkr_domain": "Weather and Exposure",
        "title": "Live Weather Context",
        "status": summary["status"],
        "location": {
            "farm_id": farm_id,
            "field_id": field_id,
            "zone_id": zone_id
        },
        "observation": summary["summary"],
        "context": summary["evidence"],
        "farmer_meaning": "Current atmospheric conditions impacting soil dynamics.",
        "suggested_inspection": "Monitor runoff if rainfall persists." if summary["rainfall_mm"] > 0 else "No immediate atmospheric action needed.",
        "possible_interventions": [
            "Check drainage channels",
            "Adjust irrigation schedule"
        ],
        "evidence": summary["evidence"],
        "confidence": "high"
    }
    
    now = datetime.now(timezone.utc)
    card_id = f"card-weather-{farm_id}"
    
    graph.storage.add_card(
        card_id=card_id,
        created_at=now.isoformat(),
        card_type=card["card_type"],
        status=card["status"],
        payload=card
    )
    
    return card

def generate_grazing_readiness_card(graph: FarmGraph, farm_id: str, paddock_id: str):
    """
    Generates a card for grazing readiness based on PFKR-2 doctrine.
    """
    from .queries import get_paddock_grazing_readiness
    
    summary = get_paddock_grazing_readiness(graph, farm_id, paddock_id)
    
    card = {
        "card_type": "GrazingReadinessCard",
        "pfkr_id": "PFKR-2",
        "pfkr_domain": "Grazing Readiness and Recovery",
        "title": f"Paddock {paddock_id}: Ready for grazing" if summary["status"] == "ok" else f"Paddock {paddock_id}: Readiness Alert",
        "status": summary["status"],
        "location": {
            "farm_id": farm_id,
            "paddock_id": paddock_id
        },
        "observation": summary["farmer_meaning"],
        "context": summary["evidence"],
        "farmer_meaning": summary["farmer_meaning"],
        "suggested_inspection": summary["suggested_inspection"],
        "possible_interventions": [
            "Wait for rest target",
            "Perform visual recovery score",
            "Adjust herd move schedule"
        ],
        "evidence": summary["evidence"],
        "confidence": summary["confidence"]
    }
    
    now = datetime.now(timezone.utc)
    card_id = f"card-grazing-{paddock_id}"
    
    graph.storage.add_card(
        card_id=card_id,
        created_at=now.isoformat(),
        card_type=card["card_type"],
        status=card["status"],
        payload=card
    )
    
    return card

