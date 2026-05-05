# GPS Perimeter Environment Node Firmware Notes

These notes define the expected firmware shape for the first GPS perimeter node implementation.

## Firmware Goal

Keep the first firmware version simple:

```text
initialize hardware
read GPS
read environment sensor
validate readings
build observation payloads
publish to SAIS
repeat
```

## Main Loop Pattern

Preferred loop:

```text
read GPS parser
read environment sensor on interval
update node health
validate freshness and sensor status
build one or more telemetry observations
publish observations
log result
wait until next publish interval
```

Pseudo-code:

```cpp
void loop() {
    gps.update();

    if (timeToReadEnvironment()) {
        environmentReading = environment.read();
    }

    nodeHealth = health.read();
    faults = faultDetector.evaluate(gpsState, environmentReading, nodeHealth, config);
    observations = telemetryBuilder.buildObservations(gpsState, environmentReading, nodeHealth, faults, config);
    telemetryPublisher.publish(observations);

    delay(config.loopDelayMs);
}
```

## Recommended Libraries

Prototype-friendly options:

```text
TinyGPSPlus                  GPS parser
Adafruit_SHT31               SHT31 temperature and humidity
Adafruit_BME280              BME280 temperature, humidity, pressure
ArduinoJson                  JSON payload creation
WiFi                         network connection
HTTPClient                   POST /api/observations
```

## Configuration Values

The firmware should support these values from config or a clearly documented compile-time section:

```text
node_id
node_type
farm_id
field_id
zone_id
firmware_version
hardware_profile
wifi_ssid
wifi_password or provisioning method
telemetry_host
telemetry_port
telemetry_path
gps_rx_pin
gps_tx_pin
gps_baud
gps_min_satellites
gps_max_fix_age_ms
gps_max_hdop
i2c_sda_pin
i2c_scl_pin
environment_sensor_type
environment_read_interval_ms
telemetry_publish_interval_ms
low_battery_voltage
```

## Observation Publishing Strategy

Until a dedicated rich node-status endpoint exists, publish separate `sais.observation.v1` payloads.

At minimum, publish:

```text
environment.temperature.c
environment.humidity.percent
environment.sensor.valid
location.gps.fix_valid
health.node.uptime.ms
health.fault.active
```

When GPS fix is valid, also publish:

```text
location.latitude
location.longitude
location.altitude.m when available
location.gps.satellites when available
location.gps.hdop when available
```

## Serial Logging

Use consistent logs:

```text
[time_ms] [LEVEL] [MODULE] message
```

Example:

```text
[000500] [INFO] [BOOT] node_id=perimeter-node-001 firmware=0.1.0
[001000] [INFO] [GPS] UART started rx=16 tx=17 baud=9600
[001050] [INFO] [ENV] SHT31 detected
[005000] [WARN] [GPS] no fix yet
[005100] [INFO] [TELEMETRY] published observations=4
```

## Timing Guidance

Recommended first-pass timing:

```text
GPS parser update: every loop
environment sensor read: every 2 seconds
telemetry publish: every 5 seconds
Wi-Fi reconnect check: every 10 seconds
```

## Fault Rules

The firmware should keep publishing when one sensor fails.

Examples:

```text
GPS unavailable          -> publish environment and health
Environment unavailable  -> publish GPS and health
Wi-Fi unavailable        -> keep reading sensors and retry telemetry
```

## Future Hardening

After the first node works, consider:

```text
signed node telemetry
sequence counters
local queue for offline observations
battery voltage calibration
deep sleep mode
watchdog reset reason publishing
local config file stored in flash
BLE provisioning
LoRa bridge
weather-resistant enclosure validation
```

Do not add these before the first simple telemetry path works.
