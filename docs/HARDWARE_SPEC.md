# SAIS Hardware Specification

**Version:** 0.1.0-draft
**Status:** Active Development

---

## Overview

This document defines the hardware requirements for the Sovereign Node — the physical instantiation of the SAIS edge controller. The specification is designed to be hardware-agnostic at the component level: specific part numbers are provided as reference implementations, but the architecture supports equivalent components that meet the stated requirements.

---

## Controller Layer (Real-Time)

### Primary Reference: Espressif ESP32-S3

| Parameter | Requirement | ESP32-S3 Value |
|---|---|---|
| **Architecture** | 32-bit, dual-core capable | Xtensa LX7, dual-core |
| **Clock Speed** | ≥ 240 MHz | 240 MHz |
| **RTOS Support** | FreeRTOS or equivalent | FreeRTOS (native) |
| **Flash** | ≥ 8 MB | 8–16 MB (variant dependent) |
| **SRAM** | ≥ 512 KB | 512 KB |
| **GPIO** | ≥ 20 pins | 45 pins |
| **Communication** | UART, SPI, I2C, CAN | All supported |
| **Power Consumption** | < 500 mW active | ~240 mW @ 240 MHz |
| **Operating Temperature** | −40°C to +85°C | −40°C to +85°C |
| **Wireless** | Optional (for local sensor mesh) | Wi-Fi 802.11 b/g/n, BLE 5.0 |

### Firmware Requirements

- FreeRTOS with configurable task priorities
- Watchdog timer with automatic reset (the Controller Layer must never halt)
- Deterministic task scheduling with documented worst-case execution times for all control loops
- Rollback partition for OTA firmware updates

### Alternative Reference: Arduino UNO R4 WiFi (Qwiic)

| Parameter | Requirement | UNO R4 WiFi Value |
|---|---|---|
| **Architecture** | 32-bit | Renesas RA4M1 (Arm® Cortex®-M4) [1] |
| **Clock Speed** | ≥ 48 MHz | 48 MHz [1] |
| **Flash** | ≥ 256 KB | 256 KB [1] |
| **SRAM** | ≥ 32 KB | 32 KB [1] |
| **GPIO** | ≥ 14 pins | 14 Digital, 6 Analog [1] |
| **Communication** | I2C, UART, SPI | Qwiic I2C connector (3.3V) [2] |
| **Wireless** | Optional | On-board ESP32-S3 (Wi-Fi/BLE) [1] |

**Rationale:** The UNO R4 WiFi is an excellent rapid-prototyping alternative. The integrated Qwiic connector allows for instant, solderless integration of I2C sensor chains, which aligns perfectly with the "all-in-one" prototyping philosophy. While its 32 KB SRAM is constrained compared to the ESP32-S3, it is sufficient to run a highly optimized, low-node-count version of the NGC GeoFlow kernel ($O(k)$ memory footprint). The built-in ESP32-S3 handles the network stack, leaving the RA4M1 entirely dedicated to deterministic control and geometric computation.

---

## SCADA/Compute Layer (Intelligence)

### Primary Reference: NXP i.MX 8M Series

| Parameter | Requirement | i.MX 8M Value |
|---|---|---|
| **Architecture** | ARM Cortex-A, 64-bit | Cortex-A53, quad-core |
| **Clock Speed** | ≥ 1.0 GHz | 1.5 GHz |
| **RAM** | ≥ 2 GB LPDDR4 | 2–4 GB (variant dependent) |
| **Storage** | Industrial eMMC, ≥ 32 GB | Up to 128 GB eMMC |
| **Secure Enclave** | ARM TrustZone | TrustZone (native) |
| **Operating Temperature** | −40°C to +85°C (industrial) | −40°C to +85°C |
| **Power Consumption** | < 8 W under full load | 3–8 W |
| **Connectivity** | Gigabit Ethernet, USB | GbE, USB 3.0, USB 2.0 |
| **Wireless** | Optional | Via M.2 or USB module |

