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
    card_id = f"card-water-{zone_id}-{now.strftime('%Y%m%d%H%M%S')}"
    
    # Persist the card
    graph.storage.add_card(
        card_id=card_id,
        created_at=now.isoformat(),
        card_type=card["card_type"],
        status=card["status"],
        payload=card
    )
    
    return card
