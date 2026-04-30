# SAIS Firmware — Controller Layer (ESP32-S3)

This directory contains the RTOS firmware for the **Controller Layer** of the Sovereign Node, targeting the Espressif ESP32-S3 (or compatible microcontroller).

## Responsibilities

- High-frequency sensor polling via 4–20 mA, RS-485/Modbus, SDI-12, 1-Wire, and I2C/SPI interfaces
- Deterministic actuator control (gate motors, irrigation valves, nutrient pumps, lighting relays)
- Pre-programmed automation sequence execution (irrigation schedules, feeding cycles, alert thresholds)
- Watchdog timer management — the Controller Layer must never halt
- Serial/SPI bridge to the SCADA/Compute Layer for telemetry and command exchange
- OTA firmware update with rollback partition support

## Build Environment

- **Framework:** ESP-IDF (Espressif IoT Development Framework) v5.x
- **RTOS:** FreeRTOS (bundled with ESP-IDF)
- **Language:** C / C++
- **Build System:** CMake (via ESP-IDF)

## Getting Started

```bash
# Install ESP-IDF (follow official Espressif documentation)
# https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/get-started/

# Clone and enter firmware directory
cd firmware/

# Configure target
idf.py set-target esp32s3

# Build
idf.py build

# Flash
idf.py -p /dev/ttyUSB0 flash monitor
```

## Directory Structure (Planned)

```
firmware/
├── main/               # Main application entry point and task definitions
├── components/         # Reusable components (sensor drivers, actuator drivers, comms bridge)
│   ├── sensors/        # Sensor interface drivers (SDI-12, Modbus, 4-20mA, etc.)
│   ├── actuators/      # Actuator control drivers
│   ├── automation/     # Automation sequence engine
│   └── bridge/         # Serial/SPI bridge to SCADA/Compute Layer
├── partitions.csv      # Partition table (includes OTA rollback partition)
├── sdkconfig.defaults  # Default configuration
└── CMakeLists.txt
```

## Contributing

See the root [`CONTRIBUTING.md`](../CONTRIBUTING.md). For firmware contributions, please include evidence of hardware testing and document the worst-case execution time for any new control loop task.

---

*Nathanael J. Bocker, 2026 all rights reserved*
