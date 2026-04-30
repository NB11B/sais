# SAIS Hardware Specification

**Version:** 0.3.0-draft
**Status:** Active Development

---

## Overview

This document defines the hardware requirements for the Sovereign Node — the physical instantiation of the SAIS edge controller.

**Core Philosophy: Low-Cost, Accessible, and All-In-One First.**

The SAIS architecture is designed to democratize agricultural intelligence. This specification leads with the lowest-cost, most integrated hardware that can reliably run the full stack. The ideal entry point is a single board that eliminates the Controller/Compute split entirely. Industrial-grade multi-board configurations are supported and documented as upgrade paths, not barriers to entry.

---

## 1. Primary Target: Arduino UNO Q (All-In-One)

The Arduino UNO Q is the **ideal entry-level Sovereign Node**. It is a dual-architecture board that integrates a full Linux SBC (the SCADA/Compute Layer) and a real-time MCU (the Controller Layer) on a single board in the classic UNO form factor [1]. This eliminates the need for two separate boards, a UART/SPI bridge, and the associated wiring complexity.

| Parameter | Value |
|---|---|
| **Microprocessor (MPU — Linux/Compute)** | Qualcomm Dragonwing™ QRB2210: Quad-core Arm® Cortex®-A53 @ 2.0 GHz [1] |
| **Microcontroller (MCU — Real-Time)** | STMicroelectronics STM32U585, Arm® Cortex®-M33 @ 160 MHz [1] |
| **MCU Flash / SRAM** | 2 MB Flash / 786 KB SRAM [1] |
| **RAM (MPU)** | 2 GB or 4 GB LPDDR4 [1] |
| **Storage** | 16 GB or 32 GB onboard eMMC [1] |
| **OS** | Debian Linux (MPU) + Zephyr RTOS (MCU) [1] |
| **Wireless** | Wi-Fi 5 Dual-band (2.4/5 GHz) + Bluetooth 5.1 [1] |
| **Qwiic Connector** | Yes — native I2C, 3.3V, solderless sensor integration [1] |
| **UNO Headers** | Yes — full UNO shield compatibility [1] |
| **GPU** | Adreno 3D GPU (on QRB2210) [1] |
| **Estimated Cost** | ~$40 (2 GB / 16 GB) / ~$59 (4 GB / 32 GB) [2] |

### 1.1 Why the UNO Q Changes Everything for SAIS

The UNO Q directly maps to the SAIS dual-layer architecture in a single package:

| SAIS Layer | UNO Q Component | Function |
|---|---|---|
| **Controller Layer (Real-Time)** | STM32U585 MCU (Zephyr RTOS) | Sensor polling, actuator control, NGC GeoFlow kernel |
| **SCADA/Compute Layer (Intelligence)** | QRB2210 MPU (Debian Linux) | DDS middleware, MQTT broker, Auditor Container, NGC PSMSL engine |
| **Bridge** | Arduino RPC / Bridge library | Zero-latency IPC between MCU and MPU on the same board |

The onboard eMMC eliminates the SD card failure mode that disqualifies standard Raspberry Pi boards from production deployments. The Qwiic connector enables solderless sensor chain integration. The Adreno GPU provides hardware acceleration for the NGC geometric computation pipeline. **This is the most capable, most integrated, and most accessible entry point in the SAIS hardware ecosystem.**

---

## 2. Upgrade Paths (Multi-Board Configuration)

For deployments requiring physical separation of the control and compute layers (e.g., harsh environments where the compute node must be located remotely from the field controller), the following two-board configurations are supported.

### 2.1 Controller Layer Upgrade: Espressif ESP32-S3

| Parameter | Value |
|---|---|
| **Core** | Xtensa dual-core LX7, 240 MHz |
| **SRAM** | 512 KB + 8 MB PSRAM |
| **Flash** | 16 MB |
| **Connectivity** | Wi-Fi 802.11 b/g/n, Bluetooth 5 LE |
| **Estimated Cost** | ~$5 (module) / ~$15 (dev board) |

**Rationale:** For scaled production deployments where custom PCBs are being manufactured, the ESP32-S3 provides massive compute overhead for the NGC GeoFlow kernel at a fraction of the cost of any Arduino board.

### 2.2 Compute Layer Upgrade: Raspberry Pi Compute Module 4 (CM4, eMMC)

| Parameter | Value |
|---|---|
| **Core** | Quad-core ARM Cortex-A72, 1.5 GHz |
| **RAM** | 1 GB – 8 GB LPDDR4 |
| **Storage** | 8 GB – 32 GB onboard eMMC |
| **Operating Temperature** | −40°C to +85°C (extended temp variants) [3] |
| **Estimated Cost** | ~$35 – $55 |

**Rationale:** The CM4 with onboard eMMC is the production-grade Raspberry Pi. SD card variants are explicitly excluded due to storage failure rates in high-write SCADA environments.

