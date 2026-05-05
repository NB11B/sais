# Regenerative Agriculture Signal Methodology

## Purpose

This methodology defines how SAIS uses merged field signals to support regenerative agriculture from the soil upward.

The core claim is that farm health, like biological health, cannot be diagnosed reliably from a single signal. In biology, temperature, pulse, blood pressure, oxygen saturation, lab results, imaging, and symptoms are interpreted together to differentiate causes. SAIS applies the same diagnostic principle to working land.

SAIS treats farm telemetry as a living diagnostic signal system:

```text
soil signals
+ water signals
+ plant signals
+ weather signals
+ animal signals
+ infrastructure signals
+ operator observations
-> condition inference
-> regenerative decision support
-> auditable action history
```

The goal is not to create a generic sensor dashboard. The goal is to connect measurements to the biological and operational functions that make land more resilient, productive, and regenerative over time.

## Measurement-to-Meaning Chain

SAIS uses this chain:

```text
farm question
-> measurable indicators
-> sensor or observation source
-> signal fusion
-> condition inference
-> confidence level
-> inspection or action recommendation
-> outcome tracking
```

This allows SAIS to move from isolated readings to interpreted conditions.

Example isolated reading:

```text
soil moisture = 18 percent
```

Example interpreted condition:

```text
Zone A1 is drying faster than comparable zones after the same rainfall.
Possible causes: compaction, low organic matter, shallow rooting, bare soil, or excessive grazing pressure.
Recommended next step: inspect soil cover, infiltration, and grazing recovery before making irrigation or reseeding decisions.
```

## Why Signal Fusion Matters

A single farm signal is often ambiguous.

Example:

```text
low soil moisture
```

could mean:

```text
drought stress
rapid drainage
low organic matter
compaction and runoff
excessive plant uptake
sensor placement error
grazing-induced bare soil exposure
```

Merged signals differentiate the cause.

### Example 1: Poor Infiltration or Runoff

```text
low soil moisture
+ recent rainfall
+ weak soil moisture response
+ high runoff risk
+ bare soil observation
-> likely water loss through runoff or poor infiltration
```

### Example 2: Atmospheric Drydown

```text
low soil moisture
+ no recent rainfall
+ high temperature
+ low humidity
+ strong wind
-> likely atmospheric drydown pressure
```

### Example 3: Productive Water Use

```text
low soil moisture
+ strong canopy
+ high plant vigor
+ normal rainfall
+ no visible stress
-> likely productive water use rather than immediate field failure
```

This is the central method: SAIS does not only ask what a measurement is. It asks what the measurement means in context.

## Regenerative Agriculture Frame

Regenerative agriculture depends on improving farm function, especially:

```text
soil cover
water infiltration
water retention
root depth
biological activity
nutrient cycling
plant recovery
grazing balance
biodiversity
resilience to weather stress
```

SAIS supports regenerative agriculture by measuring indicators that reveal whether these functions are improving, degrading, or requiring inspection.

The diagnostic stack is organized from the soil upward:

```text
soil function
-> water behavior
-> plant response
-> animal interaction
-> infrastructure support
-> productivity outcome
```

## Soil-Up Diagnostic Stack

### 1. Soil Function Layer

Primary questions:

```text
Is the soil accepting water?
Is the soil holding water?
Is the root zone active?
Is compaction or bare soil limiting productivity?
Is biological function likely improving or degrading?
```

Useful measurements:

```text
soil moisture
soil temperature
soil electrical conductivity
soil type
organic matter from periodic tests
manual compaction readings
surface cover from image or field observation
```

Regenerative meaning:

```text
higher infiltration
slower drydown
stable soil temperature
greater water retention
reduced bare soil exposure
deeper rooting potential
more resilient microbial habitat
```

### 2. Water Behavior Layer

Primary questions:

```text
Did rainfall enter the root zone?
Did the field retain water after rain?
Is water pooling, running off, or disappearing too quickly?
Are some zones behaving worse than comparable zones?
```

Useful measurements:

```text
rainfall
soil moisture response after rainfall
soil moisture drydown rate
surface wetness
runoff risk from terrain
soil hydrologic group
flow accumulation
water tank or irrigation flow when applicable
```

Regenerative meaning:

```text
improved infiltration
increased effective rainfall
reduced runoff
reduced erosion risk
longer water availability between rainfall events
improved drought resilience
```

### 3. Plant and Pasture Response Layer

Primary questions:

```text
Is pasture recovering after grazing?
Is vegetation stressed?
Is plant cover improving?
Is biomass increasing or declining?
Is bare ground expanding?
```

Useful measurements:

```text
fixed RGB images
manual pasture observations
canopy cover
pasture height or biomass proxy
NDVI or vegetation index when available
canopy temperature when available
soil moisture context
rainfall context
```

Regenerative meaning:

```text
faster recovery
better ground cover
more photosynthetic activity
reduced erosion exposure
improved forage availability
improved root contribution to soil structure
```

### 4. Animal Interaction Layer

Primary questions:

```text
Are animals applying pressure evenly or unevenly?
Are they overusing a paddock?
Are they reaching water reliably?
Is heat stress changing behavior?
Is recovery time sufficient before re-grazing?
```

Useful measurements:

```text
grazing start and stop records
manual livestock observations
water tank level
water-area presence
weather heat index
optional livestock GPS or accelerometer data
gate state
```

