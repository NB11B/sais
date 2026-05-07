import os
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

# Add farm_twin to python path
sais_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(sais_root, 'software', 'farm_twin'))

from farm_twin.graph import FarmGraph
from farm_twin.gis_registry import GisRegistry
from auth import require_admin, require_node_auth

app = FastAPI(title="SAIS Dashboard API")
gis_registry = GisRegistry()

# --- WP25: Security Middleware ---

# CORS: localhost only by default; LAN origins via SAIS_CORS_ORIGINS env
_cors_origins = os.environ.get("SAIS_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://*.tile.openstreetmap.org; "
            "connect-src 'self';"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Request body size limit (1 MB)
MAX_BODY_BYTES = int(os.environ.get("SAIS_MAX_BODY_BYTES", 1_048_576))

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return Response("Request body too large", status_code=413)
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware)

# Setup static and templates
base_dir = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

def get_graph():
    path = os.environ.get("SAIS_DB_PATH", os.path.join(sais_root, "sais.sqlite"))
    return FarmGraph(path)

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "active_page": "command"})

@app.get("/map")
async def map_page(request: Request):
    return templates.TemplateResponse(request=request, name="map.html", context={"request": request, "active_page": "map"})

@app.get("/assets")
async def assets_page(request: Request):
    return templates.TemplateResponse(request=request, name="assets.html", context={"request": request, "active_page": "assets"})

@app.get("/nodes")
async def nodes_page(request: Request):
    return templates.TemplateResponse(request=request, name="nodes.html", context={"request": request, "active_page": "nodes"})

@app.get("/network")
async def network_page(request: Request):
    return templates.TemplateResponse(request=request, name="network.html", context={"request": request, "active_page": "knowledge"})

@app.get("/api/cards")
async def get_cards(admin=Depends(require_admin)):
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
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
async def update_card_action(card_id: str, data: dict, admin=Depends(require_admin)):
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
async def get_observations(limit: int = 50, admin=Depends(require_admin)):
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

from schemas import ObservationPayload, PlantObservationPayload, SoilObservationPayload, InfrastructureStatusPayload

from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception):
    import traceback
    print(traceback.format_exc())
    detail = "Internal server error"
    if os.environ.get("SAIS_ENV") == "development":
        detail = str(exc)
    return JSONResponse(status_code=500, content={"detail": detail})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/observations")
async def post_observation(data: ObservationPayload, graph: FarmGraph = Depends(get_graph), auth=Depends(require_node_auth)):
    from farm_twin.ingest_observation import ingest_sensor_observation_payload
    from farm_twin.cards import generate_water_retention_card

    data = data.model_dump(by_alias=True)

    try:
        node_id = data.get("node_id")
        node_reg = graph.storage.get_node_registry(node_id) if node_id else None

        INTELLIGENCE_TIERS = {"accepted", "reference"}
        VALID_DATA_TIERS = {"accepted", "reference", "external"}
        source_tier = node_reg.get("source_tier", "pending") if node_reg else "pending"
        node_accepted = source_tier in INTELLIGENCE_TIERS
        data_valid = source_tier in VALID_DATA_TIERS

        if not data_valid:
            data["confidence"] = "quarantined"
        elif source_tier == "external" and not data.get("confidence"):
            data["confidence"] = "low"

        obs_id = ingest_sensor_observation_payload(graph, data)

        if node_accepted:
            farm_id = data.get("farm_id")
            zone_id = data.get("zone_id")
            field_id = data.get("field_id")
            paddock_id = data.get("paddock_id")
            layer = data.get("layer")

            if farm_id:
                if zone_id and not field_id:
                    zone_node = graph.get_node(zone_id)
                    field_id = zone_node["payload"].get("field_id") if zone_node else None

                from farm_twin.cards import generate_diagnostic_cards
                generate_diagnostic_cards(
                    graph, farm_id,
                    field_id=field_id,
                    zone_id=zone_id,
                    paddock_id=paddock_id
                )

                if layer == "Weather":
                    from farm_twin.cards import generate_weather_context_card
                    generate_weather_context_card(graph, farm_id, field_id, zone_id)
                elif layer == "SoilPhysics" or layer == "SoilWater":
                    if field_id and zone_id:
                        generate_water_retention_card(graph, farm_id, field_id, zone_id)

            from farm_twin.cards import generate_ranch_health_card, generate_source_health_card
            generate_source_health_card(graph, farm_id)
            generate_ranch_health_card(graph, farm_id)

        return {
            "status": "success",
            "obs_id": obs_id,
            "quarantined": not data_valid,
            "intelligence_triggered": node_accepted,
        }
    finally:
        graph.storage.conn.close()

