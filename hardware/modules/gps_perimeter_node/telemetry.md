# GPS Perimeter Environment Node Telemetry

This document maps the GPS Perimeter Environment Node to the SAIS telemetry path.

## Telemetry Purpose

The node publishes:

```text
position
GPS fix quality
temperature
humidity
node health
fault visibility
```

## Current Dashboard Path

For readings that fit the current live sensor model, publish observations to:

```text
POST /api/observations
schema: sais.observation.v1
```

A single node update may create several observation payloads.

## Recommended Observation Mappings

| Node Value | Measurement ID | Unit | Layer | Basis |
|---|---|---:|---|---|
| Latitude | `location.latitude` | `deg` | `Location` | `direct` |
| Longitude | `location.longitude` | `deg` | `Location` | `direct` |
| Altitude | `location.altitude.m` | `m` | `Location` | `direct` |
| GPS fix valid | `location.gps.fix_valid` | `bool` | `Location` | `direct` |
| GPS satellites | `location.gps.satellites` | `count` | `Location` | `direct` |
| GPS HDOP | `location.gps.hdop` | `ratio` | `Location` | `direct` |
| Temperature | `environment.temperature.c` | `degC` | `Environment` | `direct` |
| Humidity | `environment.humidity.percent` | `%` | `Environment` | `direct` |
| Environment sensor valid | `environment.sensor.valid` | `bool` | `Environment` | `direct` |
| Uptime | `health.node.uptime.ms` | `ms` | `NodeHealth` | `direct` |
| Battery voltage | `health.battery.v` | `V` | `NodeHealth` | `direct` |
| Wi-Fi RSSI | `health.wifi.rssi.dbm` | `dBm` | `NodeHealth` | `direct` |
| Fault active | `health.fault.active` | `bool` | `NodeHealth` | `direct` |

If the current API requires numeric values, encode boolean fields as:

```text
true  -> 1
false -> 0
```

## Example Temperature Observation

```json
{
  "schema": "sais.observation.v1",
  "node_id": "perimeter-node-001",
  "farm_id": "local",
  "field_id": "field-a",
  "zone_id": "zone-a1",
  "timestamp": "2026-05-02T12:00:00Z",
  "measurement_id": "environment.temperature.c",
  "layer": "Environment",
  "value": 24.7,
  "unit": "degC",
  "measurement_basis": "direct",
  "confidence": "medium",
  "source": {
    "type": "sensor",
    "sensor_model": "SHT31",
    "hardware_profile": "esp32_s3_gps_sht31"
  }
}
```

## Example GPS Fix Observation

```json
{
  "schema": "sais.observation.v1",
  "node_id": "perimeter-node-001",
  "farm_id": "local",
  "field_id": "field-a",
  "zone_id": "zone-a1",
  "timestamp": "2026-05-02T12:00:00Z",
  "measurement_id": "location.gps.fix_valid",
  "layer": "Location",
  "value": 1,
  "unit": "bool",
  "measurement_basis": "direct",
  "confidence": "medium",
  "source": {
    "type": "sensor",
    "sensor_model": "NEO-M8N",
    "hardware_profile": "esp32_s3_gps_sht31"
  }
}
```

## Rich Node Packet Target

A richer future node-status endpoint should accept one packet shaped like this:

```json
{
  "node": {
    "id": "perimeter-node-001",
    "type": "gps_environment_node",
    "firmware_version": "0.1.0",
    "hardware_profile": "esp32_s3_gps_sht31",
    "uptime_ms": 125000
  },
  "location": {
    "latitude": 27.9094,
    "longitude": -82.7873,
    "altitude_m": 8.4,
    "fix_valid": true,
    "satellites": 9,
    "hdop": 1.2,
    "last_fix_ms": 124500
  },
  "environment": {
    "temperature_c": 28.7,
    "humidity_percent": 71.4,
    "sensor_valid": true,
    "last_read_ms": 124800
  },
  "health": {
    "battery_v": 4.08,
    "wifi_rssi_dbm": -62,
    "telemetry_ok": true,
    "fault": false,
    "last_error": null
  }
}
```

## Expected Dashboard Behavior

The dashboard should be able to show:

```text
node identity
last update time
GPS fix status
map marker when lat/lon are valid
temperature
humidity
sensor health
fault state
stale telemetry warning
```

## Stale Data Rule

If a GPS fix or environment reading is older than the configured maximum age, publish the reading as low confidence or publish the validity field as false.

Do not silently reuse stale values without marking them.
