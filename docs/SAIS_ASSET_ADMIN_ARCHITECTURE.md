# SAIS Asset Admin Architecture

## Purpose

SAIS should separate one-time farm setup from ongoing asset management.

The current Admin page is doing too much:

```text
farm identity
boundaries
fields
zones
paddocks
sensor nodes
water infrastructure
fences/gates
livestock
grazing events
```

That is acceptable during early prototyping, but it will not scale for field use.

The cleaner model is:

```text
Admin Setup
  -> farm structure and configuration

Assets
  -> living and physical assets that change over time

Nodes
  -> provisioned sensing/telemetry devices
```

Livestock should be handled as an asset class under a dedicated Asset Admin surface, not buried inside the farm-boundary setup wizard.

---

## UI Split

Recommended primary navigation:

```text
Operator Feed | GIS Twin | Knowledge Graph | Admin Setup | Assets | Nodes
```

Minimum near-term navigation:

```text
Operator Feed | GIS Twin | Knowledge Graph | Admin Setup | Assets
```

If the UI needs to remain compact, Nodes can start as a subsection under Assets:

```text
Assets
  - Livestock
  - Water
  - Infrastructure
  - Equipment
  - Sensor Nodes
```

---

## Admin Setup Page

The Admin Setup page should be for relatively stable farm configuration.

It should include:

```text
farm identity
farm boundary
fields
management zones
paddocks
unit preferences
timezone
basic source/layer defaults
```

It should not be the main place for day-to-day livestock, water, gate, equipment, or sensor operations.

Admin Setup answers:

```text
What is the farm/ranch structure?
Where are the operating areas?
How is the land divided?
```

---

## Assets Page

The Assets page should manage physical, biological, and operational assets.

Asset categories:

```text
Livestock
Water Assets
Infrastructure Assets
Equipment
Sensor Nodes
Photo/Media Evidence
```

Assets answer:

```text
What do we operate, monitor, move, maintain, identify, or protect?
```

---

## Asset Classes

### 1. Livestock Assets

Livestock are living assets and should have their own provisioning lifecycle.

Examples:

```text
individual cow
bull
calf
sheep
goat
horse
herd group
```

Core records:

```text
AnimalIdentity
RFIDTag
AnimalPhoto
LivestockDetection
LivestockObservation
Herd
```

Livestock page functions:

```text
pending RFID tags
animal provisioning
face/body photo upload
herd assignment
current paddock/location
BCS/manure/health notes
last seen
water-point detections
missing animal warnings
```

### 2. Water Assets

Examples:

```text
tank
trough
pond
well
pump
valve
water line
float switch
flow meter
```

Water page functions:

```text
asset registration
location assignment
current level/status
manual water check
sensor assignment
maintenance notes
low water alerts
pump/valve state
```

### 3. Infrastructure Assets

Examples:

```text
fence
gate
road
bridge
crossing
corral
barn
solar array
battery enclosure
```

Infrastructure page functions:

```text
asset registration
GeoJSON Point or LineString
status updates
inspection history
gate open/closed
fence hot/broken
affected paddocks
```

### 4. Equipment Assets

Examples:

```text
tractor
ATV
feed trailer
water trailer
generator
sprayer
portable fencing kit
mineral feeder
```

Equipment page functions:

```text
location
status
maintenance notes
fuel/battery
assignment to task
inspection history
```

### 5. Sensor Nodes

Sensor nodes are assets too, but they are also data sources.

Examples:

```text
soil probe
weather station
tank level sensor
gate sensor
RFID reader node
camera trap
drone gateway
```

Node page functions:

```text
pending nodes
accepted nodes
rejected nodes
role templates
multi-function capability selection
assignment to zone/paddock/asset
source health
battery/RSSI/last seen
```

---

## Livestock as Assets

Livestock should be treated as assets, but not the same kind of asset as a pump or gate.

They are:

```text
biological assets
mobile assets
identity-bearing assets
welfare-sensitive assets
production assets
```

They should support both individual and group-level management.

### Individual Animal

```json
{
  "asset_type": "livestock.animal",
  "animal_id": "animal-0001",
  "farm_id": "local",
  "status": "active",
  "species": "cattle",
  "herd_id": "cow-calf-1",
  "current_paddock_id": "paddock-1",
  "tag_ids": [],
  "photo_ids": [],
  "notes": "Watch right rear hoof."
}
```

### Herd Group

```json
{
  "asset_type": "livestock.herd",
  "herd_id": "cow-calf-1",
  "farm_id": "local",
  "species": "cattle",
  "animal_count": 84,
  "current_paddock_id": "paddock-1",
  "management_class": "cow_calf",
  "notes": "Main cow-calf herd."
}
```

Both individual animals and herds should be first-class assets.

---

## Proposed Asset Lifecycle

```text
registered
pending
active
maintenance
missing
inactive
retired
sold
deceased
rejected
```

Not all statuses apply to all asset classes.

