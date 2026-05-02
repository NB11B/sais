# SAIS Knowledge Requirements Doctrine

## Purpose

SAIS must scale beyond any specific sensor, dashboard, or hardware package. The platform needs a clear doctrine for how any data source contributes to the operator's understanding of the farm or ranch.

This document defines the flow from raw data to operational knowledge.

SAIS is not a sensor dashboard. It is a farm/ranch C4ISR system.

The core problem is:

```text
What does the operator need to know?
What evidence answers that question?
What source can provide that evidence?
How reliable is that source?
What condition does the evidence indicate?
What action, inspection, or decision does it support?
```

---

## C4ISR Translation

Military C4ISR systems organize information around command needs, intelligence requirements, collection, fusion, and action. SAIS should use the same structure, translated for farm/ranch operations.

| Military Concept | SAIS Equivalent |
|---|---|
| Commander's Intent | Operator's farm/ranch objective |
| Priority Intelligence Requirement (PIR) | Priority Farm Knowledge Requirement (PFKR) |
| Essential Elements of Information (EEI) | Required Measurements / Required Observations |
| Named Area of Interest (NAI) | Field, paddock, management zone, tank, riparian area, lane, gate, or structure |
| Indicator and Warning (I&W) | Threshold, trend, anomaly, stale source, risk pattern |
| Collection Plan | Sensor, manual observation, open data, geospatial layer, weather feed |
| Intelligence Fusion | FarmGraph + card engine + evidence chain |
| Course of Action (COA) | Suggested inspection, intervention, delay, move, repair, monitor |
| Battle Damage Assessment (BDA) | Post-action observation and outcome tracking |

The important lesson is that data is not valuable merely because it exists. Data is valuable when it answers a knowledge requirement.

---

## Core Flowthrough Model

Every datum should pass through this chain:

```text
Source
→ Measurement / Observation
→ Domain Layer
→ Indicator
→ Knowledge Requirement
→ Farmer/Rancher Meaning
→ Suggested Inspection or Action
→ Evidence Record
→ Follow-up Outcome
```

Example:

```text
rain gauge reading
→ weather.rainfall.hourly = 25 mm
→ Atmosphere / WaterCycle
→ heavy recent rainfall
→ Did rainfall enter the soil or run off?
→ inspect high-runoff zones and compare soil moisture response
→ WaterRetentionCard evidence
→ field note after inspection
```

---

## Priority Farm Knowledge Requirements

A Priority Farm Knowledge Requirement is a question the operator must be able to answer to manage the farm or ranch.

PFKRs should be stable even as sensors change.

Sensors, weather feeds, imagery, manual observations, and lab reports are all just ways of answering these requirements.

---

## PFKR-1: Water Status and Movement

### Operator Question

```text
Where is water entering, moving, pooling, being stored, or being lost?
```

### Why It Matters

Water drives plant recovery, grazing timing, erosion risk, pond/tank security, compaction risk, biological activity, and access decisions.

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Recent rainfall | rain gauge, weather station, open weather, manual entry | direct/open/manual |
| Soil moisture by depth | capacitive probe, tensiometer, gypsum block | direct |
| Terrain slope | DEM-derived layer | open/derived |
| Flow accumulation | DEM-derived hydrology | derived |
| Hydrologic soil group | SSURGO or local soil survey | open |
| Surface cover | manual estimate, imagery, camera | manual/open/direct |
| Pond/tank level | ultrasonic sensor, pressure sensor, manual check | direct/manual |
| Runoff evidence | field note, photo, turbidity, sediment observation | manual/direct |

### Indicators

```text
rainfall with no deep moisture response
rapid post-rain moisture loss
high slope + poor cover
high flow accumulation near bare soil
ponding in low-lying area
falling tank level during heat/high demand
```

### Cards / Outputs

```text
WaterRetentionCard
RunoffRiskCard
Tank/WaterSecurityCard
GrazingAccessRiskCard
```

