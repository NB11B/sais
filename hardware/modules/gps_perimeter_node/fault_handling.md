# GPS Perimeter Environment Node Fault Handling

The node should fail visibly.

A sensor fault should not make the node disappear from the dashboard. The node should continue publishing whatever valid state it still has, plus a clear fault field.

## Fault Philosophy

Use this rule:

```text
bad sensor data should become visible fault telemetry
missing sensor data should become visible fault telemetry
stale sensor data should become visible fault telemetry
```

Do not silently reuse stale readings as if they are current.

## Fault Codes

Recommended initial fault codes:

| Fault Code | Meaning | Severity |
|---|---|---|
| `NONE` | No active fault | normal |
| `GPS_NOT_DETECTED` | GPS UART has no usable data | warning |
| `GPS_NO_FIX` | GPS is detected but has no valid fix | warning |
| `GPS_STALE_FIX` | Last valid fix is older than max allowed age | warning |
| `GPS_LOW_SATELLITES` | Satellite count below configured minimum | warning |
| `GPS_POOR_HDOP` | HDOP is above configured threshold | warning |
| `ENV_SENSOR_NOT_FOUND` | Environment sensor not detected | warning |
| `ENV_SENSOR_INVALID` | Environment reading is invalid or out of range | warning |
| `WIFI_DISCONNECTED` | Wi-Fi is not connected | warning |
| `TELEMETRY_PUBLISH_FAILED` | Last telemetry publish failed | warning |
| `LOW_BATTERY` | Battery below configured warning voltage | warning |
| `CONFIG_INVALID` | Config missing or invalid | fault |

## Fault Behavior

### GPS not detected

Telemetry behavior:

```text
location.gps.fix_valid = 0
health.fault.active = 1
health.last_error = GPS_NOT_DETECTED
```

The node should still publish environment and health readings if available.

### GPS no fix

Telemetry behavior:

```text
location.gps.fix_valid = 0
health.last_error = GPS_NO_FIX
```

The node should continue running because no-fix behavior is normal during indoor bench testing or cold start.

### GPS stale fix

Telemetry behavior:

```text
location.gps.fix_valid = 0
health.last_error = GPS_STALE_FIX
```

Do not publish stale coordinates as fresh high-confidence location readings.

### Environment sensor unavailable

Telemetry behavior:

```text
environment.sensor.valid = 0
health.fault.active = 1
health.last_error = ENV_SENSOR_NOT_FOUND
```

The node should still publish GPS and health readings if available.

### Telemetry publish failed

Telemetry behavior:

```text
health.telemetry.ok = 0
health.last_error = TELEMETRY_PUBLISH_FAILED
```

The node should retry on the next publish interval.

## Recovery Behavior

Faults should clear automatically when valid readings resume.

Examples:

```text
GPS_NO_FIX clears when GPS fix becomes valid
ENV_SENSOR_NOT_FOUND clears when sensor is detected again after restart or rescan
WIFI_DISCONNECTED clears when Wi-Fi reconnects
TELEMETRY_PUBLISH_FAILED clears after a successful publish
```

## Logging Behavior

Serial logs should use a consistent format:

```text
[time_ms] [LEVEL] [MODULE] message
```

Examples:

```text
[001250] [INFO] [GPS] parser started at 9600 baud
[005000] [WARN] [GPS] no valid fix yet
[005010] [INFO] [ENV] temperature=24.7C humidity=63.2%
[005100] [INFO] [TELEMETRY] published 4 observations
```

## Field Rule

A field node that is alive but degraded is more useful than a silent node.

The GPS perimeter node should publish degraded status whenever possible.
