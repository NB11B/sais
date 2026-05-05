# GPS Perimeter Environment Node Contract

## Purpose

The GPS Perimeter Environment Node reports physical location, local temperature, humidity, and node health to SAIS.

It provides a simple, low-risk field telemetry module for perimeter awareness and hardware development training.

## Inputs

```text
GPS UART data
I2C temperature reading
I2C humidity reading
optional battery voltage
Wi-Fi status
firmware uptime
configuration values
```

## Outputs

```text
latitude
longitude
altitude when available
GPS fix validity
satellite count
HDOP when available
temperature
humidity
sensor validity
node uptime
optional battery voltage
Wi-Fi signal strength
fault status
last error
```

## Hardware Dependencies

Required:

```text
ESP32 or ESP32-S3 class controller
UART GPS module
I2C temperature and humidity sensor
3.3 V power for MCU and I2C sensor
common ground between all modules
```

Optional:

```text
battery voltage divider
status LED
external GPS antenna
weather-resistant enclosure
```

## Firmware Dependencies

Required:

```text
GPS parser
I2C environment sensor driver
configuration loader or compile-time config
telemetry publisher
fault logger
```

Recommended firmware libraries for prototype work:

```text
TinyGPSPlus or equivalent GPS parser
Adafruit SHT31, Adafruit BME280, or equivalent I2C sensor driver
ArduinoJson if building JSON locally
WiFi or HTTP client for dashboard posting
```

## Failure Modes

```text
GPS module not detected
GPS has no fix
GPS fix is stale
satellite count below minimum
HDOP above acceptable threshold
temperature sensor not detected
humidity reading invalid
I2C bus failure
Wi-Fi disconnected
telemetry publish failed
battery below warning threshold
unexpected reboot
configuration missing or invalid
```

## Required Telemetry

Minimum required fields:

```text
node.id
node.type
node.firmware_version
node.uptime_ms
location.fix_valid
location.latitude when valid
location.longitude when valid
environment.temperature_c
environment.humidity_percent
environment.sensor_valid
health.telemetry_ok
health.fault
health.last_error
```

Recommended observation measurement IDs:

```text
location.latitude
location.longitude
location.altitude.m
location.gps.fix_valid
location.gps.satellites
location.gps.hdop
environment.temperature.c
environment.humidity.percent
environment.sensor.valid
health.node.uptime.ms
health.battery.v
health.wifi.rssi.dbm
health.fault.active
```

## Configuration Inputs

The module should support these values in config:

```text
node_id
node_type
farm_id
field_id
zone_id
firmware_version
hardware_profile
gps UART RX pin
gps UART TX pin
gps baud rate
minimum GPS satellites
maximum GPS fix age
environment sensor type
I2C SDA pin
I2C SCL pin
publish interval
telemetry endpoint
optional battery warning threshold
```

## Integration Status

Status: specification module.

Next implementation target:

```text
hardware/examples/gps_perimeter_node_minimal/
```

Primary dashboard path:

```text
POST /api/observations
schema: sais.observation.v1
```