@app.get("/api/gis/assets")
async def get_gis_assets():
    return {"assets": gis_registry.get_asset_list()}

@app.get("/api/gis/data/{asset_id}")
async def get_gis_data(asset_id: str):
    data = gis_registry.get_asset_data(asset_id)
    if not data:
        raise HTTPException(status_code=404, detail="GIS asset not found or data missing")
    return data

@app.get("/api/graph")
async def get_graph_summary(admin=Depends(require_admin)):
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
        nodes = []
        cursor.execute("SELECT id, type, payload_json FROM nodes")
        for row in cursor.fetchall():
            payload = json.loads(row[2]) if row[2] else {}
            nodes.append({"id": row[0], "name": payload.get("name", row[0]), "labels": [row[1]], "payload": payload})

        cursor.execute("SELECT id, source_id, type, target_id FROM edges")
        edges = []
        for row in cursor.fetchall():
            edges.append({"id": row[0], "source": row[1], "type": row[2], "target": row[3]})
        return {"nodes": nodes, "edges": edges, "counts": {"nodes": len(nodes), "edges": len(edges)}}
    finally:
        graph.storage.conn.close()

@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"request": request, "active_page": "admin"})

from schemas import FarmPayload, FieldPayload, ZonePayload, PaddockPayload, SensorNodePayload, GrazingEventPayload, LivestockObservationPayload
from schemas import InfrastructureAssetPayload, WaterAssetPayload, NodeHelloPayload, NodeAssignmentPayload, NodeAcceptPayload
from farm_twin.models import Farm, Field, ManagementZone, Paddock, SensorNode, GrazingEvent, LivestockObservation

@app.get("/api/sources")
async def get_sources():
    from farm_twin.source_registry import registry
    return {"sources": registry.list_sources()}

@app.get("/api/layers")
async def get_layers():
    from farm_twin.layer_registry import registry
    return {"layers": registry.list_layers()}

