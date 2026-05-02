import os
import sys
import json
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add farm_twin to python path
sais_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(sais_root, 'software', 'farm_twin'))

from farm_twin.graph import FarmGraph

app = FastAPI(title="SAIS Dashboard API")

# Setup static and templates
base_dir = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

def get_graph():
    path = os.environ.get("SAIS_DB_PATH", os.path.join(sais_root, "sais.sqlite"))
    return FarmGraph(path)

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/map")
async def map_page(request: Request):
    return templates.TemplateResponse(request=request, name="map.html", context={"request": request})

@app.get("/network")
async def network_page(request: Request):
    return templates.TemplateResponse(request=request, name="network.html", context={"request": request})

@app.get("/api/cards")
async def get_cards():
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
        # Fetch all cards sorted by newest
        cursor.execute("SELECT payload_json, action_status, notes, updated_at, id FROM cards ORDER BY created_at DESC")
        cards = []
        for row in cursor.fetchall():
            card = json.loads(row[0])
            card["action_status"] = row[1]
            card["notes"] = row[2]
            card["updated_at"] = row[3]
            card["id"] = row[4]
            cards.append(card)
        return {"cards": cards}
    finally:
        graph.storage.conn.close()

@app.post("/api/cards/{card_id}/action")
async def update_card_action(card_id: str, data: dict):
    graph = get_graph()
    try:
        status = data.get("status", "pending")
        notes = data.get("notes", "")
        now = datetime.now(timezone.utc).isoformat()
        
        graph.storage.update_card_action(card_id, status, notes, now)
        return {"status": "success", "card_id": card_id}
    finally:
        graph.storage.conn.close()

@app.get("/api/observations")
async def get_observations(limit: int = 20):
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
        cursor.execute("SELECT payload_json FROM observations ORDER BY timestamp DESC LIMIT ?", (limit,))
        obs = []
        for row in cursor.fetchall():
            obs.append(json.loads(row[0]))
        return {"observations": obs}
    finally:
        graph.storage.conn.close()

from schemas import ObservationPayload

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/observations")
async def post_observation(payload: ObservationPayload):
    from farm_twin.ingest_observation import ingest_sensor_observation_payload
    from farm_twin.cards import generate_water_retention_card
    
    data = payload.model_dump(by_alias=True)
    graph = get_graph()
    
    try:
        # Ingest the observation directly
        obs_id = ingest_sensor_observation_payload(graph, data)
        
        # Trigger intelligence rule if it relates to water/moisture
        farm_id = data.get("farm_id")
        zone_id = data.get("zone_id")
        layer = data.get("layer")
        
        if farm_id:
            # For cards that need a zone/field, we try to resolve them.
            # Weather cards are often farm-wide but we'll link to a zone if available for the location object.
            field_id = data.get("field_id")
            if zone_id and not field_id:
                zone_node = graph.get_node(zone_id)
                field_id = zone_node["payload"].get("field_id") if zone_node else None
            
            if layer == "Weather":
                from farm_twin.cards import generate_weather_context_card
                generate_weather_context_card(graph, farm_id, field_id, zone_id)
                # Rainfall also impacts water retention
                if field_id and zone_id:
                    generate_water_retention_card(graph, farm_id, field_id, zone_id)
            elif field_id and zone_id:
                generate_water_retention_card(graph, farm_id, field_id, zone_id)
                
        return {"status": "success", "obs_id": obs_id}
    finally:
        graph.storage.conn.close()

@app.get("/api/graph")
async def get_graph_summary():
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
        nodes = []
        cursor.execute("SELECT id, type, payload_json FROM nodes")
        for row in cursor.fetchall():
            payload = json.loads(row[2]) if row[2] else {}
            nodes.append({
                "id": row[0],
                "name": payload.get("name", row[0]),
                "labels": [row[1]],
                "payload": payload
            })
            
        cursor.execute("SELECT id, source_id, type, target_id FROM edges")
        edges = []
        for row in cursor.fetchall():
            edges.append({
                "id": row[0],
                "source": row[1],
                "type": row[2],
                "target": row[3]
            })
        
        summary = {
            "nodes": nodes,
            "edges": edges,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges)
            }
        }
        return summary
    finally:
        graph.storage.conn.close()

