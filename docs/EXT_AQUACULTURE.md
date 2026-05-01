# SAIS Extension: Aquaculture & Water Systems

## Overview
Aquaculture and large-scale water management systems (stock ponds, irrigation reservoirs) require continuous monitoring of water quality parameters. A sudden drop in dissolved oxygen (DO) or a spike in ammonia can cause catastrophic fish kills within hours. The SAIS architecture extends naturally to this domain by replacing soil sensors with submersible water quality probes, utilizing the same UNO Q Controller Layer and DDS mesh for telemetry.

## Hardware Integration

| Component | Interface | Purpose |
|---|---|---|
| **Atlas Scientific EZO-DO Circuit & Probe** | I2C | Measures Dissolved Oxygen (DO) continuously. Critical for fish health and aeration control. |
| **Atlas Scientific EZO-pH Circuit & Probe** | I2C | Measures water pH. |
| **DS18B20 Waterproof Temperature Sensor** | 1-Wire | Submersible temperature measurement for DO compensation and thermal stratification monitoring. |
| **SparkFun Qwiic Relay** | I2C | Triggers surface aerators or emergency oxygen injection when DO drops below threshold. |

## Software & Intelligence Layer
The Intelligence Layer ingests the continuous DO, pH, and temperature streams. The primary inference model predicts DO crashes before they occur by analyzing the rate of change against historical diurnal cycles (DO naturally drops at night as photosynthesis stops and respiration continues). 

When a predicted crash is detected, the node autonomously activates the Qwiic Relay to turn on the aerators, sending a notification to the C2 Dashboard. This closed-loop control prevents fish kills without requiring 24/7 human monitoring.

---
*Copyright © 2026 NB11B. All rights reserved.*