### Actions Supported

```text
inspect runoff path
check crusting or compaction
delay grazing
move herd away from wet/fragile area
check tank/valve/pump
adjust irrigation or water distribution
```

---

## PFKR-2: Grazing Readiness and Recovery

### Operator Question

```text
Which paddocks or zones are ready for grazing, need more rest, or should be avoided?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Last grazing event | manual entry, future gate/fence event | manual/direct |
| Rest period | derived from grazing history | derived |
| Plant recovery | visual estimate, NDVI, camera, manual note | manual/open/direct |
| Soil moisture | sensor or manual assessment | direct/manual |
| Weather stress | temperature, VPD, wind, rainfall forecast | direct/open/derived |
| Stocking pressure | herd count, paddock area, livestock GPS | manual/direct/derived |
| Manure score | manual/photo | manual |
| Ground cover | manual/camera/satellite | manual/direct/open |

### Indicators

```text
short rest period
low regrowth after prior grazing
low soil moisture during high VPD
high grazing pressure near water point
bare soil after herd movement
poor manure score or animal behavior change
```

### Cards / Outputs

```text
GrazingReadinessCard
PaddockRecoveryCard
GrazingPressureCard
LivestockDistributionCard
```

### Actions Supported

```text
delay move
reduce stocking density
move herd
adjust water/mineral placement
rest paddock longer
inspect plant recovery before entry
```

---

## PFKR-3: Soil Function and Biological Activity

### Operator Question

```text
Is the soil functioning as a living system capable of absorbing water, cycling nutrients, and supporting plants?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Soil temperature | probe | direct |
| Soil moisture | probe/manual | direct/manual |
| Soil respiration / CO2 | NDIR chamber | proxy/direct |
| Earthworm count | shovel test | manual |
| Aggregate stability | slake test | manual |
| Infiltration rate | ring test, rainfall response | manual/derived |
| Root depth | field dig | manual |
| Residue breakdown | manual/photo | manual/direct |
| pH / EC / lab results | field meter, lab import | direct/lab |

### Indicators

```text
warm and moist soil with low respiration
rainfall does not infiltrate
surface seals or crusts
roots shallow despite moisture
residue breakdown stalled
earthworm counts low
```

### Cards / Outputs

```text
SoilFunctionCard
BiologicalActivityCard
InfiltrationConstraintCard
CompactionRiskCard
```

### Actions Supported

```text
inspect roots
run slake or infiltration test
avoid traffic/grazing when wet
increase cover/armor
consider biological or organic matter intervention
plan decompaction strategy
```

---

## PFKR-4: Plant Condition and Production Risk

### Operator Question

```text
Are plants recovering, growing, and photosynthesizing normally, or are they showing stress?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Plant vigor | NDVI, camera, manual estimate | open/direct/manual |
| Canopy cover | imagery, camera, manual | open/direct/manual |
| Brix | refractometer | manual |
| Leaf temperature | IR/thermal | direct |
| Pest/disease signs | manual/camera | manual/direct |
| Soil moisture | sensor | direct |
| VPD and weather stress | weather station/open data | direct/open/derived |
| Growth stage | manual entry | manual |

### Indicators

```text
vigor decline after weather event
high VPD + low moisture
canopy cover loss
hot leaf temperature
pest/disease observation
low Brix trend
```

### Cards / Outputs

```text
PlantStressCard
CanopyCoverCard
PestInspectionCard
ProductionRiskCard
```

### Actions Supported

```text
inspect stress zone
adjust grazing or harvest timing
check pests or disease
adjust irrigation
protect soil cover
sample plant tissue or soil if needed
```

---

## PFKR-5: Livestock Health, Distribution, and Pressure

### Operator Question

```text
Are animals healthy, distributed properly, and applying the intended pressure to the land?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Herd location | GPS tag, manual observation | direct/manual |
| Movement/activity | accelerometer, camera, manual | direct/manual |
| Water visits | tank sensor, RFID, manual | direct/manual |
| Body condition score | manual/photo | manual |
| Manure score | manual/photo | manual |
| Stocking density | herd count + paddock area | derived |
| Time in paddock | grazing event log | manual/derived |
| Weather heat stress | temperature, humidity, VPD | direct/open/derived |

