# SAIS Livestock RFID and Animal Provisioning Architecture

## Purpose

SAIS needs a livestock identity layer that works the same way as hardware node provisioning.

When an animal is tagged, the operator should be able to provision that animal into the ranch digital twin from the dashboard, attach identity evidence, associate RFID/tag identifiers, and optionally add face/body photos for future AI recognition.

The goal is:

```text
tag animal
→ detect tag
→ animal appears as pending identity
→ operator accepts/provisions animal
→ assign herd/paddock/attributes
→ attach face/body photos
→ track observations and movement
→ fuse into PFKR-5 livestock intelligence
→ support future drone ISR recognition
```

---

## Design Principle

Treat an animal identity like a field asset with a provisioning lifecycle.

A hardware node is provisioned as:

```text
node discovered
→ pending
→ accepted
→ assigned
→ active
```

A livestock identity should be provisioned as:

```text
tag detected
→ pending animal
→ accepted animal
→ assigned herd/paddock
→ active tracked identity
```

This keeps animal identity management consistent with SAIS node provisioning.

---

## RFID Technology Options

### 1. LF Animal RFID: 134.2 kHz ISO 11784/11785

This is the conventional livestock identification standard used in many animal ID systems.

Strengths:

```text
widely used for livestock identity
works with official animal ID programs
low interference
good individual ID confirmation
mature ear tag / bolus ecosystem
```

Limitations:

```text
short read range
not suitable for drone standoff detection
usually requires chute, wand, alley, or close gate reader
```

Best SAIS use:

```text
confirmed animal identity at chute/gate/water point
manual or semi-automated welfare check
official ID linkage
```

### 2. Passive UHF RFID / RAIN RFID: 860-960 MHz, EPC Gen2 / ISO 18000-63

This is the most plausible passive long-range RFID option.

Strengths:

```text
meter-scale reads possible with proper reader, antenna, and tag orientation
passive tags require no battery
can support ground stations at gates, water points, mineral stations, trailers, alleys
possible future drone-mounted reader experiments
lower per-tag maintenance than active systems
```

Limitations:

```text
range depends strongly on tag design, antenna, power, orientation, animal body shadowing, and motion
regional frequency/power rules vary
read collisions must be handled for groups
less official livestock-standard than LF in some contexts
weather, mud, ear placement, and body absorption can affect reliability
```

Best SAIS use:

```text
ranch-local detection at water points, gates, mineral stations, handling alleys, drone flyover experiments
```

### 3. Active RFID / BLE / LoRa / UWB Tags

These are battery-powered identity/location tags rather than simple passive RFID.

Strengths:

```text
longer range
better drone/ground detection potential
can include motion, temperature, GPS, or health telemetry
can report periodically without passing a reader gate
```

Limitations:

```text
higher cost
battery maintenance
larger tag package
more complex provisioning and security
possible overkill for first SAIS livestock identity layer
```

Best SAIS use:

```text
high-value animals
research herds
drone ISR experiments
real-time animal movement studies
```

---

## Recommended SAIS Path

Use a two-layer identity approach.

### Baseline Identity Layer

```text
LF 134.2 kHz official ID if needed
or passive UHF RFID ear tag for longer local detection
```

### Local Tracking Layer

```text
UHF RFID readers at water/gates/mineral stations
plus future drone-mounted UHF or active tag receiver
```

### Future ISR Layer

```text
drone camera
+ RFID cue
+ face/body photo reference
+ AI recognition model
```

This creates a practical path:

```text
identity now
movement evidence next
AI/drone recognition later
```

---

## Ground Station Detection Model

Ground stations should be deployed at high-value chokepoints:

```text
water tanks / troughs
mineral stations
gates
handling alleys
weigh points
shade/shelter areas
paddock entry/exit points
```

Each ground station should act like a SAIS node:

```text
rfid-reader-node
→ reports tag detections
→ has node health/status
→ is provisioned to a physical location
→ contributes to livestock distribution intelligence
```

Example detection event:

```json
{
  "schema": "sais.livestock_detection.v1",
  "reader_node_id": "sais-rfid-gate-01",
  "animal_tag_id": "EPC-300833B2DDD9014000000001",
  "tag_type": "uhf_epc_gen2",
  "farm_id": "local",
  "field_id": "field-a",
  "paddock_id": "paddock-1",
  "asset_id": "water-tank-north",
  "timestamp": "2026-05-02T12:00:00Z",
  "rssi": -54,
  "read_count": 7,
  "confidence": "medium",
  "source": {
    "type": "rfid_reader",
    "antenna": "north-facing-panel",
    "reader_model": "local-uhf-reader"
  }
}
```

