# SAIS Engineering Guidance

## Measurement Intelligence and Low-Cost Farm Digital Twin

This guidance consolidates the current SAIS direction into engineering priorities for the next build stage.

The core decision: **do not begin with schemas, dashboards, or hardware packages alone. Begin with the measurement-to-meaning map.**

SAIS should answer:

```text
What can we measure cheaply?
What does it tell the farmer?
What decision does it support?
What intervention might follow?
What evidence supports the recommendation?
```

The current SAIS ontology already defines the farm as a causal system: soil biology, soil chemistry, soil physics, plant health, water cycle, atmosphere, livestock, ecosystem, and market/financial layers. It also defines the closed-loop intelligence cycle of observe, contextualize, diagnose, and act. 

The Farmer Activity Overlay correctly frames the system around the farmer’s real workflow: **Observation → Decision → Intervention**. Sensor data must augment that loop rather than replace it. 

The Sensor Deployment Map already maps ontology layers to target metrics, sensor types, deployment locations, data frequency, and hardware packages. 

---

# 1. Engineering objective

Build SAIS as a **low-cost farm intelligence layer** that combines:

```text
direct sensors
+ manual farmer observations
+ open geospatial data
+ weather/rainfall context
+ derived hydrology/terrain/soil intelligence
+ signed event history
= practical farm digital twin
```

The digital twin should not be a decorative map. It should be the central reasoning surface of the system.

The dashboard should answer:

```text
What changed?
Where did it change?
Why might it have changed?
What should the farmer inspect?
What action might be appropriate?
How confident is the system?
What evidence supports the recommendation?
```

---

# 2. Required measurement categories

Every measurement in SAIS should belong to one of five categories.

| Category                 | Meaning                                                    | Example                                                       |
| ------------------------ | ---------------------------------------------------------- | ------------------------------------------------------------- |
| **Direct sensor**        | Physical measurement from hardware                         | soil moisture, tank level, temperature                        |
| **Proxy measurement**    | Indirect signal that informs a biological/ecological state | CO₂ as microbial respiration proxy, audio as rumination proxy |
| **Manual observation**   | Farmer-entered measurement or field note                   | Brix, earthworm count, manure score                           |
| **Open data**            | Public geospatial, weather, soil, or satellite data        | DEM, SSURGO soils, rainfall, NDVI                             |
| **Derived intelligence** | Computed from multiple sources                             | runoff risk, infiltration score, grazing readiness            |

Every record should eventually carry:

```yaml
measurement_basis: direct | proxy | manual | open_data | derived
confidence: low | medium | high
cost_profile: free | low | medium | high
farmer_question: "What decision does this support?"
```

---

# 3. Measurement-to-meaning inventory

## Soil biology

| Measurement            | Source                          | Farmer meaning                                      | Dashboard use            |
| ---------------------- | ------------------------------- | --------------------------------------------------- | ------------------------ |
| Soil CO₂ / respiration | NDIR CO₂ chamber                | Is microbial activity increasing or decreasing?     | Biological engine status |
| Soil temperature       | DS18B20 / thermistor            | Is soil warm enough for biological activity?        | Biology context          |
| Soil moisture          | capacitive probe / gypsum block | Is biology limited by dry or saturated conditions?  | Respiration context      |
| Earthworm count        | manual shovel test              | Is the soil food web active?                        | Biological health score  |
| Residue breakdown      | manual/photo observation        | Is decomposition active?                            | Carbon cycling trend     |
| Soil smell/color       | manual note                     | Anaerobic, compacted, or biologically active signal | Qualitative field note   |

Engineering note: CO₂ flux should be treated as a **biological proxy**, not a full carbon accounting tool.

---

## Soil chemistry

| Measurement       | Source                     | Farmer meaning                      | Dashboard use          |
| ----------------- | -------------------------- | ----------------------------------- | ---------------------- |
| pH                | cheap probe / strips / lab | Are nutrients chemically available? | pH constraint warning  |
| EC                | low-cost EC probe          | Salinity/fertility pulse            | Salt/fertility trend   |
| NPK trend         | ISE or low-cost NPK probe  | Nutrient trend, not lab-grade truth | Trend only             |
| SOC               | lab/manual imported        | Long-term carbon baseline           | MRV baseline           |
| CEC               | soil report / SSURGO / lab | Nutrient holding capacity           | Soil buffering layer   |
| Brix              | manual refractometer       | Plant sugar / photosynthesis proxy  | Plant energy score     |
| Input application | manual log                 | Fertility/intervention history      | Explains later changes |

