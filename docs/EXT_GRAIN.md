# SAIS Extension: Grain Storage & Post-Harvest

## Overview
Grain spoilage in silos is a massive, invisible economic drain. Moisture migration, insect infestation, and fungal growth create localized "hot spots" that can ruin thousands of bushels before they are detected. The SAIS architecture provides continuous, multi-depth monitoring of the grain mass, utilizing the same UNO Q Controller Layer and DDS mesh for telemetry.

## Hardware Integration

| Component | Interface | Purpose |
|---|---|---|
| **DS18B20 Temperature Sensor Cable (x10)** | 1-Wire | Suspended vertically through the grain mass to map the temperature profile and detect hot spots. |
| **SCD41 CO2 Sensor** | I2C | Measures CO2 concentration in the headspace. A rising CO2 level is the earliest indicator of insect or fungal respiration. |
| **BME280 Environmental Sensor** | I2C | Measures ambient temperature and humidity outside the silo for aeration control. |
| **SparkFun Qwiic Relay** | I2C | Controls the silo aeration fans. |

## Software & Intelligence Layer
The Intelligence Layer ingests the temperature profile and headspace CO2 levels. The primary inference model detects the onset of spoilage by analyzing the rate of temperature change and the absolute CO2 concentration.

When a hot spot or rising CO2 is detected, the node autonomously activates the Qwiic Relay to turn on the aeration fans, drawing cool, dry air through the grain mass to stabilize it. The system also monitors ambient weather conditions, ensuring the fans only run when the outside air is cooler and drier than the grain, preventing the introduction of moisture.

---
*Copyright © 2026 NB11B. All rights reserved.*