---

## Drone Detection Model

Drone detection should be considered a future ISR collection layer, not the first dependency.

Potential drone modes:

```text
1. Drone camera only, later AI recognition.
2. Drone-mounted UHF RFID reader for opportunistic tag scans.
3. Drone-mounted active/BLE/LoRa receiver for battery-powered tags.
4. Drone acts as temporary mobile collection gateway.
```

Important cautions:

```text
passive UHF RFID from drones is possible in principle but highly sensitive to antenna geometry, altitude, speed, reader power, tag orientation, and local radio regulations
LF livestock RFID is not suitable for practical drone standoff detection
active tags are easier for drone detection but require batteries and higher-cost tags
```

SAIS should design for drone ISR by keeping livestock identity separate from collection method.

The animal record should not care whether detection came from:

```text
ground reader
drone reader
camera AI
manual observation
GPS collar
```

All are collection sources attached to the same animal identity.

---

## Animal Provisioning Lifecycle

```text
UNSEEN
  ↓
DETECTED
  ↓
PENDING_ACCEPTANCE
  ↓
ACCEPTED
  ↓
ASSIGNED
  ↓
ACTIVE
  ↓
MISSING / SOLD / DECEASED / RETIRED
```

### DETECTED

A tag is seen by an RFID reader, but SAIS does not yet know which animal it belongs to.

### PENDING_ACCEPTANCE

The tag appears in the Admin livestock queue.

### ACCEPTED

The operator confirms this tag belongs to the ranch inventory.

### ASSIGNED

The operator attaches animal metadata, herd, photos, and management context.

### ACTIVE

The animal identity is now allowed to contribute to livestock distribution and welfare intelligence.

### MISSING

The animal has not been detected within the expected window or is absent from expected herd movement.

---

## Animal Record Schema

Recommended table/model:

```text
AnimalIdentity
```

Payload:

```json
{
  "animal_id": "animal-0001",
  "farm_id": "local",
  "status": "active",
  "tag_ids": [
    {
      "tag_id": "EPC-300833B2DDD9014000000001",
      "tag_type": "uhf_epc_gen2",
      "placement": "left_ear",
      "active": true
    },
    {
      "tag_id": "840003123456789",
      "tag_type": "lf_iso_11784_11785",
      "placement": "right_ear",
      "active": true
    }
  ],
  "species": "cattle",
  "sex": "cow",
  "breed": "angus_cross",
  "birth_date": "2024-03-12",
  "herd_id": "cow-calf-1",
  "current_paddock_id": "paddock-1",
  "visual_markings": "white blaze, left hip patch",
  "photo_face_id": "photo-animal-0001-face",
  "photo_body_id": "photo-animal-0001-body-left",
  "notes": "Calm temperament. Watch right rear hoof."
}
```

---

## Animal Photo Records

Photo records should be first-class evidence objects, not just loose files.

```json
{
  "photo_id": "photo-animal-0001-face",
  "animal_id": "animal-0001",
  "farm_id": "local",
  "photo_type": "face",
  "view_angle": "front",
  "timestamp": "2026-05-02T12:00:00Z",
  "file_path": "media/animals/animal-0001/face-front-2026-05-02.jpg",
  "source": "admin_upload",
  "quality": "good",
  "notes": "Face photo for future recognition model."
}
```

Minimum required photos during provisioning:

```text
face/front
body/left or body/right
```

Recommended optional photos:

```text
face/left
face/right
body/left
body/right
rear/markings
brand/ear tag closeup
```

---

## Admin UX

Add an Admin section:

```text
Admin → Livestock
```

### Pending Tags Queue

Shows tags detected but not assigned:

```text
tag_id
tag_type
reader_node_id
first_seen
last_seen
read_count
rssi
probable_location
actions: accept / reject / merge with animal
```

### Animal Provisioning Wizard

Steps:

```text
1. Confirm tag.
2. Create or select animal record.
3. Add animal metadata.
4. Assign herd.
5. Upload face photo.
6. Upload body photo.
7. Confirm current paddock or last known location.
8. Save animal identity.
```

### Required Fields

```text
animal_id or auto-generate
farm_id
species
tag_id
tag_type
herd_id
status
face photo
body photo
```

### Optional Fields