Engineering note: low-cost NPK probes must be labeled as **trend sensors**. Do not present them as precision lab measurements.

---

## Soil physics

| Measurement              | Source                              | Farmer meaning                       | Dashboard use            |
| ------------------------ | ----------------------------------- | ------------------------------------ | ------------------------ |
| Volumetric water content | soil moisture probe                 | Is water available in the root zone? | Moisture trend           |
| Multi-depth moisture     | 10/30/60 cm array                   | Did rainfall infiltrate downward?    | Infiltration profile     |
| Soil temperature         | thermistor / DS18B20                | Germination and biological activity  | Soil thermal layer       |
| Bulk density             | manual core sample                  | Is compaction limiting roots?        | Compaction baseline      |
| Penetrometer resistance  | manual tool                         | Where are hard layers?               | Root restriction map     |
| Aggregate stability      | slake test                          | Is structure improving?              | Soil structure score     |
| Infiltration rate        | ring test or rain/moisture response | Is water entering or running off?    | Runoff risk              |
| Surface cover            | camera/manual                       | Is soil armored?                     | Evaporation/erosion risk |

The Farmer Activity Overlay already ties soil physics to compaction, aggregation, root growth, and water infiltration decisions. 

---

## Plant health

| Measurement             | Source                           | Farmer meaning                        | Dashboard use          |
| ----------------------- | -------------------------------- | ------------------------------------- | ---------------------- |
| NDVI / vegetation index | satellite/drone/camera           | Is plant vigor rising or falling?     | Vigor map              |
| Canopy cover            | camera/manual/satellite          | Is soil protected?                    | Armor score            |
| Brix                    | manual refractometer             | Plant energy/photosynthesis           | Plant sugar trend      |
| Leaf temperature        | IR sensor / thermal if available | Water stress                          | Transpiration stress   |
| Pest/disease signs      | manual/camera                    | Crop risk                             | Inspection alert       |
| Growth stage            | manual entry                     | Timing of grazing/termination/harvest | Management window      |
| Root depth              | manual dig                       | Drought resilience                    | Root development score |

Engineering note: open satellite imagery should be used first. Drone or tractor-mounted imaging can be added later.

---

## Water cycle and hydrology

| Measurement            | Source                          | Farmer meaning                   | Dashboard use      |
| ---------------------- | ------------------------------- | -------------------------------- | ------------------ |
| Elevation              | open DEM                        | What is the terrain shape?       | Base terrain twin  |
| Slope                  | derived from DEM                | Where is erosion/runoff likely?  | Erosion risk       |
| Aspect                 | derived from DEM                | Which slopes dry faster?         | Dryness exposure   |
| Flow accumulation      | derived from DEM                | Where does water concentrate?    | Water path map     |
| Wetness index          | DEM + soils                     | Where are chronic wet/dry zones? | Wetness layer      |
| Rainfall               | open weather/radar/manual gauge | Water input                      | Rain event trigger |
| Soil moisture response | on-farm probes                  | Did rain infiltrate?             | Infiltration score |
| Pond/tank level        | ultrasonic/pressure sensor      | Water availability               | Water security     |
| Runoff clarity         | manual/photo                    | Is soil leaving the field?       | Erosion pulse      |

Engineering note: this is the most important open-data layer. Even before dense hardware deployment, terrain and hydrology can provide useful intelligence.

---

## Atmosphere and microclimate

| Measurement           | Source                    | Farmer meaning               | Dashboard use             |
| --------------------- | ------------------------- | ---------------------------- | ------------------------- |
| Air temperature       | BME280/SHT31/weather      | Heat/frost risk              | Microclimate layer        |
| Relative humidity     | BME280/SHT31/weather      | Disease and stress context   | Humidity map              |
| VPD                   | derived from temp/RH      | Plant transpiration stress   | VPD stress card           |
| Wind                  | weather station/open data | Spray drift, drying, erosion | Wind exposure             |
| Rainfall              | gauge/open data           | Water event                  | Hydrology trigger         |
| Solar radiation/light | sensor/open model         | Growth potential             | Light availability        |
| CO₂ flux              | NDIR chamber              | Soil respiration proxy       | Biology/atmosphere bridge |
| Methane proxy         | acoustic behavior         | Livestock digestion proxy    | Experimental/proxy layer  |

Engineering note: atmosphere metrics should distinguish **direct measurement**, **proxy**, and **modeled estimate**.

---

## Livestock