Regenerative meaning:

```text
balanced grazing pressure
adequate recovery time
reduced overgrazing
improved manure distribution
better pasture utilization
lower water-access risk
```

### 5. Weather and Microclimate Layer

Primary questions:

```text
Is the field under heat, cold, wind, or drydown stress?
Did rainfall occur locally?
Is evapotranspiration pressure high?
Are disease or frost risks increasing?
```

Useful measurements:

```text
air temperature
relative humidity
rainfall
barometric pressure
wind speed and direction
solar radiation or light
leaf wetness when relevant
```

Regenerative meaning:

```text
better interpretation of drydown
heat stress awareness
frost risk awareness
disease pressure context
weather-normalized productivity comparison
```

### 6. Infrastructure Support Layer

Primary questions:

```text
Is the sensor network trustworthy?
Are water systems functioning?
Are pumps, tanks, gates, and power systems healthy?
Is field telemetry stale or degraded?
```

Useful measurements:

```text
node uptime
last telemetry timestamp
battery voltage
solar charge state
pump current
tank level
flow rate
water pressure
gate state
fault codes
```

Regenerative meaning:

```text
reliable observation
reduced water failure risk
better timing of interventions
lower maintenance uncertainty
higher operator trust in the system
```

## Diagnostic Differentiation Method

SAIS should differentiate similar-looking symptoms by merging signals.

### Symptom: Low Soil Moisture

| Possible Cause | Differentiating Signals |
|---|---|
| Drought | low rainfall, high temperature, low humidity, normal infiltration response |
| Runoff or poor infiltration | recent rain, weak soil moisture response, high slope, bare soil, flow accumulation |
| Low water-holding capacity | normal rainfall, fast drydown, poor recovery compared to similar zones |
| Productive plant uptake | strong canopy, high growth, normal rainfall, low stress indicators |
| Sensor problem | implausible flatline, no response to rainfall, nearby sensors disagree |

### Symptom: Poor Pasture Recovery

| Possible Cause | Differentiating Signals |
|---|---|
| Water limitation | low soil moisture, low rainfall, high drydown pressure |
| Overgrazing | recent grazing record, low cover, slow regrowth, animal pressure history |
| Compaction | poor infiltration after rain, penetrometer note, pooling or runoff |
| Heat stress | high temperature, low humidity, high canopy temperature |
| Fertility or pH issue | repeated poor growth despite adequate water, soil test context |

### Symptom: Water Asset Risk

| Possible Cause | Differentiating Signals |
|---|---|
| Tank drawdown | falling tank level, livestock presence, no refill event |
| Pump failure | pump current absent, tank not rising, pressure low |
| Leak | flow detected without expected use, pressure drop, tank decline |
| Telemetry problem | stale node, low battery, publish failures |

## Confidence Scoring

SAIS should assign confidence based on signal agreement, freshness, and source quality.

Suggested levels:

```text
high     multiple fresh signals agree and source quality is strong
medium   one strong signal plus supporting context
low      weak, stale, conflicting, or uncalibrated signals
unknown  insufficient evidence
```

## Decision Support Rule

SAIS should translate fused signals into inspection and management prompts, not unsupported automatic prescriptions.

Good decision card language:

```text
Zone A1 is showing faster drydown than comparable zones after rainfall.
Evidence: rainfall occurred, soil moisture rose weakly, drydown accelerated, runoff risk is high.
Suggested inspection: check soil cover, compaction, infiltration, and grazing pressure.
```

Avoid unsupported claims:

```text
Apply fertilizer now.
Irrigate now.
This field is unhealthy.
```

The system should present evidence and recommended inspection first. Management action remains operator-owned.

## Sensor Selection Method

Sensors should be chosen by contribution to diagnosis, not novelty.

Evaluation criteria:

```text
What farm-health question does this sensor help answer?
What ambiguity does it reduce?
What decision card could it improve?
How reliable is the measurement in field conditions?
How expensive is it to deploy and maintain?
Can the value be cross-checked by another signal?
Does it support regenerative function from soil upward?
```

A sensor belongs in SAIS when it improves one or more of:

```text
soil function interpretation
water behavior interpretation
plant recovery interpretation
grazing balance
livestock safety
infrastructure reliability
operator confidence
```

## First Integration Priorities

Recommended first layer:

```text
GPS node identity and placement
air temperature and humidity
soil moisture
soil temperature
rainfall
node uptime
battery voltage
last telemetry timestamp
```

Recommended second layer:

```text
tank level
pump current
gate state
fixed RGB field image
barometric pressure
wind speed and direction
```

Recommended later layer:

```text
NDVI or multispectral imaging
thermal canopy sensing
soil electrical conductivity
pasture height sensing
livestock GPS or accelerometer tags
leaf wetness
flow rate
water pressure
```

Use caution with:

```text
cheap continuous NPK sensors
cheap continuous pH sensors
overly complex multispectral systems before basic telemetry is stable
full mesh networking before one-node telemetry is reliable
```

## Method Summary

SAIS supports regenerative agriculture by measuring soil-up system function, merging signals to differentiate causes, assigning confidence, and producing evidence-backed inspection prompts.

The intended result is not just more data. The intended result is better land stewardship, better productivity decisions, and a clearer operational record of how the farm system is changing over time.
