# GPS Perimeter Environment Node Wiring

This wiring guide defines a simple bench prototype for the GPS Perimeter Environment Node.

## Prototype Board

Recommended first target:

```text
ESP32 or ESP32-S3 development board
```

The exact pins can be changed in config or firmware, but the module must document the pin map used by each prototype.

## GPS Module Wiring

Typical UART GPS module wiring:

| GPS Pin | ESP32 Pin | Notes |
|---|---:|---|
| VCC | 3.3 V or 5 V | Depends on GPS module regulator and logic level |
| GND | GND | Common ground required |
| TX | GPIO 16 | GPS TX to ESP32 RX |
| RX | GPIO 17 | GPS RX to ESP32 TX |

Default UART settings:

```text
baud: 9600
format: 8N1
```

## Temperature and Humidity Sensor Wiring

Preferred I2C sensor: SHT31 or BME280.

| Sensor Pin | ESP32 Pin | Notes |
|---|---:|---|
| VCC | 3.3 V | Use 3.3 V logic for I2C |
| GND | GND | Common ground required |
| SDA | GPIO 8 | I2C data |
| SCL | GPIO 9 | I2C clock |

Common I2C addresses:

```text
SHT31: 0x44 or 0x45
BME280: 0x76 or 0x77
```

## Optional Battery Voltage Sense

Use a resistor divider sized for the expected battery voltage and ESP32 ADC input range.

| Signal | ESP32 Pin | Notes |
|---|---:|---|
| Battery divider output | GPIO 4 | ADC input, optional |

Battery voltage sensing is optional for the first prototype. Do not connect battery voltage directly to an ESP32 ADC pin.

## Optional Status LED

| Signal | ESP32 Pin | Notes |
|---|---:|---|
| Status LED | Board LED or GPIO 2 | Optional heartbeat or fault indicator |

## Power Notes

- Use USB power for first bench testing.
- Keep all grounds common.
- Confirm GPS module voltage requirements before connecting VCC.
- Confirm I2C sensor is 3.3 V compatible.
- If using an external antenna GPS module, test sky visibility before enclosure testing.

## Bring-Up Checks

Before running full telemetry firmware:

```text
[ ] Confirm ESP32 boots from USB power
[ ] Confirm serial monitor works
[ ] Confirm GPS module power LED is on if present
[ ] Confirm GPS NMEA output appears on UART
[ ] Confirm I2C scanner detects the environment sensor
[ ] Confirm temperature and humidity readings are plausible
[ ] Confirm Wi-Fi can reach the SAIS dashboard host
[ ] Confirm telemetry reaches POST /api/observations
```

## Field Notes

- GPS modules may take several minutes to get first fix after cold start.
- GPS performs poorly indoors or inside metal enclosures.
- Enclosures may require an external GPS antenna.
- Place temperature and humidity sensors away from voltage regulators and direct sun when possible.
- If the node is used as a perimeter marker, record its physical mounting location in the FarmGraph as a sensor node.