| Measurement            | Source                         | Farmer meaning                | Dashboard use     |
| ---------------------- | ------------------------------ | ----------------------------- | ----------------- |
| GPS location           | LoRa/GPS tags                  | Where is the herd?            | Herd heatmap      |
| Accelerometer activity | IMU tag                        | Rest/walk/graze behavior      | Behavior state    |
| Rumination proxy       | acoustic/IMU                   | Digestive behavior            | Health proxy      |
| Water visits           | tank sensor/RFID/manual        | Water dependency and movement | Water-use pattern |
| Body condition score   | manual/photo                   | Nutrition and health          | Herd trend        |
| Manure score           | manual/photo                   | Digestive/forage signal       | Diet feedback     |
| Fence movement         | manual/app event               | Grazing intervention          | Paddock history   |
| Stocking density       | animal count + area + location | Grazing pressure              | Impact per acre   |
| Rest period            | derived from grazing history   | Recovery status               | Grazing readiness |

The ontology already treats livestock as nutrient cyclers, inoculators, and grazers that affect soil biology, chemistry, and plant health. 

---

## Farm ecosystem and biodiversity

| Measurement          | Source                     | Farmer meaning           | Dashboard use           |
| -------------------- | -------------------------- | ------------------------ | ----------------------- |
| Pollinator presence  | camera/manual              | Habitat function         | Pollinator score        |
| Bird/insect activity | camera/acoustic/manual     | Predator/pest balance    | Ecosystem service proxy |
| Wildlife tracks      | manual/photo               | Habitat use              | Wildlife layer          |
| Vegetation diversity | manual/camera/satellite    | Plant diversity          | Diversity trend         |
| Edge habitat         | map/manual/open land cover | Refuge/corridor strength | Habitat connectivity    |
| Tree/shrub cover     | imagery/open data          | Shelter, shade, habitat  | Woody cover layer       |
| Pest pressure        | manual/camera              | Crop risk                | Pest alert              |
| Predator-prey proxy  | camera/manual              | Biological control       | Pest-control context    |

Engineering note: biodiversity should start with manual/photo observations and open imagery, not expensive AI hardware.

---

## Market, MRV, and audit

| Measurement           | Source                                    | Farmer meaning          | Dashboard use              |
| --------------------- | ----------------------------------------- | ----------------------- | -------------------------- |
| Practice log          | farmer/app                                | What was done and when? | Intervention ledger        |
| Sensor hash chain     | gateway signing                           | Can data be trusted?    | Audit integrity            |
| Field history         | local records                             | What changed over time? | Farm memory                |
| Input costs           | manual/accounting import                  | ROI of practice changes | Cost layer                 |
| Yield estimate        | manual/harvest record                     | Production outcome      | Output layer               |
| Carbon proxy trend    | SOC + practices + vegetation + flux proxy | Carbon story            | MRV support                |
| Water retention trend | rain + moisture + DEM                     | Resilience value        | Ecosystem service evidence |
| Biodiversity trend    | observation + imagery                     | Ecological value        | Ecosystem service evidence |

Engineering note: SAIS should not claim automatic carbon credit generation. It should provide **evidence packages** that may support MRV workflows.

---

# 4. Open-source geospatial data targets

The engineering team should evaluate these as candidate low/no-cost data sources. Endpoints and licensing should be verified during implementation.

## Terrain and hydrology

| Data type                     | Candidate source family                | Use                             |
| ----------------------------- | -------------------------------------- | ------------------------------- |
| DEM / elevation               | USGS 3DEP, state LiDAR where available | terrain base layer              |
| Slope / aspect                | derived from DEM                       | erosion, drying, solar exposure |
| Flow direction / accumulation | derived from DEM                       | water path prediction           |
| Watersheds                    | USGS/NHD/WBD-style datasets            | catchment context               |
| Streams / ponds / ditches     | NHD, OSM, manual mapping               | hydrology layer                 |
| Flood zones                   | FEMA-style flood maps                  | risk layer                      |

Derived hydrology products:

```text
DEM → slope
DEM → aspect
DEM → flow direction
DEM → flow accumulation
DEM + soils → wetness index
DEM + rainfall → runoff risk
DEM + paddocks → grazing erosion risk
```

---

## Soils

| Data type                    | Candidate source family | Use                            |
| ---------------------------- | ----------------------- | ------------------------------ |
| Soil map units               | USDA SSURGO / gSSURGO   | soil baseline                  |
| Texture                      | SSURGO / soil reports   | infiltration and water holding |
| Hydrologic soil group        | SSURGO                  | runoff/infiltration modeling   |
| Available water capacity     | SSURGO                  | drought buffer                 |
| Drainage class               | SSURGO                  | ponding/wetness risk           |
| Ecological site descriptions | NRCS-style references   | restoration targets            |