Examples:

```text
animal -> active / missing / sold / deceased
pump -> active / maintenance / retired
gate -> active / maintenance / broken
sensor node -> pending / active / stale / rejected / retired
```

---

## Recommended Routes

### Page routes

```text
/assets
/assets/livestock
/assets/water
/assets/infrastructure
/assets/equipment
/assets/nodes
```

### API routes

```text
GET  /api/assets
POST /api/assets
GET  /api/assets/{asset_id}
PUT  /api/assets/{asset_id}
POST /api/assets/{asset_id}/status
GET  /api/assets/{asset_id}/history
```

Livestock-specific:

```text
GET  /api/assets/livestock
POST /api/assets/livestock/animals
GET  /api/assets/livestock/animals/{animal_id}
PUT  /api/assets/livestock/animals/{animal_id}
POST /api/assets/livestock/animals/{animal_id}/photos
POST /api/assets/livestock/tags/detect
GET  /api/assets/livestock/tags/pending
POST /api/assets/livestock/tags/{tag_id}/accept
POST /api/assets/livestock/tags/{tag_id}/reject
```

Node-specific:

```text
GET  /api/assets/nodes
GET  /api/assets/nodes/pending
POST /api/assets/nodes/hello
POST /api/assets/nodes/{node_id}/accept
POST /api/assets/nodes/{node_id}/reject
PUT  /api/assets/nodes/{node_id}/assignment
```

The existing `/api/nodes/*` routes can remain as compatibility aliases.

---

## Asset Graph Model

All assets should be graph nodes.

Recommended node types:

```text
AnimalIdentity
Herd
RFIDTag
AnimalPhoto
WaterAsset
InfrastructureAsset
EquipmentAsset
SensorNode
RFIDReaderNode
CameraNode
DroneAsset
```

Recommended edges:

```text
BELONGS_TO
ASSIGNED_TO
LOCATED_IN
DEPLOYED_IN
ATTACHED_TO
DETECTED_BY
OBSERVED_BY
HAS_PHOTO
HAS_TAG
PART_OF_HERD
USES_WATER_ASSET
INFORMS
```

Examples:

```text
AnimalIdentity HAS_TAG RFIDTag
AnimalIdentity HAS_PHOTO AnimalPhoto
AnimalIdentity PART_OF_HERD Herd
AnimalIdentity LOCATED_IN Paddock
RFIDTag DETECTED_BY RFIDReaderNode
RFIDReaderNode DEPLOYED_IN Gate
TankLevelNode ATTACHED_TO WaterAsset
GateSensor ATTACHED_TO InfrastructureAsset
```

---

## Asset Admin UX

### Assets Landing Page

Cards:

```text
Livestock
Water
Infrastructure
Equipment
Nodes
Media
```

Each card shows:

```text
active count
pending count
alert count
stale/missing count
last update
```

### Livestock Page

Tabs:

```text
Animals
Herds
Pending Tags
Detections
Photos
Health Notes
```

### Nodes Page

Tabs:

```text
Pending
Active
Stale/Error
Rejected
Role Templates
```

### Water Page

Tabs:

```text
Tanks/Troughs
Pumps/Valves
Manual Checks
Telemetry
Maintenance
```

### Infrastructure Page

Tabs:

```text
Gates
Fences
Roads
Structures
Status History
```

---

## Why This Matters

The farm setup wizard should be painless and finite.

Asset management is ongoing.

Mixing the two creates UI clutter and increases operator error.

Correct split:

```text
Admin Setup = define the ranch structure
Assets = manage things that live, move, break, report, or need maintenance
Operator Feed = decide what to do next
GIS Twin = see where everything is
Knowledge Graph = understand why SAIS thinks what it thinks
```

---

## Recommended Work Package

### WP20: Admin Setup UX Cleanup

Focus:

```text
boundary point builder
field/zone/paddock dropdowns
remove free-text parent IDs
multifunction node provisioning schema
```

### WP21: Asset Admin Foundation

Focus:

```text
/assets route
asset registry table
generic Asset model
WaterAsset and InfrastructureAsset migration into Asset view
Node provisioning moved/linked under Assets → Nodes
```

### WP22: Livestock Asset Provisioning

Focus:

```text
AnimalIdentity
RFIDTag
AnimalPhoto
pending RFID tag queue
face/body photo upload
herd assignment
livestock asset page
```

### WP23: RFID Reader Node

Focus:

```text
RFID reader node role template
tag detection event schema
ground reader bridge
water/gate detection tests
```

---

## Bottom Line

Yes: livestock should be treated as assets, but livestock deserves a specialized asset page because it has identity, welfare, movement, production, and photo/recognition requirements.

The clean structure is:

```text
Admin Setup
  farm shape and operating areas

Assets
  livestock, water, infrastructure, equipment, nodes

Operator Feed
  decisions and alerts

GIS Twin
  spatial operating picture
```
