# SAIS Hardware Specification

**Version:** 0.2.0-draft
**Status:** Active Development

---

## Overview

This document defines the hardware requirements for the Sovereign Node — the physical instantiation of the SAIS edge controller. 

**Core Philosophy: Low-Cost and Accessible First.**
The SAIS architecture is designed to democratize agricultural intelligence. Therefore, this specification leads with the lowest-cost, most accessible hardware that can reliably run the stack. Industrial-grade components are supported and documented, but they are positioned as optional upgrades for scaled deployments, not as barriers to entry.

---

## 1. Controller Layer (Real-Time)

The Controller Layer requires a deterministic RTOS environment to manage physical I/O without interruption.

### 1.1 Primary Target: Arduino UNO R4 WiFi (Qwiic)
- **Core:** Renesas RA4M1 (Arm® Cortex®-M4) 32-bit microprocessor, 48 MHz [1]
- **Memory:** 32 KB SRAM [1]
- **Storage:** 256 KB Flash [1]
- **Connectivity:** On-board ESP32-S3 module for Wi-Fi and Bluetooth [1]
- **I/O:** 14 Digital I/O, 6 Analog, DAC, Qwiic I2C connector (3.3V) [1] [2]
- **Estimated Cost:** ~$28
- **Rationale:** The UNO R4 WiFi is the ultimate accessible entry point. The integrated Qwiic connector allows for instant, solderless integration of I2C sensor chains (soil moisture, temp, etc.), eliminating the need for custom PCBs during prototyping. The 32 KB SRAM is sufficient to run a highly optimized, low-node-count version of the NGC GeoFlow kernel ($O(k)$ memory footprint). The built-in ESP32-S3 handles the network stack, leaving the RA4M1 entirely dedicated to deterministic control.

### 1.2 Upgrade Target: Espressif ESP32-S3
- **Core:** Xtensa dual-core 32-bit LX7 microprocessor, up to 240 MHz
- **Memory:** 512 KB SRAM, 8 MB PSRAM
- **Storage:** 16 MB SPI Flash
- **Estimated Cost:** ~$5 (module only) / ~$15 (dev board)
- **Rationale:** For scaled deployments where custom PCBs are being manufactured, the ESP32-S3 provides massive compute overhead for the NGC GeoFlow kernel at a fraction of the cost of the Arduino. Its dual-core architecture allows one core to handle FreeRTOS control loops while the second core is dedicated to geometric computation.

---

## 2. SCADA/Compute Layer (Intelligence)

The SCADA/Compute Layer runs the containerized intelligence stack, including the DDS middleware, the Auditor Container, and the full NGC PSMSL engine.

### 2.1 Primary Target: Raspberry Pi Zero 2 W
- **Core:** Quad-core 64-bit ARM Cortex-A53, 1 GHz [3]
- **Memory:** 512 MB SDRAM [3]
- **Storage:** MicroSD (High-Endurance required)
- **Estimated Cost:** ~$15
- **Rationale:** The Pi Zero 2 W is the cheapest viable Linux computer capable of running a lightweight container stack (Docker/k3s). It provides enough compute to run the local MQTT broker, DDS middleware, and a constrained NGC PSMSL engine. **Critical Warning:** To prevent the most common failure mode of edge devices (storage corruption), a High-Endurance or Industrial-grade MicroSD card (e.g., SanDisk High Endurance) is absolutely mandatory.

### 2.2 Upgrade Target: Raspberry Pi Compute Module 4 (CM4)
- **Core:** Quad-core ARM Cortex-A72, 1.5 GHz [4]
- **Memory:** 1 GB to 8 GB LPDDR4
- **Storage:** 8 GB to 32 GB onboard eMMC [4]
- **Estimated Cost:** ~$35 - $55 (depending on RAM/eMMC)
- **Rationale:** For production deployments, the CM4 with onboard eMMC replaces the fragile SD card interface entirely. Recent CM4 variants also support extended industrial temperature ranges (-40°C to +85°C) [5], making it a true industrial-grade solution at a maker-friendly price point.

### 2.3 Enterprise Target: NXP i.MX 8M (Industrial SBC)
- **Core:** Quad-core ARM Cortex-A53, up to 1.5 GHz
- **Memory:** 2 GB to 4 GB LPDDR4
- **Storage:** Industrial eMMC
- **Security:** ARM TrustZone (Secure Enclave)
- **Estimated Cost:** ~$150+
- **Rationale:** The i.MX 8M is required only when hardware-backed cryptographic security (TrustZone) is mandated by the Carbon-Plus bond issuer for the Auditor Container's ZKP signing pipeline.

---

## 3. Communication Hardware

### 3.1 Local Mesh (Short Range)
- **Primary:** Wi-Fi 802.11 b/g/n (2.4 GHz) via the Controller Layer's ESP32-S3.
- **Cost:** Included in Controller Layer.

