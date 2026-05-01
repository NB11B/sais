# SAIS Extension: Precision Irrigation

## Overview
Water scarcity is the defining challenge of modern agriculture. Traditional irrigation relies on timers or visual inspection, leading to overwatering, nutrient leaching, and wasted energy. The SAIS architecture extends to precision irrigation by deploying dense arrays of soil moisture sensors and integrating them with automated valve control, driven by real-time evapotranspiration (ET) modeling.

## Hardware Integration

| Component | Interface | Purpose |
|---|---|---|
| **Capacitive Soil Moisture Sensor (x3)** | Analog / I2C | Deployed at multiple depths (e.g., 10cm, 30cm, 60cm) to map the moisture profile and root zone. |
| **BME280 Environmental Sensor** | I2C | Measures ambient temperature, humidity, and pressure for ET calculations. |
| **SparkFun Qwiic Relay (x4)** | I2C | Controls 24VAC irrigation solenoid valves for individual zones. |
| **Flow Meter (Pulse Output)** | Digital In | Measures actual water volume delivered to the zone. |

## Software & Intelligence Layer
The Intelligence Layer ingests the multi-depth moisture profile and the ambient weather data. It calculates the daily crop water requirement (ETc) based on the specific crop type and growth stage. 

Instead of watering on a fixed schedule, the node autonomously opens the solenoid valve only when the root zone moisture drops below the critical threshold (Management Allowed Depletion). It closes the valve precisely when the moisture reaches field capacity, preventing deep percolation and nutrient loss. The flow meter confirms delivery, and any discrepancy (e.g., a stuck valve or broken pipe) triggers an immediate alert.

---
*Copyright © 2026 NB11B. All rights reserved.*
