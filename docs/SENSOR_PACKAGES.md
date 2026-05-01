# SAIS Sensor Package Specification

This document defines the standardized sensor packages for the Sovereign Ag-Infrastructure Stack (SAIS). 

The packages are designed around the **Qwiic / STEMMA QT (I2C)** ecosystem to ensure plug-and-play compatibility with the Arduino UNO Q without requiring soldering or custom PCB design for initial deployments.

## 1. The Core Philosophy

A sensor package must serve two masters simultaneously:
1. **The Farmer:** It must solve an immediate, daily operational pain point (e.g., "Is my pump failing?", "Is my soil too dry?").
2. **The Intelligence Layer:** It must provide the high-fidelity, continuous data streams required to build the baseline models for anomaly detection and, ultimately, the Carbon-Plus bond verification.

---

## 2. Package 1: The Soil & Microclimate Baseline
**Target:** Row crops, orchards, vineyards.
**Pain Point Solved:** Over/under-watering, frost damage prediction.
**Intelligence Value:** Baseline soil health metrics, evapotranspiration modeling.

This is the foundational package for any SAIS deployment. It establishes the ground-truth environmental conditions.

| Sensor | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **SparkFun Qwiic Soil Moisture Sensor** | I2C (Qwiic) | Capacitive soil moisture measurement (avoids corrosion of resistive sensors). | $7.50 |
| **BME280 Environmental Sensor** | I2C (Qwiic) | High-precision temperature, humidity, and barometric pressure. | $15.00 |
| **VEML6075 UV/Light Sensor** | I2C (Qwiic) | UVA, UVB, and visible light index for canopy penetration analysis. | $10.00 |

*Deployment Note:* These three sensors can be daisy-chained on a single Qwiic cable, requiring only one port on the UNO Q.

---

## 3. Package 2: The Structural Health & Machinery Monitor
**Target:** Irrigation pumps, grain silos, processing equipment.
**Pain Point Solved:** Unexpected equipment failure, catastrophic downtime.
**Intelligence Value:** High-frequency vibration data for the PSMSL Adaptive Engine to detect resonance shifts (bearing wear, structural fatigue).

| Sensor | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **ISM330DHCX 6-DoF IMU** | I2C (Qwiic) | Industrial-grade accelerometer/gyroscope for high-frequency vibration analysis. | $20.00 |
| **Contact Microphone (Piezo)** | Analog / ADC | Acoustic anomaly detection (hissing leaks, grinding bearings). | $5.00 |
| **MLX90614 IR Thermometer** | I2C (Qwiic) | Non-contact temperature measurement of motor casings or bearings. | $18.00 |

*Deployment Note:* The IMU data is fed directly into the `sais_adaptive_mode_structural_health` firmware component to generate the Leibniz-Bocker curvature ($\Omega$) metric.

---

## 4. Package 3: The Livestock & Enclosure Monitor
**Target:** Poultry houses, dairy barns, swine facilities.
**Pain Point Solved:** Heat stress, poor air quality, disease outbreaks.
**Intelligence Value:** Environmental stress correlation with herd health.

| Sensor | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **SGP40 Air Quality Sensor** | I2C (Qwiic) | VOC (Volatile Organic Compounds) index for air staleness. | $15.00 |
| **SCD41 CO2 Sensor** | I2C (Qwiic) | True photoacoustic CO2 measurement for ventilation control. | $45.00 |
| **BME280 Environmental Sensor** | I2C (Qwiic) | Temperature and humidity for calculating the Heat/Humidity Index (THI). | $15.00 |

---

## 5. Package 5: The Smart Perimeter & Fence Controller
**Target:** Open-range grazing, property boundaries, predator exclusion zones.
**Pain Point Solved:** Wasted electricity on continuous fence energizing, undetected fence breaches, battery drain on solar setups.
**Intelligence Value:** Perimeter breach mapping, wildlife/predator movement patterns, livestock grazing boundary pressure.

This package converts a "dumb" continuous-pulse electric fence into a reactive, energy-efficient perimeter. It only energizes the fence when a physical presence is detected, saving massive amounts of power on solar-backed systems and extending battery life exponentially.