Derived soil products:

```text
soil texture + slope + rainfall → runoff risk
available water capacity + root depth → drought buffer
drainage class + DEM wetness → ponding risk
hydrologic group + cover → infiltration potential
```

---

## Vegetation and land cover

| Data type             | Candidate source family | Use                                      |
| --------------------- | ----------------------- | ---------------------------------------- |
| Sentinel-2 imagery    | public satellite        | current vigor                            |
| Landsat imagery       | public satellite        | long-term vegetation history             |
| NAIP imagery          | public aerial imagery   | farm boundary and infrastructure mapping |
| Cropland Data Layer   | USDA-style crop history | rotation history                         |
| NLCD-style land cover | public land cover       | surrounding ecosystem context            |

Derived vegetation products:

```text
NDVI trend → plant vigor
NDVI anomaly → stress zone
bare soil index → exposure risk
vegetation persistence → cover score
field history → rotation/diversity score
```

---

## Weather and climate

| Data type            | Candidate source family         | Use                    |
| -------------------- | ------------------------------- | ---------------------- |
| Rainfall             | NOAA/weather/radar/manual gauge | event trigger          |
| Forecast             | open forecast APIs              | tactical planning      |
| Temperature/humidity | weather station/open data       | stress context         |
| Drought status       | public drought products         | regional risk          |
| Historical climate   | gridded climate products        | baseline and anomalies |

Derived weather products:

```text
rainfall + soil moisture response → infiltration score
forecast rain + paddock condition → move/hold decision
VPD + soil moisture + canopy → plant stress risk
temperature + growth stage → frost/heat risk
```

---

# 5. Digital twin architecture

The digital twin should be a layered farm graph.

```text
Farm
├── Fields
│   ├── boundaries
│   ├── management zones
│   ├── soil map units
│   ├── paddocks
│   └── sensor nodes
├── Terrain
│   ├── elevation
│   ├── slope
│   ├── aspect
│   └── flow paths
├── Hydrology
│   ├── catchments
│   ├── wetness zones
│   ├── ponds/tanks
│   └── runoff risk
├── Biology
│   ├── respiration zones
│   ├── soil health observations
│   └── biodiversity observations
├── Plants
│   ├── vigor zones
│   ├── canopy cover
│   └── stress zones
├── Livestock
│   ├── herd locations
│   ├── grazing pressure
│   └── rest periods
└── Ledger
    ├── observations
    ├── decisions
    ├── interventions
    └── signed audit records
```

The dashboard should expose these as toggleable layers:

```text
Terrain
Soils
Water flow
Moisture
Plant vigor
Grazing pressure
Rest period
Biodiversity
Sensor health
Farmer observations
Interventions
Audit/MRV
```

---

# 6. Dashboard design principle

The dashboard should not primarily be a charting UI. It should be a **decision-support cockpit**.

Each alert/card should follow this structure:

```text
Observation:
What changed?

Context:
What other layers explain or contradict it?

Farmer meaning:
What does this imply operationally?

Suggested inspection:
What should the farmer verify in the field?

Possible intervention:
What action may be appropriate?

Evidence:
What data supports this?

Confidence:
Low / Medium / High
```

Example:

```text
Field A: Rainfall capture appears weak

Evidence:
- 0.7 in rain detected yesterday
- 10 cm moisture rose briefly
- 30 cm moisture did not respond
- west edge has high slope
- latest vegetation layer shows low canopy cover

Farmer meaning:
Water may not be entering or staying in the root zone.

Suggested inspection:
Check west slope for runoff, crusting, bare soil, or compaction.

Possible interventions:
Increase soil armor, delay grazing, add deep-rooting cover crop, inspect water flow path.

Confidence:
Medium
```

---

# 7. MVP measurement stack

The first engineering target should be useful with minimal cost.

## Open data first

```text
farm boundary
DEM/elevation
slope/aspect
soil map units
hydrologic soil group
available water capacity
flow accumulation
land cover
historical vegetation index
rainfall/weather
```

## Manual inputs

```text
paddock moves
rain gauge reading
Brix
earthworm count
slake test
infiltration test
manure score
body condition score
field notes/photos
input applications
```

## Low-cost sensors

```text
soil moisture at 2-3 depths
soil temperature
air temperature/RH
rain gauge
tank level
relay/valve state
optional CO2 chamber
optional sample livestock GPS tag
```

Do not overbuild the first node. A farm boundary, DEM, soil layer, rainfall, and a few cheap probes can already generate meaningful intelligence.

