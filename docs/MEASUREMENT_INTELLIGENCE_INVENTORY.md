# Measurement Intelligence Inventory

**Status:** Active Development
**Purpose:** This document catalogs all measurements supported by the SAIS platform, tracing them from physical sensor or data source, through the causal ontology layer, to the operational meaning for the farmer.

Every measurement strictly adheres to the principle: **Measurement → Meaning → Farmer Decision → Intervention → Evidence**.

---

## 1. Soil Biology

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `soil.biology.respiration` | SoilBiology | proxy | NDIR CO₂ chamber | Is microbial activity increasing/decreasing? | Biological Engine Status | Medium | Medium |
| `soil.biology.temp` | SoilBiology | direct | DS18B20 / thermistor | Is soil warm enough for biological activity? | Biology Context | High | Low |
| `soil.biology.moisture` | SoilBiology | direct | capacitive probe | Is biology limited by dry/saturated conditions? | Respiration Context | High | Low |
| `soil.biology.earthworms` | SoilBiology | manual | shovel test | Is the soil food web active? | Biological Health Score | High | Free |
| `soil.biology.residue` | SoilBiology | manual | photo/observation | Is decomposition active? | Carbon Cycling Trend | High | Free |

---

## 2. Soil Chemistry

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `soil.chemistry.ph` | SoilChemistry | direct | cheap probe/strips | Are nutrients chemically available? | pH Constraint Warning | Medium | Low |
| `soil.chemistry.ec` | SoilChemistry | direct | EC probe | Salinity/fertility pulse | Salt/Fertility Trend | Medium | Low |
| `soil.chemistry.npk_trend`| SoilChemistry | proxy | ISE/NPK probe | Nutrient trend (not lab-grade truth) | Trend Only | Low | Medium |
| `soil.chemistry.soc` | SoilChemistry | manual | lab import | Long-term carbon baseline | MRV Baseline | High | High |
| `soil.chemistry.brix` | SoilChemistry | manual | refractometer | Plant sugar / photosynthesis proxy | Plant Energy Score | Medium | Low |

---

## 3. Soil Physics

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `soil.physics.vwc` | SoilPhysics | direct | moisture probe | Is water available in root zone? | Moisture Trend | High | Low |
| `soil.physics.infiltration`| SoilPhysics | derived | rain + moisture | Did rainfall infiltrate or run off? | Runoff Risk / Infiltration | Medium | Low |
| `soil.physics.compaction` | SoilPhysics | manual | penetrometer | Where are hard layers? | Root Restriction Map | High | Low |
| `soil.physics.cover` | SoilPhysics | manual/open | camera/satellite | Is soil armored? | Evaporation/Erosion Risk | High | Free/Low |

---

## 4. Plant Health

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `plant.health.ndvi` | PlantHealth | open_data | Sentinel-2 / Landsat | Is plant vigor rising or falling? | Vigor Map | High | Free |
| `plant.health.canopy` | PlantHealth | open_data | satellite / camera | Is soil protected? | Armor Score | High | Free |
| `plant.health.stress` | PlantHealth | derived | VPD + canopy + VWC | Is the plant under transpiration stress? | Transpiration Stress | Medium | Low |

---

## 5. Water Cycle & Hydrology

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `water.terrain.elevation` | Hydrology | open_data | DEM (USGS/LiDAR) | What is the terrain shape? | Base Terrain Twin | High | Free |
| `water.terrain.slope` | Hydrology | derived | DEM | Where is erosion/runoff likely? | Erosion Risk | High | Free |
| `water.flow.accumulation` | Hydrology | derived | DEM | Where does water concentrate? | Water Path Map | High | Free |
| `water.cycle.rainfall` | Hydrology | open/direct | radar / gauge | Water input | Rain Event Trigger | High | Free/Low |
| `water.storage.tank` | Hydrology | direct | ultrasonic sensor | Water availability | Water Security | High | Low |

---

## 6. Atmosphere & Microclimate

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `atmosphere.air.temp` | Atmosphere | direct | BME280/SHT31 | Heat/frost risk | Microclimate Layer | High | Low |
| `atmosphere.air.rh` | Atmosphere | direct | BME280/SHT31 | Disease and stress context | Humidity Map | High | Low |
| `atmosphere.air.vpd` | Atmosphere | derived | temp + RH | Plant transpiration stress | VPD Stress Card | High | Low |

---

## 7. Livestock

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `livestock.location.gps` | Livestock | direct | GPS/LoRa tags | Where is the herd? | Herd Heatmap | High | Medium |
| `livestock.health.rumination`| Livestock | proxy | acoustic/IMU | Digestive behavior | Health Proxy | Medium | Medium |
| `livestock.management.density`| Livestock | derived | count + area + GPS| Grazing pressure | Impact per Acre | High | Low |
| `livestock.management.rest` | Livestock | derived | grazing history | Recovery status | Grazing Readiness | High | Free |

---

## 8. Ecosystem & Biodiversity

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `ecosystem.habitat.edge` | Ecosystem | open_data | NLCD / map | Refuge/corridor strength | Habitat Connectivity | Medium | Free |
| `ecosystem.fauna.pollinator`| Ecosystem | manual | observation | Habitat function | Pollinator Score | High | Free |

---

## 9. Market, MRV, and Audit

| ID | Layer | Measurement Basis | Source | Farmer Meaning | Dashboard Card | Confidence | Cost Profile |
|---|---|---|---|---|---|---|---|
| `audit.event.intervention` | Ledger | manual | app/log | What was done and when? | Intervention Ledger | High | Free |
| `audit.security.hash` | Ledger | derived | gateway signing | Can data be trusted? | Audit Integrity | High | Free |