**Critical Requirement:** Consumer-grade SBCs (Raspberry Pi 4, Orange Pi, etc.) using SD card storage are explicitly not supported for production deployments, as SD cards fail under continuous write cycles [5].

### Alternative Reference: Raspberry Pi Compute Module 4 (CM4) / Pi 5

| Parameter | Requirement | CM4 / Pi 5 Value |
|---|---|---|
| **Architecture** | ARM Cortex-A, 64-bit | Cortex-A72 (CM4) [3] / Cortex-A76 (Pi 5) [4] |
| **Clock Speed** | ≥ 1.5 GHz | 1.5 GHz (CM4) / 2.4 GHz (Pi 5) |
| **RAM** | ≥ 1 GB LPDDR4 | 1–8 GB |
| **Storage** | Industrial eMMC or NVMe | 8–32 GB onboard eMMC (CM4) [3] / NVMe via PCIe (Pi 5) [4] |
| **Operating Temperature** | −40°C to +85°C (industrial) | −40°C to +85°C (CM4 extended temp variants) [6] |

**Rationale:** The Raspberry Pi ecosystem offers unmatched community support and rapid development velocity. For SAIS deployments, the **Compute Module 4 (CM4) with onboard eMMC** is the only acceptable Pi variant for production, as standard SD-card-based Pis suffer from unacceptable storage failure rates in high-write SCADA environments [5]. Recent CM4 variants also support extended industrial temperature ranges (-40°C to +85°C) [6]. The Pi 5 offers massive compute overhead for the NGC PSMSL engine, but requires active cooling or massive passive heatsinks, making it harder to seal in an IP67 enclosure compared to the CM4 or i.MX 8M.

### Storage Requirements

| Parameter | Requirement |
|---|---|
| **Type** | Industrial-grade eMMC (not SD card) |
| **Capacity** | ≥ 32 GB |
| **Write Endurance** | ≥ 3,000 P/E cycles (industrial grade) |
| **Operating Temperature** | −40°C to +85°C |
| **Interface** | eMMC 5.1 or later |

---

## Physical Enclosure

| Parameter | Requirement |
|---|---|
| **IP Rating** | IP67 minimum (dust-tight, waterproof to 1 m for 30 min) |
| **Material** | Die-cast aluminum alloy |
| **Thermal Management** | Fanless; chassis acts as passive heat sink |
| **Operating Temperature** | −30°C to +70°C (ambient) |
| **Mounting Options** | DIN rail, fence post (35 mm tube), surface mount |
| **Dimensions** | Target: ≤ 200 × 150 × 80 mm |
| **Weight** | Target: ≤ 2 kg (without mounting hardware) |
| **Connectors** | M12 circular (IP67-rated) for all external connections |
| **Cable Entry** | M20 cable glands with IP67 rating |

---

## Power System

### Solar Input

| Parameter | Requirement |
|---|---|
| **Input Voltage** | 12V or 24V nominal |
| **Charge Controller** | MPPT (Maximum Power Point Tracking) |
| **Panel Sizing** | Minimum 30W for 12V system; 60W recommended |

### Battery

| Parameter | Requirement |
|---|---|
| **Chemistry** | LiFePO4 (preferred for cycle life and thermal stability) |
| **Voltage** | 12V or 24V nominal |
| **Capacity** | Minimum 50 Ah (12V) for 3-day autonomy at full load |
| **Operating Temperature** | −20°C to +60°C |
| **BMS** | Integrated Battery Management System required |

### Power Budget

| Component | Typical Power Draw |
|---|---|
| ESP32-S3 (Controller Layer) | 0.24 W |
| i.MX 8M (SCADA/Compute Layer) | 5.0 W |
| LoRa Radio Module | 0.5 W (TX), 0.05 W (RX) |
| Sensors (typical array) | 1.0 W |
| Actuator standby | 0.5 W |
| **Total (typical)** | **~7.3 W** |
| **Total (peak)** | **~15 W** |

---

## Communication Hardware