```text
breed
sex
birth date
color
visual markings
brand
health notes
BCS baseline
management notes
```

---

## API Endpoints

Suggested endpoints:

```text
POST /api/livestock/tags/detect
GET  /api/livestock/tags/pending
POST /api/livestock/tags/{tag_id}/accept
POST /api/livestock/tags/{tag_id}/reject
POST /api/livestock/animals
GET  /api/livestock/animals
GET  /api/livestock/animals/{animal_id}
PUT  /api/livestock/animals/{animal_id}
POST /api/livestock/animals/{animal_id}/photos
GET  /api/livestock/animals/{animal_id}/photos
POST /api/livestock/detections
GET  /api/livestock/detections/recent
```

---

## Detection Trust Rules

Unprovisioned tag:

```text
store detection
show pending tag
low confidence
no operational livestock card impact
```

Accepted animal:

```text
store detection
update last_seen
update last_known_location
contribute to PFKR-5 distribution and water visit logic
```

Rejected tag:

```text
store only as ignored/quarantined if desired
no operational impact
```

Duplicate tag:

```text
flag conflict
do not auto-merge
require operator review
```

---

## PFKR Mapping

RFID and animal identity primarily inform:

```text
PFKR-5: Livestock Health, Distribution, and Pressure
PFKR-1: Water Status and Movement
PFKR-2: Grazing Readiness and Recovery
PFKR-6: Infrastructure and Access
PFKR-8: Source Health and Confidence
```

Examples:

```text
Animal not seen at water point during heat → WaterAccessCard / HeatStressCard
Herd enters paddock early → GrazingPressureCard
Animal repeatedly alone or missing → LivestockDistributionCard
Reader stale or offline → SourceHealthCard
Gate reader detects unexpected movement → InfrastructureAlertCard
```

---

## Ground Reader Hardware Candidates

SAIS should evaluate reader classes, not lock to one vendor early.

### Fixed UHF Reader Station

```text
UHF RFID reader module
high-gain directional antenna
ESP32/CM4/UNO Q gateway
solar/battery option
weatherproof enclosure
local UDP/HTTP telemetry to SAIS
```

Best for:

```text
gates
water points
mineral stations
alleyways
```

### Portable Wand / Close Reader

```text
LF official ID reader
or handheld UHF reader
mobile admin workflow
```

Best for:

```text
chute work
manual animal provisioning
confirmed tag-to-animal assignment
```

### Drone Reader Payload

```text
lightweight UHF reader or active-tag receiver
directional antenna
payload power budget
telemetry bridge back to SAIS
```

Best for future:

```text
pasture sweep
missing animal search
herd distribution checks
RFID-cued visual recognition
```

---

## Recommended First Prototype

Do not start with drone RFID.

Start with a fixed ground reader at a controlled chokepoint.

Prototype path:

```text
1. Passive UHF ear tag.
2. Fixed UHF reader + directional antenna at gate or water point.
3. Reader gateway posts tag detections to SAIS.
4. Admin pending tag queue provisions animal.
5. Operator uploads face/body photos.
6. Detection events update animal last_seen and water/grazing logic.
```

Then evaluate drone detection after ground identity is stable.

---

## Repo Work Package Proposal

### WP21: Livestock RFID Identity and Animal Provisioning

Deliverables:

```text
AnimalIdentity model
AnimalPhoto model
RFIDTag model
LivestockDetection model
pending tag registry
/api/livestock/tags/detect
/api/livestock/tags/pending
animal provisioning UI
face/body photo upload path
detection trust rules
PFKR-5 livestock distribution card hooks
```

### WP22: Ground RFID Reader Node

Deliverables:

```text
reader-node firmware/gateway
UHF reader integration
tag detection packet format
bench test with sample tags
water/gate reader station profile
source health monitoring
```

### WP23: Drone ISR Preparation

Deliverables:

```text
drone detection event schema
photo dataset structure
animal re-identification metadata
RFID-cued camera workflow
future drone reader payload interface
```

---

## Bottom Line

Use RFID as the identity anchor, not the whole tracking system.

The SAIS livestock tracking stack should be:

```text
RFID tag
→ provisioned AnimalIdentity
→ face/body photo evidence
→ ground station detections
→ PFKR-5 livestock intelligence
→ future drone ISR and AI recognition
```

Start with UHF RFID for local long-range ranch detection, keep LF RFID compatibility for official close-range identity, and leave room for active tags or drone-based receivers where the operational need justifies the cost.
