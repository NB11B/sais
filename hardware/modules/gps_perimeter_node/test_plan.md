# GPS Perimeter Environment Node Test Plan

This plan makes the first GPS perimeter node repeatable on a bench before field testing.

## Bench Setup

Required:

```text
ESP32 or ESP32-S3 development board
UART GPS module
SHT31 or BME280 temperature and humidity sensor
USB cable
SAIS dashboard running on local network
serial monitor
```

Optional:

```text
battery pack
status LED
external GPS antenna
```

## Test 1: Boot Test

Procedure:

```text
1. Connect the node over USB.
2. Open serial monitor.
3. Restart the node.
4. Observe startup logs.
```

Expected result:

```text
node_id printed
firmware_version printed
GPS initialization attempted
environment sensor initialization attempted
telemetry transport initialization attempted
```

Pass criteria:

```text
node boots without reset loop
startup logs identify hardware profile
```

## Test 2: Environment Sensor Detection

Procedure:

```text
1. Boot the node with the environment sensor connected.
2. Read temperature and humidity.
3. Confirm sensor_valid is true.
```

Expected result:

```text
temperature reading is plausible
humidity reading is plausible
environment.sensor.valid publishes true or 1
```

## Test 3: GPS No-Fix Behavior

Procedure:

```text
1. Boot the node in a normal indoor bench environment.
2. Allow the GPS parser to run.
3. Observe telemetry before GPS lock.
```

Expected result:

```text
node keeps publishing telemetry
location.gps.fix_valid is false or 0
health.fault.active may be true if no fix exceeds configured timeout
last_error may show GPS_NO_FIX
```

Pass criteria:

```text
node does not go silent while waiting for GPS fix
```

## Test 4: GPS Fix Behavior

Procedure:

```text
1. Move the GPS antenna or node to clear sky view.
2. Wait for GPS fix.
3. Observe serial logs and dashboard telemetry.
```

Expected result:

```text
location.gps.fix_valid becomes true or 1
latitude publishes
longitude publishes
satellite count publishes when available
HDOP publishes when available
```

Pass criteria:

```text
valid latitude and longitude appear in the dashboard path
```

## Test 5: Environment Sensor Fault Visibility

Procedure:

```text
1. Start from a known-good bench setup.
2. Run a second test with the environment sensor absent or unavailable.
3. Observe telemetry.
```

Expected result:

```text
environment.sensor.valid is false or 0
health.fault.active is true or 1
last_error includes ENV_SENSOR_FAIL or ENV_SENSOR_NOT_FOUND
node continues publishing GPS and health fields when possible
```

Pass criteria:

```text
sensor failure is visible and does not stop the node from reporting other status
```

## Test 6: Telemetry Publish Test

Procedure:

```text
1. Run the SAIS dashboard on the network.
2. Configure node telemetry endpoint.
3. Boot the node.
4. Confirm observations are posted at configured interval.
```

Expected result:

```text
new observations arrive every publish interval
node_id matches config
measurement_id values match TELEMETRY_FIELD_MAP.md
```

Pass criteria:

```text
dashboard or API logs show accepted observations
```

## Test 7: Node Identity Test

Procedure:

```text
1. Set node_id to perimeter-node-001.
2. Publish telemetry.
3. Set node_id to perimeter-node-002 on another run.
4. Publish telemetry again.
```

Expected result:

```text
the dashboard can distinguish the two node identities
```

Pass criteria:

```text
node identity is not hardcoded in firmware behavior
```

## Test 8: Stale Reading Test

Procedure:

```text
1. Allow the node to obtain a GPS fix.
2. Continue running until the fix is no longer current according to max_fix_age_ms.
3. Observe telemetry freshness behavior.
```

Expected result:

```text
GPS fix becomes invalid or low confidence when stale
last_error includes GPS_STALE_FIX or GPS_NO_FIX when applicable
stale coordinates are not published as fresh high-confidence readings
```

## Full Pass Criteria

The module passes bench validation when:

```text
[ ] node boots reliably
[ ] environment sensor is detected
[ ] GPS no-fix behavior is visible
[ ] GPS fix behavior is visible
[ ] sensor fault behavior is visible
[ ] observations reach POST /api/observations
[ ] node ID is configurable
[ ] stale readings are marked or suppressed
```
