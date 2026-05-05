# GPS Perimeter Node Minimal Example

This example folder is the target location for the first simple firmware implementation of the GPS Perimeter Environment Node.

The first implementation should prove one thing:

```text
one ESP32-class node can publish GPS status, temperature, humidity, and node health into SAIS consistently
```

## Prototype Goal

Build a bench node that:

```text
boots cleanly
reads GPS UART data
reads an I2C temperature and humidity sensor
builds SAIS observation payloads
posts to POST /api/observations
logs faults visibly
```

## Suggested Hardware

```text
ESP32 or ESP32-S3 development board
NEO-M8N or NEO-6M GPS module
SHT31 or BME280 temperature and humidity sensor
USB power
SAIS dashboard reachable over Wi-Fi
```

## Suggested File Plan

Future firmware files can be added here:

```text
gps_perimeter_node_minimal.ino
config.example.json
README.md
```

## Firmware Loop

The first firmware should follow this pattern:

```text
initialize serial
load or define config
connect Wi-Fi
start GPS UART
start I2C
start environment sensor
read GPS continuously
read environment sensor on interval
publish observations every publish interval
log faults without stopping the node
```

## Dashboard Path

Use the existing live observation route:

```text
POST /api/observations
```

Use the schema:

```text
sais.observation.v1
```

## First Pass Observation Set

Publish at least:

```text
environment.temperature.c
environment.humidity.percent
environment.sensor.valid
location.gps.fix_valid
health.node.uptime.ms
health.fault.active
```

Publish these when GPS fix is valid:

```text
location.latitude
location.longitude
location.altitude.m
location.gps.satellites
location.gps.hdop
```

## Do Not Add Yet

Keep the first version boring. Do not add these until the simple telemetry path works:

```text
LoRa
BLE provisioning
signed telemetry
deep sleep
mesh networking
enclosure-specific behavior
advanced geofencing
actuator control
```