### Indicators

```text
animals camping near water
low movement during heat
unexpected absence from water
high pressure on small zone
poor manure score
body condition decline
```

### Cards / Outputs

```text
LivestockDistributionCard
WaterAccessCard
HeatStressCard
GrazingPressureCard
```

### Actions Supported

```text
move herd
check water source
move mineral/salt
adjust paddock size
inspect animals
change grazing plan
```

---

## PFKR-6: Infrastructure, Access, and Field Operations

### Operator Question

```text
Are fences, gates, water infrastructure, roads, and access paths operational and safe?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Fence line location | GIS asset, manual mapping | GIS/manual |
| Gate status | manual, future sensor | manual/direct |
| Tank/pond level | sensor/manual | direct/manual |
| Pump/valve state | relay telemetry/manual | direct/manual |
| Road/lane condition | manual note/photo | manual |
| Flooded access | rainfall + terrain + manual | derived/manual |
| Battery/power state | node telemetry | direct |
| Sensor last seen | system telemetry | derived |

### Indicators

```text
sensor offline
pump/valve state mismatch
water level falling unexpectedly
fence layer intersects grazing boundary issue
road inaccessible after rainfall
node battery low
```

### Cards / Outputs

```text
SensorHealthCard
InfrastructureStatusCard
WaterInfrastructureCard
AccessRiskCard
```

### Actions Supported

```text
inspect node
repair fence
check tank or pump
avoid wet access path
switch water source
replace battery or solar panel
```

---

## PFKR-7: Weather and Exposure

### Operator Question

```text
What atmospheric conditions are affecting livestock, plants, water, fire risk, and field work?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Temperature | weather station/open/manual | direct/open/manual |
| Humidity | weather station/open | direct/open |
| Rainfall | gauge/open/manual | direct/open/manual |
| Wind speed/direction | station/open | direct/open |
| VPD | derived from temp/RH | derived |
| Heat index | derived | derived |
| Forecast | open weather, manual planning | open |
| Lightning/fire context | future open source/manual | open/manual |

### Indicators

```text
high VPD
heavy rainfall
dry windy conditions
heat stress conditions
freeze risk
forecast conflicts with planned field work
```

### Cards / Outputs

```text
WeatherContextCard
HeatStressCard
FieldWorkWindowCard
FireWeatherWatchCard
```

### Actions Supported

```text
delay grazing or field work
inspect water access
adjust irrigation
prepare shelter/shade
monitor fire risk
move animals before storm/heat event
```

---

## PFKR-8: Source Health and Confidence

### Operator Question

```text
Can I trust the current operating picture?
```

### Essential Elements of Information

| EEI | Source Options | Basis |
|---|---|---|
| Sensor last seen | system telemetry | derived |
| Data freshness | observation timestamp | derived |
| Source type | registry | metadata |
| Source confidence | registry + calibration | metadata/derived |
| Duplicate or missing readings | telemetry system | derived |
| Manual confirmation | field note | manual |
| Registry validity | source/layer/GIS registry | system |

### Indicators

```text
sensor stale
weather feed stale
missing zone assignment
invalid observation payload
unmapped sensor node
conflicting evidence
low-confidence proxy used alone
```

### Cards / Outputs

```text
SensorHealthCard
SourceHealthCard
FarmSetupCompletenessCard
ConfidenceWarningCard
```

### Actions Supported

```text
inspect node
calibrate sensor
confirm manually
assign sensor to zone
repair source registry
ignore unsupported recommendation until confirmed
```

---

## Data Source Classes

Every source must declare its class and trust posture.

