# GPS Perimeter Environment Node

The GPS Perimeter Environment Node is the first simple SAIS hardware module.

It reports physical location, temperature, humidity, and node health into the SAIS telemetry path. It is intended for fence lines, field edges, gates, water assets, temporary work zones, equipment yards, and other perimeter or boundary locations.

This node observes and reports. It does not actuate relays, pumps, valves, gates, or power-routing hardware.

## Purpose

The node answers basic field questions:

```text
Where is this node?
Is it still alive?
Does it have a valid GPS fix?
What are the local temperature and humidity?
Is the environment sensor healthy?
When was the last valid update?
```

## What This Module Teaches

This module teaches the basic SAIS hardware pattern:

```text
sense
validate
package
publish
observe in dashboard
```

It also teaches three common hardware domains:

```text
Location      -> UART GPS module
Environment   -> I2C temperature and humidity sensor
Node health   -> uptime, signal quality, optional battery voltage, fault state
```

## Recommended Prototype Hardware

| Function | Recommended Part | Notes |
|---|---|---|
| Microcontroller | ESP32 or ESP32-S3 | Wi-Fi capable, low-cost, easy field prototype |
| GPS | u-blox NEO-M8N or similar | NEO-6M can work for low-cost bench testing |
| Temperature and humidity | SHT31 or BME280 | Prefer I2C sensors over DHT-style sensors for reliability |
| Power | USB for bench, battery for field | Add battery telemetry in later revision |
| Optional | Status LED | Useful during field bring-up |
| Optional | External GPS antenna | Useful for enclosures or poor sky view |

## Basic Data Flow

```text
GPS UART stream
+ environment sensor reading
+ node health
-> validation
-> telemetry packet
-> SAIS dashboard path
```

## What This Module Does

- Reads GPS position and fix quality.
- Reads temperature and humidity.
- Tracks node uptime and basic health.
- Publishes visible telemetry.
- Publishes visible fault states when a sensor fails.

## What This Module Does Not Do

- It does not control actuators.
- It does not make agronomic decisions.
- It does not replace the FarmGraph or dashboard logic.
- It does not require a new repository.
- It does not require a cloud service.

## Files In This Module

```text
README.md             Plain-language module explanation
module_contract.md    Inputs, outputs, dependencies, failure modes, telemetry
wiring.md             Suggested wiring and pin map
temetry.md            Telemetry field mapping and example payloads
test_plan.md          Repeatable test procedure
fault_handling.md     Visible fault behavior
firmware_notes.md     Firmware loop and implementation notes
```

## First Milestone

Build one node that publishes usable telemetry every 5 seconds.

Success criteria:

```text
node boots reliably
GPS module is detected
temperature and humidity sensor is detected
telemetry reaches the SAIS dashboard path
node ID is visible
GPS fix status is visible
temperature and humidity are visible
sensor faults are visible
```

## Integration Status

Status: specification module, ready for firmware implementation.

Target path:

```text
hardware/examples/gps_perimeter_node_minimal/
```

Target live API path when using current observation ingestion:

```text
POST /api/observations
schema: sais.observation.v1
```
