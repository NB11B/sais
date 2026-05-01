# SAIS Extension: Equine Performance

## Overview
High-value equine athletes require continuous monitoring of their physiological state during training and recovery. The SAIS architecture extends to equine performance by deploying wearable biometric sensors and integrating them with the Adaptive Engine's PSMSL gait analysis, driven by real-time heart rate and thermal imaging.

## Hardware Integration

| Component | Interface | Purpose |
|---|---|---|
| **Polar H10 Heart Rate Sensor** | BLE | Measures heart rate and heart rate variability (HRV) during exercise and recovery. |
| **ISM330DHCX Industrial IMU** | I2C | Mounted on the saddle or girth to capture the 6-axis motion of the horse's stride. |
| **MLX90640 Thermal Camera Array** | I2C | Handheld or fixed-mount thermal imaging of the lower limbs and back to detect inflammation. |
| **UNO Q Adreno 702 GPU** | Internal | Runs the PSMSL gait analysis and thermal inference models locally. |

## Software & Intelligence Layer
The Intelligence Layer ingests the continuous heart rate, HRV, and IMU data streams. The primary inference model is the **Adaptive Engine (PSMSL)**, which analyzes the high-frequency accelerometer data to detect subtle asymmetries in the horse's gait (lameness) before they are visible to the rider or trainer.

Simultaneously, the thermal camera scans the horse's legs post-workout. The edge AI model identifies localized hot spots (e.g., a strained tendon or suspensory ligament) and flags them for veterinary attention. The heart rate data tracks the horse's fitness progression and recovery rate, ensuring the training load is optimized and overtraining is avoided.

---
*Copyright © 2026 NB11B. All rights reserved.*
