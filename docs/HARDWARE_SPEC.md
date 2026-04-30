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

**Critical Requirement:** Consumer-grade SBCs (Raspberry Pi, Orange Pi, etc.) are explicitly not supported for production deployments. They use SD card storage, which fails under continuous write cycles, and are not rated for industrial temperature ranges or continuous unattended operation.

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

*Nathanael J. Bocker, 2026 all rights reserved*