```text
direct_sensor
manual_observation
open_weather
open_geospatial
derived
proxy
lab_import
gis_asset
system_telemetry
```

Each source should define:

```yaml
source_id: direct_sensor
source_class: direct_sensor
trust_level: high
latency: realtime
cost_profile: low
operator_notes: "Physical sensor; requires calibration and last-seen checks."
```

---

## Measurement Rule Format

Each measurement should be mapped to what it informs.

```yaml
measurement_id: soil.moisture.vwc
source_classes:
  - direct_sensor
domain_layers:
  - SoilPhysics
  - WaterCycle
knowledge_requirements:
  - PFKR-1
  - PFKR-2
  - PFKR-3
indicators:
  - low_root_zone_water
  - rainfall_infiltration_response
cards:
  - WaterRetentionCard
  - GrazingReadinessCard
operator_meaning: "Indicates whether water is available in the root zone and whether rainfall is infiltrating."
inspection_prompts:
  - "Check for runoff, crusting, compaction, or bare soil."
```

---

## Rule Engine Doctrine

Rules should be deterministic before they are predictive.

A rule should declare:

```text
what knowledge requirement it answers
what sources it uses
what evidence it requires
what status values it may emit
what confidence level is justified
what operator action it supports
what missing data changes the status to
```

Example:

```yaml
rule_id: water_retention_after_rain
answers: PFKR-1
requires:
  - weather.rainfall.hourly
  - soil.moisture.vwc
uses_context:
  - runoff_risk
  - slope
  - hydrologic_soil_group
status_logic:
  watch: "rainfall present and deep moisture did not rise"
  ok_with_warning: "rainfall present but moisture response unknown"
  insufficient_data: "no recent moisture observation"
  stale_data: "weather or moisture observations outside freshness window"
operator_action:
  - inspect runoff path
  - check compaction or crusting
  - delay grazing if soil is fragile
```

---

## Evidence Chain Requirement

Every intelligence card must show its evidence chain.

Minimum evidence fields:

```text
measurement_id
source_id or source_type
value
unit
timestamp
location: farm / field / zone / asset
confidence
freshness
```

Cards should never hide uncertainty.

Allowed card statuses:

```text
ok
watch
action
alert
ok_with_warning
insufficient_data
insufficient_context
invalid_data
stale_data
```

---

## Collection Planning

Before adding a sensor, define the knowledge requirement it serves.

Use this checklist:

```text
1. What PFKR does this source answer?
2. What measurement does it provide?
3. What action could this measurement change?
4. What location does it apply to?
5. What freshness window matters?
6. What confidence level is justified?
7. What manual observation could confirm or refute it?
8. What card or dashboard layer should use it?
```

If a source does not answer a knowledge requirement, it should not be prioritized.

---

## Dashboard Implications

The UI should be organized around knowledge requirements, not raw sensor lists.

Recommended dashboard grouping:

```text
Water
Grazing
Soil Function
Plant Condition
Livestock
Infrastructure
Weather
Source Health
```

Each group should show:

```text
current status
supporting evidence
missing data
recommended inspection
action history
```

---

## Expansion Rule

Any future data source must be added through this sequence:

```text
1. Add or identify PFKR.
2. Define EEIs it contributes.
3. Register source class.
4. Register measurement IDs.
5. Map measurements to domain layers.
6. Define freshness and confidence rules.
7. Define which cards or layers consume it.
8. Add tests proving degraded behavior.
9. Only then expose it in the UI.
```

This preserves SAIS as a coherent operating platform instead of a pile of feeds.

---

## Bottom Line

SAIS should expand around knowledge requirements, not around sensors.

The core doctrine is:

```text
Need to know
→ evidence required
→ source collection
→ fusion rule
→ farmer/rancher meaning
→ inspection/action
→ outcome record
```

That doctrine is what allows weather, water, soil, livestock, GIS assets, manual notes, sensor telemetry, and future hardware to contribute to the same operating picture.
