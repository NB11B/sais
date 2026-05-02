# WP6: Live-Transferable Sensor Simulation, Admin Setup, and Farm Configuration

## Purpose

WP6 must not be a throwaway demo layer. The simulator, admin page, farm boundary editor, growing-zone editor, and weather ingestion path must use the same API contracts and database paths that will be used by real hardware and real farm setup workflows.

The goal is to bridge from the current seeded dashboard to live field operation without a future rewrite.

Current foundation:

- WP2 produces geospatial provisioning layers and a manifest.
- WP3 stores the Farm Digital Twin as SQLite-backed graph nodes, edges, observations, and cards.
- WP4 exposes the operator dashboard, GIS Twin, and Knowledge Graph.
- WP5 accepts live `sais.observation.v1` telemetry through `POST /api/observations`.
- WP5.5 validates ingestion, avoids temporary files, supports duplicate/idempotent behavior, and regenerates decision cards.

WP6 adds:

1. A sensor-node simulator that behaves like future ESP32/UNO Q firmware.
2. An Admin Setup page for defining farm geometry, fields, management zones, paddocks, and node placement.
3. Weather ingestion as first-class observations.
4. A single shared API path for simulated and real devices.

---

## Design Rule

Every WP6 feature must be live-transferable.

Do not create demo-only payloads, demo-only database tables, or simulator-only endpoints.

Use this flow for both simulation and hardware:

```text
field source
  -> sais.observation.v1 or sais.admin_profile_update.v1
  -> FastAPI endpoint
  -> FarmGraph / SQLite
  -> cards / GIS / network views
```

---

## Work Package 6A: Sensor Node Simulator

### Objective

Create a CLI tool that posts realistic telemetry to the existing `POST /api/observations` endpoint.

The simulator is a stand-in for real ESP32/UNO Q firmware, so its payloads must match the live API exactly.

### Proposed structure

```text
tools/sensor_sim/
├── README.md
├── sensor_sim.py
├── profiles/
│   ├── soil_node_normal.json
│   ├── soil_node_drydown.json
│   ├── soil_node_recovery.json
│   ├── soil_node_invalid.json
│   ├── weather_station_basic.json
│   └── multi_sensor_zone.json
└── tests/
    ├── test_sensor_sim_payloads.py
    └── test_sensor_sim_posting.py
```

### CLI examples

```bash
python tools/sensor_sim/sensor_sim.py --url http://localhost:8000 --profile tools/sensor_sim/profiles/soil_node_drydown.json --interval 5
```

```bash
python tools/sensor_sim/sensor_sim.py --url http://localhost:8000 --profile tools/sensor_sim/profiles/weather_station_basic.json --interval 60
```

### Required modes

| Mode | Purpose |
|---|---|
| `normal` | Moisture stable around healthy range. |
| `drydown` | Moisture gradually falls below the decision threshold. |
| `recovery` | Moisture rises after simulated rainfall. |
| `invalid` | Sends malformed payloads to test API rejection. |
| `burst` | Sends rapid duplicate/concurrent readings. |
| `multi_sensor` | Multiple node IDs publish the same metric. |
| `weather` | Publishes weather observations such as rainfall, air temperature, humidity, and wind. |

### Required payload contract

Every generated observation must be valid `sais.observation.v1` unless intentionally using invalid mode.

Example soil payload:

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

Example weather payload:

```json
{
  "schema": "sais.observation.v1",
  "node_id": "weather-station-001",
  "farm_id": "local",
  "field_id": null,
  "zone_id": null,
  "timestamp": "2026-05-02T12:00:00Z",
  "measurement_id": "weather.rainfall.hourly",
  "layer": "Atmosphere",
  "value": 0.18,
  "unit": "in/hr",
  "measurement_basis": "direct",
  "confidence": "medium",
  "source": {
    "type": "weather_station",
    "sensor_model": "simulated-rain-gauge"
  }
}
```

### Acceptance tests

- Simulator posts valid soil observations to `/api/observations`.
- Simulator can trigger WaterRetentionCard status change from `ok` to `watch`.
- Simulator can publish weather observations without breaking card generation.
- Invalid mode returns `422` responses for malformed payloads.
- Burst mode does not create duplicate rows when timestamps and node IDs are identical.

---

## Work Package 6B: Admin Setup Page

### Objective

Add an admin page for configuring the actual farm shape, fields, growing zones, paddocks, and node placement.

This is not just a UI convenience. It becomes the setup path for real deployments.

### Proposed route

```text
GET /admin
```

### Proposed files

```text
software/dashboard/templates/admin.html
software/dashboard/static/admin.js
```

### Admin page capabilities

1. Farm metadata
   - farm ID
   - farm name
   - operator notes