### Local Mesh (Short Range)

| Parameter | Requirement |
|---|---|
| **Protocol** | Wi-Fi 802.11 b/g/n (2.4 GHz) |
| **Range** | ≥ 100 m line-of-sight |
| **Antenna** | External, weatherproof, N-type or SMA connector |

### Long-Range Mesh

| Parameter | Requirement |
|---|---|
| **Protocol** | LoRa (Long Range) |
| **Frequency** | 868 MHz (EU) / 915 MHz (US) |
| **Range** | ≥ 2 km line-of-sight; ≥ 500 m in agricultural terrain |
| **Module** | SX1276 or equivalent |
| **Antenna** | External, weatherproof, fiberglass omni |

---

## Sensor Interface Standards

The Controller Layer supports the following sensor interface standards:

| Interface | Use Case |
|---|---|
| **4–20 mA current loop** | Industrial soil sensors, flow meters |
| **0–10V analog** | Pressure sensors, level sensors |
| **RS-485 / Modbus RTU** | Multi-drop sensor networks |
| **SDI-12** | Environmental sensors (standard in agriculture) |
| **1-Wire** | Temperature sensors (DS18B20 and compatible) |
| **I2C / SPI** | On-board sensors, display modules |
| **Pulse counter** | Flow meters, rain gauges |

---

## Bill of Materials (Reference Implementation)

> **Note:** This BOM represents the reference implementation. Equivalent components may be substituted provided they meet the specifications above. Full KiCad schematics are available in the `hardware/` directory.

| Component | Reference Part | Quantity | Notes |
|---|---|---|---|
| Microcontroller | ESP32-S3-WROOM-1 | 1 | Controller Layer |
| Industrial SBC | Compulab SBC-iMX8 or equivalent | 1 | SCADA/Compute Layer |
| LoRa Module | Semtech SX1276 breakout | 1 | Long-range mesh |
| MPPT Charge Controller | Victron SmartSolar MPPT 75/15 | 1 | Power management |
| LiFePO4 Battery | 12V 100Ah LiFePO4 | 1 | 3-day autonomy |
| Solar Panel | 100W 12V monocrystalline | 1 | Primary power source |
| Enclosure | Custom IP67 die-cast aluminum | 1 | See mechanical drawings |
| M12 Connectors | Binder Series 713 | 6 | External I/O |
| DIN Rail | 35 mm aluminum, 200 mm | 1 | Internal mounting |

---

## References

[1] Arduino, "Arduino® UNO R4 WiFi," *docs.arduino.cc*. [Online]. Available: https://docs.arduino.cc/hardware/uno-r4-wifi
[2] SparkFun, "SparkFun Arduino UNO R4 WiFi Qwiic Kit Hookup Guide," *learn.sparkfun.com*. [Online]. Available: https://learn.sparkfun.com/tutorials/sparkfun-arduino-uno-r4-wifi-qwiic-kit-hookup-guide/all
[3] Raspberry Pi, "Raspberry Pi Compute Module 4 Product Brief," *pip.raspberrypi.com*. [Online]. Available: https://pip.raspberrypi.com/documents/RP-008169-DS-cm4-product-brief.pdf
[4] Raspberry Pi, "Raspberry Pi 5 Product Brief," *pip.raspberrypi.com*. [Online]. Available: https://pip.raspberrypi.com/documents/RP-008348-DS-raspberry-pi-5-product-brief.pdf
[5] Industrial Monitor Direct, "Raspberry Pi Edge Deployment Failures: Root Causes and Solutions," *industrialmonitordirect.com*. [Online]. Available: https://industrialmonitordirect.com/blogs/knowledgebase/raspberry-pi-edge-deployment-failures-root-causes-and-solutions
[6] Raspberry Pi, "New extended temperature range for Compute Module 4," *raspberrypi.com*. [Online]. Available: https://www.raspberrypi.com/news/new-extended-temperature-range-for-compute-module-4/

---

*Nathanael J. Bocker, 2026 all rights reserved*
