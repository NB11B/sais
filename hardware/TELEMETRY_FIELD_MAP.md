# SAIS Hardware Telemetry Field Map

This document defines the shared language between hardware modules and the existing SAIS dashboard telemetry path.

SAIS already accepts live sensor observations through:

```text
POST /api/observations
schema: sais.observation.v1
```

Hardware modules should use that path whenever a reading can be represented as a measurement observation. Rich node health and transport status may require additional dashboard support, but those fields should still be documented here so the system evolves consistently.

## Observation Payload Baseline

The current observation API expects the live telemetry shape documented in the root README.

Minimum pattern:

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
    "sensor_model": "SHT31"
  }
}
```

## Recommended Measurement IDs

### Location

| Measurement ID | Unit | Layer | Notes |
|---|---:|---|---|
| `location.latitude` | `deg` | `Location` | Decimal degrees |
| `location.longitude` | `deg` | `Location` | Decimal degrees |
| `location.altitude.m` | `m` | `Location` | GPS altitude when available |
| `location.gps.satellites` | `count` | `Location` | Number of satellites used or visible |
| `location.gps.hdop` | `ratio` | `Location` | Horizontal dilution of precision |
| `location.gps.fix_valid` | `bool` | `Location` | Use 1 for true, 0 for false if numeric API is required |

### Environment

| Measurement ID | Unit | Layer | Notes |
|---|---:|---|---|
| `environment.temperature.c` | `degC` | `Environment` | Air temperature near node |
| `environment.humidity.percent` | `%` | `Environment` | Relative humidity |
| `environment.sensor.valid` | `bool` | `Environment` | Use 1 for true, 0 for false if numeric API is required |

### Node Health

| Measurement ID | Unit | Layer | Notes |
|---|---:|---|---|
| `health.node.uptime.ms` | `ms` | `NodeHealth` | Uptime since boot |
| `health.battery.v` | `V` | `NodeHealth` | Battery voltage if available |
| `health.wifi.rssi.dbm` | `dBm` | `NodeHealth` | Wi-Fi signal strength |
| `health.telemetry.ok` | `bool` | `NodeHealth` | Last publish status |
| `health.fault.active` | `bool` | `NodeHealth` | Active fault present |

## Rich Node Telemetry Shape

For dashboard views that want one full node packet instead of separate observation rows, hardware modules should document a shape like this:

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

This rich packet is a documentation target for dashboard evolution. Until a dedicated endpoint exists, modules should publish individual `sais.observation.v1` observations where possible.

## Confidence Guidance

Use confidence conservatively:

```text
high     calibrated sensor, current reading, valid status
medium   normal low-cost sensor reading, current enough for dashboard use
low      stale, degraded, weak GPS, or uncalibrated reading
```

## Failure Visibility Rule

When a sensor fails, publish a visible fault or validity measurement when possible.

Examples:

```text
GPS no fix              -> location.gps.fix_valid = 0
humidity sensor missing -> environment.sensor.valid = 0
node fault active       -> health.fault.active = 1
```

Missing telemetry should be treated as a failure mode, not a normal state.