| Sensor / Actuator | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **RCWL-0516 Microwave Radar Sensor** | Digital I/O | Doppler radar presence detection. Works through plastic enclosures and ignores temperature changes (unlike PIR), making it highly reliable outdoors. | $2.00 |
| **SparkFun Qwiic Single Relay** | I2C (Qwiic) | Switches the 12V power supply to the fence energizer on/off based on radar triggers. | $10.00 |
| **Voltage Divider / ADC** | Analog | Monitors the high-voltage pulse return to confirm the fence is actually shocking (detects grounded/broken wires). | $3.00 |

*Deployment Note:* The microwave radar detects motion up to 7 meters away. When triggered, the UNO Q commands the Qwiic Relay to activate the fence energizer for a set duration (e.g., 60 seconds). If the voltage return sensor detects a drop (indicating a grounded wire or a breach), it immediately sends an alert to the C2 Dashboard.

---

## 6. Package 6: The Livestock Water Tank Monitor
**Target:** Open-range cattle, sheep, and horse operations with remote water tanks, troughs, or stock ponds.
**Pain Point Solved:** Dry tanks discovered only after livestock have been without water for hours; unnecessary daily driving to check tank levels.
**Intelligence Value:** Water consumption rate modeling, livestock herd activity inference, pump cycle health.

This is one of the highest-value, lowest-cost packages in the SAIS stack. A dry water tank on a hot day is a livestock welfare emergency and a direct financial loss. Yet checking tank levels is one of the most time-consuming "windshield time" tasks on any ranch. A single ultrasonic sensor mounted to the top of a tank lid solves this completely.

| Sensor / Actuator | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **SparkFun Qwiic Ultrasonic Distance Sensor (HC-SR04 / SparkFun variant)** | I2C (Qwiic) | Measures the air gap between the sensor and the water surface. Tank level is derived from the known tank geometry. | $10.00 |
| **BME280 Environmental Sensor** | I2C (Qwiic) | Temperature and humidity correction for ultrasonic speed-of-sound compensation (ensures accuracy across seasons). | $15.00 |
| **SparkFun Qwiic Single Relay** *(optional)* | I2C (Qwiic) | Triggers a float-valve solenoid or pump to auto-refill the tank when level drops below a threshold. | $10.00 |

*Deployment Note:* The sensor mounts inside a sealed PVC cap on the top of the tank — completely protected from weather and livestock. The UNO Q calculates the fill percentage from the measured air gap and the known tank diameter. Alerts are sent to the C2 Dashboard at configurable thresholds (e.g., 30% and 10% remaining). With the optional relay, the system can trigger an automatic refill pump, turning a passive monitor into a fully autonomous water management system.

**The Dual-Sensor Insight:** The same RCWL-0516 microwave radar from Package 5 can be co-deployed on the tank node to detect livestock presence at the trough. By correlating radar presence events with water level drop rate, the Intelligence Layer can estimate herd size and drinking frequency — a proxy for herd health and heat stress that requires no additional hardware.

---

## 7. Package 4: The Carbon Verification Array (Phase 3)
**Target:** Regenerative agriculture plots seeking Carbon-Plus bond issuance.
**Pain Point Solved:** $50,000 manual MRV auditor fees.
**Intelligence Value:** The cryptographic proof of soil carbon sequestration.

This package is more expensive and is deployed selectively to generate the data required by the Auditor Container.

| Sensor | Interface | Purpose | Estimated Cost |
|---|---|---|---|
| **AS7265x Triad Spectroscopy Sensor** | I2C (Qwiic) | 18-channel multispectral analysis (UV to NIR) for soil organic carbon estimation. | $65.00 |
| **NDIR Methane (CH4) Sensor** | UART / I2C | Enteric fermentation monitoring (for livestock grazing plots). | $80.00 |
| **High-Precision Soil NPK Sensor** | RS-485 (via Modbus to I2C bridge) | Nitrogen, Phosphorus, Potassium levels. | $120.00 |

*Deployment Note:* The data from this array is processed by the NGC GeoFlow kernel on the UNO Q's Adreno GPU, and the resulting geometric proof is cryptographically signed by the Auditor Container.