### 2.3 Enterprise Compute: NXP i.MX 8M (Industrial SBC)

| Parameter | Value |
|---|---|
| **Core** | Quad-core ARM Cortex-A53, 1.5 GHz |
| **RAM** | 2 GB – 4 GB LPDDR4 |
| **Storage** | Industrial eMMC |
| **Security** | ARM TrustZone (hardware secure enclave) |
| **Estimated Cost** | ~$150+ |

**Rationale:** Required only when a Carbon-Plus bond issuer mandates hardware-backed TrustZone for the Auditor Container's ZKP signing pipeline.

---

## 3. Communication Hardware

### 3.1 Local Mesh (Short Range)
Wi-Fi 802.11 b/g/n (2.4 GHz) via the UNO Q's onboard WCBN3536A wireless module. No additional hardware required.

### 3.2 Long-Range Mesh (LoRa)

| Parameter | Value |
|---|---|
| **Primary Module** | SX1278 LoRa Ra-01 (433 MHz / 868 MHz / 915 MHz) [4] |
| **Interface** | SPI |
| **Range** | ≥ 2 km line-of-sight |
| **Estimated Cost** | ~$4 – $6 |

---

## 4. Sensor Interface Standards

The SAIS architecture prioritizes low-cost, accessible sensor standards:

| Interface | Primary Use Case | Accessibility |
|---|---|---|
| **I2C (Qwiic/STEMMA QT)** | Environmental sensors (BME280), IMUs | **Highest:** Solderless, plug-and-play via UNO Q Qwiic port |
| **Analog (ADC)** | Capacitive soil moisture sensors [5] | **High:** 3-wire, ~$2 per sensor |
| **1-Wire** | Temperature sensors (DS18B20) | **High:** Daisy-chainable, ~$1 per sensor |
| **RS-485 / Modbus RTU** | Multi-drop industrial sensor networks | **Medium:** Requires RS-485 transceiver module |
| **4–20 mA** | Industrial flow meters, pressure sensors | **Low:** Requires ADC bridge, expensive sensors |

---

## 5. Power System

### 5.1 Entry-Level: DIY 12V Solar Kit

| Component | Specification | Estimated Cost |
|---|---|---|
| Solar Panel | 50W – 100W 12V Monocrystalline | ~$40 – $60 |
| Charge Controller | 10A – 20A PWM Solar Charge Controller [6] | ~$15 |
| Battery | 12V 12Ah – 20Ah LiFePO4 [7] | ~$40 – $60 |
| **Total** | | **~$95 – $135** |

LiFePO4 is chosen over Lead-Acid for its vastly superior cycle life (2000+ cycles) and thermal stability in field environments.

---

## 6. Cost Summary

### Entry-Level Node (Single-Board, UNO Q)

| Component | Selection | Estimated Cost |
|---|---|---|
| **Controller + Compute** | Arduino UNO Q (2 GB / 16 GB) | $40 |
| **Comms** | SX1278 LoRa Module | $5 |
| **Sensors** | 3× Capacitive Soil + 1× BME280 (Qwiic) | $10 |
| **Power** | 50W Panel, PWM Controller, 12Ah LiFePO4 | $95 |
| **Enclosure** | Generic IP65 ABS Junction Box | $15 |
| **Total** | | **~$165** |

A fully sovereign, cryptographically verifiable, AI-capable edge node for under **$165** — on a single board, with no custom PCBs, no soldering required for sensors, and no SD card failure risk.

---

## 7. References

[1] Arduino, "UNO Q | Arduino Documentation," *docs.arduino.cc*. [Online]. Available: https://docs.arduino.cc/hardware/uno-q
[2] Arduino, "Arduino UNO Q 4GB," *store-usa.arduino.cc*. [Online]. Available: https://store-usa.arduino.cc/products/uno-q-4gb
[3] Raspberry Pi, "New extended temperature range for Compute Module 4," *raspberrypi.com*. [Online]. Available: https://www.raspberrypi.com/news/new-extended-temperature-range-for-compute-module-4/
[4] Makerfabs, "SX1278 LoRa Ra-01 433MHz Breakout," *makerfabs.com*. [Online]. Available: https://www.makerfabs.com/sx1278-lora-ra-01-433mhz-breakou.html
[5] Amazon, "Capacitive Soil Moisture Sensor," *amazon.com*. [Online]. Available: https://www.amazon.com/capacitive-soil-moisture-sensor/s?k=capacitive+soil+moisture+sensor
[6] eBay, "PWM Solar Charge Controller 20A 12V," *ebay.com*. [Online]. Available: https://www.ebay.com/shop/lifepo4-solar-charge-controller
[7] ExpertPower, "12V 20Ah LiFePO4 Battery," *expertpower.us*. [Online]. Available: https://www.expertpower.us/collections/solar-kit-collection-lifepo4

---

*Nathanael J. Bocker, 2026 all rights reserved*