@app.get("/api/farm/profile")
async def get_farm_profile(admin=Depends(require_admin)):
    graph = get_graph()
    try:
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
async def put_farm_profile(payload: FarmPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        farm = Farm(**payload.model_dump())
        graph.add_node(farm)
        return {"status": "success", "id": farm.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/fields")
@app.put("/api/farm/fields/{field_id}")
async def post_farm_field(payload: FieldPayload, field_id: str = None, admin=Depends(require_admin)):
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
async def post_farm_zone(payload: ZonePayload, zone_id: str = None, admin=Depends(require_admin)):
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
async def post_farm_paddock(payload: PaddockPayload, paddock_id: str = None, admin=Depends(require_admin)):
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

@app.get("/api/grazing/events")
async def get_grazing_events(paddock_id: str = None):
    graph = get_graph()
    try:
        cursor = graph.storage.conn.cursor()
        query = "SELECT payload_json FROM grazing_events"
        params = []
        if paddock_id:
            query += " WHERE paddock_id = ?"
            params.append(paddock_id)
        query += " ORDER BY started_at DESC"
        cursor.execute(query, params)
        return {"events": [json.loads(row[0]) for row in cursor.fetchall()]}
    finally:
        graph.storage.conn.close()

@app.post("/api/grazing/events")
async def post_grazing_event(payload: GrazingEventPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        if not graph.get_node(payload.paddock_id):
            raise HTTPException(status_code=400, detail="Paddock ID does not exist")
        graph.storage.add_grazing_event(
            event_id=payload.event_id,
            farm_id=payload.farm_id,
            field_id=payload.field_id,
            paddock_id=payload.paddock_id,
            started_at=payload.started_at,
            ended_at=payload.ended_at,
            animal_count=payload.animal_count,
            notes=payload.notes,
            payload=payload.model_dump(by_alias=True)
        )
        graph.add_edge(payload.paddock_id, "HOSTED_EVENT", payload.event_id)
        from farm_twin.cards import generate_grazing_readiness_card
        generate_grazing_readiness_card(graph, payload.farm_id, payload.paddock_id)
        return {"status": "success", "id": payload.event_id}
    finally:
        graph.storage.conn.close()

@app.post("/api/livestock/observations")
async def post_livestock_observation(payload: LivestockObservationPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        if not graph.get_node(payload.paddock_id):
            raise HTTPException(status_code=400, detail=f"Paddock {payload.paddock_id} does not exist")
        if payload.bcs is not None and (payload.bcs < 1 or payload.bcs > 9):
            raise HTTPException(status_code=400, detail="BCS must be between 1 and 9")
        if payload.manure_score is not None and (payload.manure_score < 1 or payload.manure_score > 5):
            raise HTTPException(status_code=400, detail="Manure score must be between 1 and 5")
        graph.storage.add_livestock_observation(payload.id, payload.farm_id, payload.paddock_id, payload.timestamp, payload.bcs, payload.manure_score, payload.model_dump())
        graph.add_edge(payload.paddock_id, "LIVESTOCK_CHECK", payload.id)
        from farm_twin.cards import generate_livestock_condition_card, generate_heat_stress_card
        generate_livestock_condition_card(graph, payload.farm_id, payload.paddock_id)
        generate_heat_stress_card(graph, payload.farm_id, payload.paddock_id)
        return {"status": "success", "id": payload.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/farm/sensor-nodes")
@app.put("/api/farm/sensor-nodes/{node_id}")
async def post_sensor_node(payload: SensorNodePayload, node_id: str = None, admin=Depends(require_admin)):
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

@app.post("/api/plant/observations")
async def post_plant_observation(payload: PlantObservationPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        if not graph.get_node(payload.paddock_id):
            raise HTTPException(status_code=400, detail=f"Paddock {payload.paddock_id} does not exist")
        graph.storage.add_plant_observation(payload.id, payload.farm_id, payload.paddock_id, payload.timestamp, payload.forage_mass_kg_ha, payload.cover_percent, payload.height_cm, payload.recovery_score, payload.model_dump())
        graph.add_edge(payload.paddock_id, "PLANT_CHECK", payload.id)
        from farm_twin.cards import generate_forage_balance_card, generate_plant_recovery_card, generate_grazing_readiness_card, generate_ranch_health_card
        generate_forage_balance_card(graph, payload.farm_id, payload.paddock_id)
        generate_plant_recovery_card(graph, payload.farm_id, payload.paddock_id)
        generate_grazing_readiness_card(graph, payload.farm_id, payload.paddock_id)
        generate_ranch_health_card(graph, payload.farm_id)
        return {"status": "success", "id": payload.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/soil/observations")
async def post_soil_observation(payload: SoilObservationPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        graph.storage.add_soil_observation(payload.id, payload.farm_id, payload.paddock_id, payload.timestamp, payload.infiltration_mm_hr, payload.model_dump())
        if payload.paddock_id:
            graph.add_edge(payload.paddock_id, "SOIL_TEST", payload.id)
        from farm_twin.cards import generate_soil_function_card, generate_ranch_health_card, generate_plant_recovery_card
        generate_soil_function_card(graph, payload.farm_id, payload.paddock_id)
        if payload.paddock_id:
            generate_plant_recovery_card(graph, payload.farm_id, payload.paddock_id)
        generate_ranch_health_card(graph, payload.farm_id)
        return {"status": "success", "id": payload.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/infrastructure/status")
async def post_infrastructure_status(payload: InfrastructureStatusPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        graph.storage.add_infrastructure_asset(payload.id, payload.farm_id, payload.asset_type, payload.status, payload.model_dump())
        node = graph.get_node(payload.id)
        if node:
            node["payload"]["status"] = payload.status
            graph.storage.add_node(payload.id, node.get("type", "InfrastructureAsset"), node["payload"])
        from farm_twin.cards import generate_infrastructure_alert_card, generate_ranch_health_card
        generate_infrastructure_alert_card(graph, payload.farm_id)
        generate_ranch_health_card(graph, payload.farm_id)
        return {"status": "success", "id": payload.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/infrastructure/asset")
async def post_infrastructure_asset(payload: InfrastructureAssetPayload, admin=Depends(require_admin)):
    from farm_twin.models import InfrastructureAsset
    graph = get_graph()
    try:
        data = payload.model_dump()
        asset = InfrastructureAsset(id=data["id"], farm_id=data["farm_id"], asset_type=data["asset_type"], name=data.get("name", data["id"]), status=data.get("status", "unknown"), location_geojson=data.get("location_geojson"), notes=data.get("notes"))
        graph.add_node(asset)
        graph.storage.add_infrastructure_asset(asset.id, asset.farm_id, asset.asset_type, asset.status, data)
        return {"status": "success", "id": asset.id}
    finally:
        graph.storage.conn.close()

@app.post("/api/infrastructure/water")
async def post_water_asset(payload: WaterAssetPayload, admin=Depends(require_admin)):
    from farm_twin.models import WaterAsset
    graph = get_graph()
    try:
        data = payload.model_dump()
        asset = WaterAsset(id=data["id"], farm_id=data["farm_id"], asset_type=data["asset_type"], name=data["name"], location=data.get("location"))
        graph.add_node(asset)
        return {"status": "success", "id": asset.id}
    finally:
        graph.storage.conn.close()

# --- WP19 Node Provisioning API ---

@app.post("/api/nodes/hello")
async def node_hello(payload: NodeHelloPayload):
    node_id = payload.id
    graph = get_graph()
    try:
        now = datetime.now(timezone.utc).isoformat()
        existing = graph.storage.get_node_registry(node_id)
        data = payload.model_dump()
        if not existing:
            graph.storage.update_node_registry(node_id=node_id, status="pending", first_seen=now, last_seen=now, capabilities=payload.capabilities or {}, payload=data)
        else:
            graph.storage.update_node_registry(node_id=node_id, last_seen=now, payload=data)
        return {"status": "success", "node_id": node_id}
    finally:
        graph.storage.conn.close()

@app.get("/api/nodes/pending")
async def get_pending_nodes(admin=Depends(require_admin)):
    graph = get_graph()
    try:
        return {"nodes": graph.storage.get_nodes_by_status("pending")}
    finally:
        graph.storage.conn.close()

@app.get("/api/nodes/active")
async def get_active_nodes(admin=Depends(require_admin)):
    graph = get_graph()
    try:
        return {"nodes": graph.storage.get_nodes_by_status("accepted")}
    finally:
        graph.storage.conn.close()

@app.post("/api/nodes/{node_id}/accept")
async def accept_node(node_id: str, payload: NodeAcceptPayload = None, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        tier = payload.source_tier if payload else "accepted"
        graph.storage.update_node_registry(node_id, status="accepted", source_tier=tier)
        return {"status": "success", "node_id": node_id, "source_tier": tier}
    finally:
        graph.storage.conn.close()

@app.post("/api/nodes/{node_id}/reject")
async def reject_node(node_id: str, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        graph.storage.update_node_registry(node_id, status="rejected", source_tier="rejected")
        return {"status": "success", "node_id": node_id}
    finally:
        graph.storage.conn.close()

@app.put("/api/nodes/{node_id}/assignment")
async def update_node_assignment(node_id: str, data: NodeAssignmentPayload, admin=Depends(require_admin)):
    graph = get_graph()
    try:
        assignment = data.model_dump(exclude_none=True)
        graph.storage.update_node_registry(node_id=node_id, role=assignment.get("role"), farm_id=assignment.get("farm_id"), field_id=assignment.get("field_id"), zone_id=assignment.get("zone_id"), paddock_id=assignment.get("paddock_id"), asset_id=assignment.get("asset_id"), config=assignment.get("config", {}))
        reg = graph.storage.get_node_registry(node_id)
        if reg and reg["status"] == "accepted":
            sensor = SensorNode(id=node_id, farm_id=reg.get("farm_id", "local"), node_type=reg.get("role_template", "sensor"), field_id=reg.get("field_id"), zone_id=reg.get("zone_id"), location=data.location)
            graph.add_node(sensor)
            if sensor.zone_id:
                graph.add_edge(node_id, "DEPLOYED_IN", sensor.zone_id)
        return {"status": "success", "node_id": node_id}
    finally:
        graph.storage.conn.close()

@app.get("/api/nodes/roles")
async def get_node_roles(admin=Depends(require_admin)):
    from farm_twin.provisioning import get_all_roles
    return {"roles": get_all_roles()}

if __name__ == "__main__":
    import uvicorn
    bind_host = "0.0.0.0" if os.environ.get("SAIS_BIND_LAN") == "true" else "127.0.0.1"
    reload_mode = os.environ.get("SAIS_ENV") != "production"
    port = int(os.environ.get("SAIS_PORT", 8000))
    print(f"SAIS Dashboard binding to {bind_host}:{port} (LAN={'enabled' if bind_host == '0.0.0.0' else 'disabled'})")
    uvicorn.run("main:app", host=bind_host, port=port, reload=reload_mode)