@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"request": request})

from schemas import FarmPayload, FieldPayload, ZonePayload, PaddockPayload, SensorNodePayload
from farm_twin.models import Farm, Field, ManagementZone, Paddock, SensorNode

@app.get("/api/sources")
async def get_sources():
    from farm_twin.source_registry import registry
    return {"sources": registry.list_sources()}

@app.get("/api/layers")
async def get_layers():
    from farm_twin.layer_registry import registry
    return {"layers": registry.list_layers()}

@app.get("/api/farm/profile")
async def get_farm_profile():
    graph = get_graph()
    try:
        # Simple assembly of the farm hierarchy from nodes
        nodes = {"Farm": [], "Field": [], "ManagementZone": [], "Paddock": [], "SensorNode": []}
        cursor = graph.storage.conn.cursor()
        cursor.execute("SELECT type, payload_json FROM nodes")
        for row in cursor.fetchall():
            ntype = row[0]
            payload = json.loads(row[1]) if row[1] else {}
            if ntype in nodes:
                nodes[ntype].append(payload)
        return nodes
    finally:
        graph.storage.conn.close()

@app.put("/api/farm/profile")
async def put_farm_profile(payload: FarmPayload):
    graph = get_graph()
    try:
        farm = Farm(**payload.model_dump())
        graph.add_node(farm)
        return {"status": "success", "id": farm.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/fields")
@app.put("/api/farm/fields/{field_id}")
async def post_farm_field(payload: FieldPayload, field_id: str = None):
    if field_id and field_id != payload.id:
        raise HTTPException(status_code=400, detail="Path ID does not match payload ID")
    graph = get_graph()
    try:
        if not graph.get_node(payload.farm_id):
            raise HTTPException(status_code=400, detail="Parent farm_id does not exist")
        field = Field(**payload.model_dump())
        graph.add_node(field)
        graph.add_edge(field.farm_id, "CONTAINS", field.id)
        return {"status": "success", "id": field.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/zones")
@app.put("/api/farm/zones/{zone_id}")
async def post_farm_zone(payload: ZonePayload, zone_id: str = None):
    if zone_id and zone_id != payload.id:
        raise HTTPException(status_code=400, detail="Path ID does not match payload ID")
    graph = get_graph()
    try:
        if not graph.get_node(payload.field_id):
            raise HTTPException(status_code=400, detail="Parent field_id does not exist")
        zone = ManagementZone(**payload.model_dump())
        graph.add_node(zone)
        graph.add_edge(zone.field_id, "CONTAINS", zone.id)
        return {"status": "success", "id": zone.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/paddocks")
@app.put("/api/farm/paddocks/{paddock_id}")
async def post_farm_paddock(payload: PaddockPayload, paddock_id: str = None):
    if paddock_id and paddock_id != payload.id:
        raise HTTPException(status_code=400, detail="Path ID does not match payload ID")
    graph = get_graph()
    try:
        if not graph.get_node(payload.field_id):
            raise HTTPException(status_code=400, detail="Parent field_id does not exist")
        paddock = Paddock(**payload.model_dump())
        graph.add_node(paddock)
        graph.add_edge(paddock.field_id, "CONTAINS", paddock.id)
        return {"status": "success", "id": paddock.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/sensor-nodes")
@app.put("/api/farm/sensor-nodes/{node_id}")
async def post_sensor_node(payload: SensorNodePayload, node_id: str = None):
    if node_id and node_id != payload.id:
        raise HTTPException(status_code=400, detail="Path ID does not match payload ID")
    graph = get_graph()
    try:
        if payload.zone_id and not graph.get_node(payload.zone_id):
            raise HTTPException(status_code=400, detail="zone_id does not exist")
        if payload.field_id and not graph.get_node(payload.field_id):
            raise HTTPException(status_code=400, detail="field_id does not exist")
            
        sensor = SensorNode(**payload.model_dump())
        graph.add_node(sensor)
        if sensor.zone_id:
            graph.add_edge(sensor.id, "DEPLOYED_IN", sensor.zone_id)
        elif sensor.field_id:
            graph.add_edge(sensor.id, "DEPLOYED_IN", sensor.field_id)
        return {"status": "success", "id": sensor.id}
    finally:
        graph.storage.conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