---

# 8. Engineering work packages

## Work Package 1: Measurement Intelligence Inventory

Create:

```text
docs/MEASUREMENT_INTELLIGENCE_INVENTORY.md
docs/measurement_inventory.yaml
```

Each measurement should define:

```yaml
id: soil.moisture.vwc
layer: SoilPhysics
measurement_basis: direct
source_type: sensor
cost_profile: low
sensor_options:
  - capacitive_probe
  - gypsum_block
  - tensiometer
informs:
  - water_availability
  - infiltration_response
  - grazing_timing
  - biological_activity_context
farmer_questions:
  - "Is there enough water in the root zone?"
  - "Did rainfall infiltrate or run off?"
  - "Should livestock be kept off this paddock?"
dashboard_cards:
  - water_retention
  - grazing_readiness
  - drought_stress
confidence: medium
```

---

## Work Package 2: Open Geospatial Intake

Build a local/offline-first ingest path for:

```text
farm boundary GeoJSON
DEM raster
soil map unit polygons
land cover raster/vector
weather/rainfall time series
satellite vegetation index raster
```

Initial outputs:

```text
slope map
aspect map
flow accumulation map
wetness index
soil capability layer
runoff risk zones
management zones
```

---

## Work Package 3: Farm Digital Twin Core

Implement the farm twin as a graph:

```text
Farm → Field → Zone → SensorNode → Measurement
Field → SoilMapUnit
Field → HydrologyCell
Field → Paddock
Paddock → GrazingEvent
Measurement → OntologyLayer
Observation → Decision → Intervention
SensorReading → AuditRecord
```

The current ontology and Farmer Activity Overlay should drive the initial node and edge types.

---

## Work Package 4: Dashboard Intelligence Cards

Implement card types before fancy visualization:

```text
Water Retention Card
Grazing Readiness Card
Soil Biology Activity Card
Plant Stress Card
Tank/Water Security Card
Paddock Recovery Card
MRV Evidence Card
Sensor Health Card
```

Each card must include:

```text
observation
context
farmer meaning
suggested inspection
possible intervention
evidence
confidence
```

---

## Work Package 5: Sensor Node MVP

Build one low-cost node:

```text
ESP32 or Uno-compatible controller
soil moisture
soil temperature
air temp/RH
optional rain gauge
optional relay/valve state
signed JSON event output
local buffering if offline
```

Event shape:

```json
{
  "schema": "sais.observation.v1",
  "node_id": "node-soil-001",
  "farm_id": "farm-local",
  "field_id": "field-a",
  "zone_id": "zone-a1",
  "timestamp": "2026-05-01T12:00:00Z",
  "measurement_id": "soil.moisture.vwc",
  "layer": "SoilPhysics",
  "value": 0.23,
  "unit": "m3/m3",
  "measurement_basis": "direct",
  "confidence": "medium",
  "source": {
    "type": "sensor",
    "sensor_model": "capacitive_probe",
    "depth_cm": 30
  }
}
```

---

# 9. Key engineering constraints

## Keep it low/no cost

Preference order:

```text
1. open public data
2. farmer manual input
3. low-cost sensors
4. reused farm equipment
5. optional advanced packages
```

Do not require drones, livestock tags, CO₂ flux chambers, or AI cameras for the MVP.

## Treat proxies honestly

Any indirect measurement must be labeled as proxy.

Examples:

```text
CO₂ flux → microbial respiration proxy
audio → rumination/methane proxy
NDVI → plant vigor proxy
cheap NPK → nutrient trend proxy
```

## Build for degraded/offline mode

The farm twin must still work with:

```text
no internet
missing weather API
dead sensor
manual-only field entry
delayed satellite imagery
```

## Separate evidence from recommendation

The system should never hide how it reached a recommendation.

Every recommendation needs an evidence chain.

---

# 10. Immediate next steps

1. Build `MEASUREMENT_INTELLIGENCE_INVENTORY.md`.
2. Build `measurement_inventory.yaml`.
3. Normalize measurement IDs.
4. List open geospatial data layers required for MVP.
5. Define the first dashboard cards.
6. Implement a basic farm boundary + DEM + soil + moisture dashboard.
7. Add the first low-cost soil node.
8. Connect observations to farmer decisions and interventions.
9. Add signed audit records after the first event flow works.
10. Only then consolidate the ontology into the canonical machine-readable schema.

The engineering priority is:

```text
Measurement → Meaning → Farmer Decision → Intervention → Evidence
```

That should become the design rule for the whole SAIS platform.