2. Boundary editing
   - add GPS marker points
   - close polygon
   - save as `boundary_geojson`
   - import GeoJSON file
   - export current farm profile JSON

3. Field editing
   - create field polygons
   - name fields
   - assign field IDs

4. Growing zone editing
   - create management zones inside fields
   - label soil type, crop, cover, or management intent

5. Paddock editing
   - create paddock polygons
   - assign rest-period target
   - optional grazing notes

6. Sensor placement
   - place node marker on map
   - assign node ID
   - assign field/zone
   - assign sensor package type

7. Weather setup
   - choose manual weather station, local simulated weather, or optional online weather source
   - store station location
   - map weather observations to the farm-level Atmosphere layer

### Important offline-first note

The current GIS page uses Leaflet from a public CDN. That is acceptable for development, but not for sovereign/offline field use.

WP6 should add a local/static fallback:

```text
software/dashboard/static/vendor/leaflet/
├── leaflet.css
├── leaflet.js
└── images/
```

The dashboard should not depend on the internet to render farm geometry.

---

## Work Package 6C: Farm Profile API

### Objective

Expose API endpoints that let the Admin page read and update farm profile graph nodes.

### Proposed endpoints

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

### Payloads

Use graph-backed payloads that mirror existing model dataclasses.

Example field update:

```json
{
  "id": "field-a",
  "farm_id": "local",
  "name": "Field A",
  "boundary_geojson": {
    "type": "Feature",
    "properties": {},
    "geometry": {
      "type": "Polygon",
      "coordinates": []
    }
  }
}
```

### Persistence rule

Admin updates must write to the same `nodes` and `edges` tables used by the FarmGraph.

Do not create a second farm-profile store.

---

## Work Package 6D: Weather Monitoring

### Objective

Treat weather as first-class observations rather than a special dashboard-only integration.

### Minimum weather measurements

| Measurement ID | Layer | Unit | Basis |
|---|---|---|---|
| `weather.air_temperature` | Atmosphere | `C` or `F` | direct/open_data |
| `weather.relative_humidity` | Atmosphere | `%` | direct/open_data |
| `weather.rainfall.hourly` | Atmosphere / WaterCycle | `in/hr` or `mm/hr` | direct/open_data |
| `weather.wind_speed` | Atmosphere | `mph` or `m/s` | direct/open_data |
| `weather.vpd` | Atmosphere / PlantHealth | `kPa` | derived |

### Weather source priority

1. Local low-cost weather station or rain gauge.
2. Manual rainfall entry.
3. Optional open weather API when internet is available.
4. Simulated weather for demo/testing.

### Dashboard effect

Weather observations should appear in:

- Latest Observations
- GIS context panel
- WaterRetentionCard evidence chains
- later PlantStressCard and GrazingReadinessCard

---

## Work Package 6E: Card Logic Extension

WP6 should not build a large AI layer. It should extend deterministic card logic enough to make the admin/weather setup meaningful.

### Add or prepare for these cards

```text
WaterRetentionCard       existing
WeatherContextCard       new
SensorHealthCard         new
FarmSetupCompletenessCard new
```

### FarmSetupCompletenessCard

This card should warn when the digital twin is missing required setup pieces.

Examples:

- Farm boundary missing.
- Field boundary missing.
- No management zones defined.
- No sensor nodes assigned to zones.
- No weather source configured.

This is important because incomplete setup can make later recommendations misleading.

---

## Acceptance Criteria

WP6 is complete when:

1. The simulator posts valid `sais.observation.v1` payloads to the existing live endpoint.
2. The same endpoint can be used by future ESP32/UNO Q firmware without API changes.
3. The Admin page can define or update farm, field, zone, and paddock boundaries.
4. Updated boundaries render on `/map` without reseeding the database manually.
5. The Knowledge Graph reflects admin-created nodes and edges.
6. Weather observations can be posted and displayed.
7. All admin writes persist to SQLite.
8. The dashboard can run without internet dependency for core farm geometry rendering.
9. Tests cover admin profile updates, simulator payloads, and weather observations.

---

## Suggested Build Order

1. Add simulator CLI using existing `/api/observations`.
2. Add weather simulator profile.
3. Add `/admin` page shell.
4. Add farm profile read API.
5. Add farm/field/zone/paddock write APIs.
6. Add boundary drawing/import/export.
7. Add sensor node placement.
8. Add weather observation handling and display.
9. Add local Leaflet assets or documented offline fallback.
10. Add tests for the full admin-to-dashboard loop.

---

## Non-Goals for WP6

- No LLM or RAG agent.
- No complex auth system yet.
- No cloud weather dependency as a requirement.
- No drone or vision pipeline.
- No advanced hydrologic model.
- No graph database migration.

WP6 should make SAIS configurable and live-transferable, not more complicated.
