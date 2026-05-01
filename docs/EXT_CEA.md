# SAIS Extension: Controlled Environment Agriculture (CEA)

## Overview
Greenhouses and indoor vertical farms require precise control over every environmental variable. The SAIS architecture extends to CEA by deploying dense arrays of microclimate sensors and integrating them with automated climate control systems, driven by real-time Vapor Pressure Deficit (VPD) and Photosynthetic Photon Flux Density (PPFD) modeling. This is the direct bridge to the orbital habitat use case.

## Hardware Integration

| Component | Interface | Purpose |
|---|---|---|
| **SCD41 CO2 Sensor** | I2C | Measures CO2 concentration for automated enrichment. |
| **BME280 Environmental Sensor** | I2C | Measures ambient temperature, humidity, and pressure for VPD calculations. |
| **VEML7700 Ambient Light Sensor** | I2C | Measures light intensity (lux) to estimate PPFD and Daily Light Integral (DLI). |
| **SparkFun Qwiic Relay (x4)** | I2C | Controls ventilation fans, shade cloths, CO2 injection, and supplemental lighting. |

## Software & Intelligence Layer
The Intelligence Layer ingests the microclimate data and calculates the real-time VPD, which is the primary driver of plant transpiration and nutrient uptake. 

Instead of controlling temperature and humidity independently, the node autonomously adjusts ventilation, shading, and misting to maintain the optimal VPD target for the specific crop and growth stage. It also tracks the cumulative light exposure (DLI) and supplements with artificial lighting only when the natural sunlight falls short of the daily target, optimizing energy use.

---
*Copyright © 2026 NB11B. All rights reserved.*