### 3.2 Long-Range Mesh (LoRa)
- **Primary Target:** SX1278 LoRa Ra-01 Breakout Module (433MHz / 868MHz / 915MHz) [6]
- **Interface:** SPI
- **Estimated Cost:** ~$4 - $6
- **Rationale:** The SX1278 is the cheapest, most ubiquitous LoRa transceiver available. It provides multi-kilometer range for mesh communication without requiring cellular subscriptions or expensive gateways.

---

## 4. Sensor Interface Standards

The SAIS architecture prioritizes low-cost, accessible sensor standards:

| Interface | Primary Use Case | Accessibility |
|---|---|---|
| **I2C (Qwiic/STEMMA)** | Environmental sensors (BME280), IMUs | **Highest:** Solderless, plug-and-play |
| **Analog (ADC)** | Low-cost capacitive soil moisture sensors [7] | **High:** 3-wire connection, ~$2 per sensor |
| **1-Wire** | Temperature sensors (DS18B20) | **High:** Daisy-chainable, ~$1 per sensor |
| **4–20 mA** | Industrial flow meters, pressure sensors | **Low:** Requires ADC bridge, expensive sensors |

---

## 5. Power System

The power system must support continuous off-grid operation.

### 5.1 Primary Target: DIY 12V Solar Kit
- **Solar Panel:** 50W - 100W 12V Monocrystalline (~$40 - $60)
- **Charge Controller:** 10A - 20A PWM Solar Charge Controller (~$15) [8]
- **Battery:** 12V 12Ah - 20Ah LiFePO4 Battery (~$40 - $60) [9]
- **Estimated Total Cost:** ~$95 - $135
- **Rationale:** A basic PWM controller and a small LiFePO4 battery provide a highly reliable, low-cost power foundation. LiFePO4 is chosen over Lead-Acid for its vastly superior cycle life (2000+ cycles) and thermal stability in field environments.

---

## 6. Cost Summary (Entry-Level Node)

| Component | Selection | Estimated Cost |
|---|---|---|
| **Controller** | Arduino UNO R4 WiFi | $28 |
| **Compute** | Raspberry Pi Zero 2 W | $15 |
| **Storage** | 32GB High-Endurance MicroSD | $12 |
| **Comms** | SX1278 LoRa Module | $5 |
| **Sensors** | 3x Capacitive Soil, 1x BME280 | $10 |
| **Power** | 50W Panel, PWM Controller, 12Ah LiFePO4 | $95 |
| **Enclosure** | Generic IP65 ABS Junction Box | $15 |
| **Total** | | **~$180** |

This entry-level BOM proves that a fully sovereign, cryptographically verifiable, AI-capable edge node can be deployed for under $200.

---

## 7. References

[1] Arduino, "Arduino® UNO R4 WiFi," *docs.arduino.cc*. [Online]. Available: https://docs.arduino.cc/hardware/uno-r4-wifi
[2] SparkFun, "SparkFun Arduino UNO R4 WiFi Qwiic Kit Hookup Guide," *learn.sparkfun.com*. [Online]. Available: https://learn.sparkfun.com/tutorials/sparkfun-arduino-uno-r4-wifi-qwiic-kit-hookup-guide/all
[3] Raspberry Pi, "Raspberry Pi Zero 2 W," *raspberrypi.com*. [Online]. Available: https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
[4] Raspberry Pi, "Raspberry Pi Compute Module 4 Product Brief," *pip.raspberrypi.com*. [Online]. Available: https://pip.raspberrypi.com/documents/RP-008169-DS-cm4-product-brief.pdf
[5] Raspberry Pi, "New extended temperature range for Compute Module 4," *raspberrypi.com*. [Online]. Available: https://www.raspberrypi.com/news/new-extended-temperature-range-for-compute-module-4/
[6] Makerfabs, "SX1278 LoRa Ra-01 433MHz Breakout," *makerfabs.com*. [Online]. Available: https://www.makerfabs.com/sx1278-lora-ra-01-433mhz-breakou.html
[7] Amazon, "Capacitive Soil Moisture Sensor," *amazon.com*. [Online]. Available: https://www.amazon.com/capacitive-soil-moisture-sensor/s?k=capacitive+soil+moisture+sensor
[8] eBay, "PWM Solar Charge Controller 20A 12V," *ebay.com*. [Online]. Available: https://www.ebay.com/shop/lifepo4-solar-charge-controller
[9] ExpertPower, "12V 20Ah LiFePO4 Battery," *expertpower.us*. [Online]. Available: https://www.expertpower.us/collections/solar-kit-collection-lifepo4

---

*Nathanael J. Bocker, 2026 all rights reserved*
