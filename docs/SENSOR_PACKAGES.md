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

## 5. Package 4: The Carbon Verification Array (Phase 3)
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
