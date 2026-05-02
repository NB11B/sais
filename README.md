# Sovereign Ag-Infrastructure Stack (SAIS)

> **A sovereign, offline-first C4ISR platform for farm and ranch operations.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-green.svg)]()
[![Architecture: Offline First](https://img.shields.io/badge/Architecture-Offline%20First-orange.svg)]()
[![Stack: FastAPI + SQLite](https://img.shields.io/badge/Stack-FastAPI%20%2B%20SQLite-purple.svg)]()

SAIS is an open-source, edge-native command platform for farms, ranches, and closed-loop resource environments. It fuses low-cost sensors, manual farmer observations, open geospatial data, weather data, soil context, and live telemetry into a local farm digital twin.

The purpose is simple:

```text
all sources
→ farm digital twin
→ fused intelligence
→ farmer-facing decision cards
→ auditable action loop
```

SAIS is being designed as the farm/ranch equivalent of a C4ISR system:

| C4ISR Function | SAIS Equivalent |
|---|---|
| Command | Operator dashboard, Admin setup, decision cards |
| Control | Future relays, valves, pumps, gates, and actuator workflows |
| Communications | Sensor telemetry API, future LoRa/BLE/MQTT/serial bridges |
| Computers | FarmGraph, SQLite, geospatial ingest, local FastAPI dashboard |
| Intelligence | Runoff risk, water-retention alerts, future grazing and plant-stress cards |
| Surveillance | Soil sensors, weather, tanks, livestock, cameras, and field observations |
| Reconnaissance | Farmer field walks, manual notes, satellite/geospatial layers |

**The farmer owns the hardware. The farmer owns the data. The farmer owns the intelligence.**

---

## Current Status

SAIS now has a working local vertical slice:

```text
open geospatial data
+ farm profile / GeoJSON boundaries
+ live sensor observations
→ SQLite-backed FarmGraph
→ intelligence cards
→ Operator Feed, GIS Twin, Knowledge Graph, and Admin Setup UI
```

Implemented so far:

| Work Package | Status | What exists |
|---|---:|---|
| WP2: Geospatial Ingest | Implemented | Offline DEM/SSURGO processing, slope, aspect, flow accumulation, runoff risk, manifest output |
| WP3: Farm Digital Twin Core Graph | Implemented | Typed graph model, SQLite storage, geospatial manifest ingest, observation ingest, card generation |
| WP3.5: Verification Harness | Implemented | Persistence tests, degraded-state tests, geospatial tests, end-to-end WP2 to WP3 test |
| WP4: Dashboard/API | Implemented | FastAPI dashboard, Operator Feed, API routes, seeded demo database |
| WP5: Live Sensor Ingestion | Implemented | `POST /api/observations`, direct payload ingest, card regeneration |
| WP5.5: Ingestion Reliability | Implemented | Pydantic validation, duplicate handling, card idempotency, `/health`, concurrency tests |
| WP8: Admin Setup and Layer Control | Implemented MVP | Admin setup wizard, farm CRUD endpoints, GeoJSON boundary input, GIS layer toggles |

Not yet implemented:

```text
real ESP32/UNO Q field firmware client
signed node telemetry
LoRa/BLE/MQTT field bridge
weather source registry
source/layer registry
interactive polygon drawing
offline local tile package
actuator control
cryptographic audit ledger
LLM/RAG layer
```

The current implementation is intentionally local, inspectable, and offline-first.

---

## System Architecture

```text
                ┌──────────────────────────┐
                │   Open Geospatial Data    │
                │ DEM, SSURGO, hydrology    │
                └─────────────┬────────────┘
                              │
                              ▼
                ┌──────────────────────────┐
                │ Geospatial Ingest Pipeline│
                │ slope, aspect, flow risk │
                └─────────────┬────────────┘
                              │ manifest.json
                              ▼
┌───────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│ Admin Setup   │ ──▶ │ SQLite FarmGraph      │ ◀── │ Live Observations     │
│ boundaries,   │     │ nodes, edges, cards,  │     │ /api/observations     │
│ zones, nodes  │     │ observations          │     │ sensors/weather/manual│
└───────────────┘     └──────────┬───────────┘     └──────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Intelligence Card Engine │
                    │ water retention now,     │
                    │ grazing/weather later    │
                    └──────────┬──────────────┘
                               │
                               ▼
        ┌────────────────────────────────────────────────────┐
        │ Dashboard                                           │
        │ Operator Feed | GIS Twin | Knowledge Graph | Admin  │
        └────────────────────────────────────────────────────┘
```

---

## Main Dashboard Views

### Operator Feed

Daily decision cockpit. Shows current intelligence cards, latest observations, status, evidence chains, and suggested inspections.

Default route:

```text
/
```

### GIS Twin

Spatial farm view. Renders farm boundaries, fields, management zones, paddocks, and sensor markers using GeoJSON stored in the FarmGraph.

Route:

```text
/map
```

### Knowledge Graph

Semantic and audit/debug view. Shows how farms, fields, zones, sensors, observations, measurements, geospatial layers, and cards connect.

Route:

```text
/network
```

### Admin Setup

Farm configuration interface. Used to define farm identity, boundaries, fields, zones, paddocks, and sensor nodes without manually editing seed files.

Route:

```text
/admin
```

---

## Quick Start: Dashboard Demo

From the repository root:

```bash
cd software/dashboard
pip install -r requirements.txt
python seed_db.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open:

```text
http://localhost:8000
```

Useful routes:

```text
http://localhost:8000/          Operator Feed
http://localhost:8000/map       GIS Twin
http://localhost:8000/network   Knowledge Graph
http://localhost:8000/admin     Admin Setup
http://localhost:8000/health    API health check
```

---

## Live Sensor Observation API

SAIS accepts live telemetry through:

```text
POST /api/observations
```

Example `sais.observation.v1` payload:

```json
{
  "schema": "sais.observation.v1",
  "node_id": "soil-node-001",
  "farm_id": "local",
  "field_id": "field-a",
  "zone_id": "zone-a1",
  "timestamp": "2026-05-02T12:00:00Z",
  "measurement_id": "soil.moisture.vwc",
  "layer": "SoilPhysics",
  "value": 0.21,
  "unit": "m3/m3",
  "measurement_basis": "direct",
  "confidence": "medium",
  "source": {
    "type": "sensor",
    "sensor_model": "simulated-capacitive-probe",
    "depth_cm": 30
  }
}
```

Minimal curl example:

```bash
curl -X POST http://localhost:8000/api/observations \
  -H "Content-Type: application/json" \
  -d '{
    "schema": "sais.observation.v1",
    "node_id": "soil-node-001",
    "farm_id": "local",
    "field_id": "field-a",
    "zone_id": "zone-a1",
    "timestamp": "2026-05-02T12:00:00Z",
    "measurement_id": "soil.moisture.vwc",
    "layer": "SoilPhysics",
    "value": 0.21,
    "unit": "m3/m3",
    "measurement_basis": "direct",
    "confidence": "medium"
  }'
```

The API validates the payload, stores the observation, updates the graph, and regenerates applicable decision cards.

---

## Admin Farm Configuration API

The Admin UI uses the same graph-backed endpoints that live setup workflows will use.

```text
GET  /api/farm/profile
PUT  /api/farm/profile
POST /api/farm/fields
PUT  /api/farm/fields/{field_id}
POST /api/farm/zones
PUT  /api/farm/zones/{zone_id}
POST /api/farm/paddocks
PUT  /api/farm/paddocks/{paddock_id}
POST /api/farm/sensor-nodes
PUT  /api/farm/sensor-nodes/{node_id}
```

Admin changes write directly to the FarmGraph SQLite database. The GIS Twin and Knowledge Graph read from the same state.

---

## Offline Geospatial Ingest Pipeline

The geospatial pipeline is designed as a provisioning pipeline that runs on a laptop or setup machine. This keeps heavy GIS dependencies off embedded edge nodes.

Location:

```text
scripts/geospatial_ingest/
```

Core modules:

| File | Purpose |
|---|---|
| `terrain.py` | Computes slope, aspect, and flow accumulation from a projected DEM |
| `soils.py` | Rasterizes SSURGO-style soil polygons into hydrologic group grids |
| `intelligence.py` | Produces heuristic runoff risk from slope, soil group, and flow accumulation |
| `manifest.py` | Writes a structured geospatial manifest documenting derived layers and assumptions |
| `pipeline.py` | Orchestrates the full provisioning workflow |

The runoff risk layer is a heuristic susceptibility index, not a certified hydrologic model.

---

## FarmGraph Core

Location:

```text
software/farm_twin/
```

The FarmGraph stores:

```text
Farm
Field
ManagementZone
Paddock
SensorNode
Measurement
Observation
GeospatialLayer
Card
```

Core graph edges include:

```text
CONTAINS
DEPLOYED_IN
MEASURES
PRODUCES
INFORMS
HAS_LAYER
```

The storage backend is intentionally simple:

```text
SQLite nodes table
SQLite edges table
SQLite observations table
SQLite cards table
```

No external graph database is required.

---

## Testing

Recommended test commands from the repository root:

```bash
# Farm Twin tests
PYTHONPATH=./software/farm_twin pytest software/farm_twin/tests -v

# Geospatial ingest tests
pytest scripts/geospatial_ingest/tests -v

# End-to-end WP2 to WP3 chain
PYTHONPATH=./software/farm_twin pytest tests/e2e -v

# Dashboard/API tests
cd software/dashboard
PYTHONPATH=../farm_twin pytest -v
```

On PowerShell, use:

```powershell
$env:PYTHONPATH="./software/farm_twin"
pytest software/farm_twin/tests -v
```

---

## Repository Structure

```text
sais/
├── docs/
│   ├── SAIS_UI_ARCHITECTURE.md
│   ├── WP6_SENSOR_SIM_ADMIN_SETUP_PLAN.md
│   ├── ONTOLOGY_REGEN_AG.md
│   ├── FARMER_ACTIVITY_OVERLAY.md
│   ├── SENSOR_DEPLOYMENT_MAP.md
│   ├── ARCHITECTURE.md
│   ├── HARDWARE_SPEC.md
│   └── ...
├── scripts/
│   └── geospatial_ingest/
│       ├── terrain.py
│       ├── soils.py
│       ├── intelligence.py
│       ├── manifest.py
│       ├── pipeline.py
│       └── tests/
├── software/
│   ├── farm_twin/
│   │   ├── farm_twin/
│   │   │   ├── graph.py
│   │   │   ├── storage.py
│   │   │   ├── ingest_geospatial.py
│   │   │   ├── ingest_observation.py
│   │   │   ├── queries.py
│   │   │   └── cards.py
│   │   └── tests/
│   └── dashboard/
│       ├── main.py
│       ├── seed_db.py
│       ├── schemas.py
│       ├── templates/
│       │   ├── index.html
│       │   ├── map.html
│       │   ├── network.html
│       │   └── admin.html
│       └── static/
│           ├── app.js
│           ├── map_layers.js
│           ├── admin.js
│           └── style.css
├── tests/
│   └── e2e/
├── firmware/
├── hardware/
├── task.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

---

## Design Principles

### Offline first

The farm must remain operational without internet access. Cloud services may be optional enrichments, never core dependencies.

### Low cost first

Prefer, in order:

```text
open public data
manual farmer observation
low-cost sensors
existing farm equipment
optional advanced modules
```

### Measurement to meaning

SAIS does not begin with sensors. It begins with farmer questions:

```text
Farm question
→ meaningful measurement
→ cheapest source
→ confidence level
→ recommended inspection or action
```

### Evidence before recommendation

Every decision card should show its evidence chain.

### Same path for demo and live

Simulation, Admin setup, and real field hardware should all use the same APIs and graph state.

No demo-only data formats.

---

## Near-Term Roadmap

### WP8.5: Admin Reliability and Offline UI Hardening

Planned next hardening pass:

```text
add Paddock UI form
add sensor latitude/longitude entry
validate parent IDs
validate path ID versus payload ID
add Admin API tests
move Leaflet assets local for offline use
add backend GeoJSON validation
```

### WP9: Source Registry and Weather Observations

Planned all-source expansion:

```text
source_registry.yaml
layer_registry.yaml
weather observations as sais.observation.v1
manual rainfall entry
optional open weather source
WeatherContextCard
SensorHealthCard
FarmSetupCompletenessCard
```

### WP10: Sensor Simulator and Live Hardware Bridge

Planned live-transfer bridge:

```text
sensor simulator CLI
normal, drydown, recovery, invalid, burst profiles
weather station simulator
ESP32/UNO Q firmware client path
future signed telemetry
```

---

## Hardware Direction

SAIS is intended to support a tiered hardware path:

| Tier | Purpose |
|---|---|
| Laptop/setup machine | Geospatial provisioning and dashboard development |
| ESP32/STM32-class controller | Low-cost real-time sensor and actuator node |
| Arduino UNO Q / Linux edge node | Integrated edge compute and controller target |
| Raspberry Pi / CM4 / similar | Practical local dashboard and gateway target |
| Jetson / GPU node | Optional advanced acceleration and research modules |

Current repository work is focused on the software, geospatial, dashboard, and data model layers. Real hardware firmware integration is the next major implementation track.

---

## Security Posture

SAIS is not yet a certified safety system.

Current security posture:

```text
local-first execution
validated API payloads
SQLite persistence
no required cloud dependency
no arbitrary external URL fetch endpoint
clear separation between planned research modules and active implementation
```

Future security work:

```text
signed node telemetry
node identity registry
anti-replay counters
cryptographic audit records
role-based local admin access
field-safe actuator authorization
```

---

## Contributing

SAIS is an open project. Contributions are welcome across firmware, hardware design, geospatial processing, dashboard UI, FarmGraph modeling, sensor integrations, documentation, and protocol specification.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a pull request.

---

## License

SAIS is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means derivative work, including network-deployed services, must also be released under the same license. This is deliberate: SAIS is intended to remain farmer-owned, inspectable, and resistant to proprietary enclosure.

See [`LICENSE`](LICENSE) for the full text.

---

Copyright © 2026 Nathanael J. Bocker. Licensed under AGPL-3.0.
