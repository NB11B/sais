import os
import sys
import json
from fastapi import FastAPI, Request
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

DB_PATH = os.environ.get("SAIS_DB_PATH", os.path.join(sais_root, "sais.sqlite"))

def get_graph():
    return FarmGraph(DB_PATH)

@app.get("/")
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

@app.get("/api/cards")
async def get_cards():
    graph = get_graph()
    cursor = graph.storage.conn.cursor()
    # Fetch all cards sorted by newest
    cursor.execute("SELECT payload_json FROM cards ORDER BY created_at DESC")
    cards = []
    for row in cursor.fetchall():
        cards.append(json.loads(row[0]))
    graph.storage.conn.close()
    return {"cards": cards}

@app.get("/api/observations")
async def get_observations(limit: int = 20):
    graph = get_graph()
    cursor = graph.storage.conn.cursor()
    cursor.execute("SELECT payload_json FROM observations ORDER BY timestamp DESC LIMIT ?", (limit,))
    obs = []
    for row in cursor.fetchall():
        obs.append(json.loads(row[0]))
    graph.storage.conn.close()
    return {"observations": obs}

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
        
        if farm_id and zone_id:
            zone_node = graph.get_node(zone_id)
            field_id = zone_node["payload"].get("field_id") if zone_node else None
            
            if field_id:
                generate_water_retention_card(graph, farm_id, field_id, zone_id)
                
        return {"status": "success", "obs_id": obs_id}
    finally:
        graph.storage.conn.close()

@app.get("/api/graph")
async def get_graph_summary():
    graph = get_graph()
    cursor = graph.storage.conn.cursor()
    
    nodes = []
    cursor.execute("SELECT id, type, payload_json FROM nodes")
    for row in cursor.fetchall():
        payload = json.loads(row[2])
        nodes.append({
            "id": row[0],
            "labels": [row[1]],
            "name": payload.get("name", row[0])
        })
        
    cursor.execute("SELECT id, source_id, type, target_id FROM edges")
    edges = []
    for row in cursor.fetchall():
        edges.append({
            "id": row[0],
            "source_id": row[1],
            "type": row[2],
            "target_id": row[3]
        })
    
    # Just return nodes and edges
    summary = {
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges)
        }
    }
    
    graph.storage.conn.close()
    return summary

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
