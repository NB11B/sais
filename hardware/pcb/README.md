# SAIS PCB Design Framework

This directory contains the electronics hardware designs for the Sovereign Node system.

## Design Standards

### 1. General Rules
- **Tooling:** KiCad 7.0 or newer.
- **Layers:** 4-Layer (Signal - GND - Power/Signal - Signal) preferred for signal integrity and EMI.
- **Trace Width:** 0.2mm minimum for signal, 0.5mm+ for power paths.
- **Clearance:** 0.2mm minimum.
- **Vias:** 0.3mm drill / 0.6mm annular ring minimum.

### 2. Component Selection
- Use **Industrial Grade** parts (-40°C to +85°C) whenever possible.
- Avoid obsolete or NRND (Not Recommended for New Design) parts.
- Standard passive sizes: 0603 (1608 Metric) for ease of manual rework, 0402 only where space is critical.

### 3. Connectors & IO
- **M12 Connectors:** IP67-rated circular connectors are the standard for all external IO.
- **Internal Headers:** 2.54mm pitch locking headers (e.g., Molex SL or KK) for internal module interconnects.

## Directory Structure

- `controller/`: Main SBC/MCU carrier (ESP32-S3 / i.MX 8M).
- `power/`: MPPT, Battery Management, and Voltage Regulation.
- `io/`: Interface breakout for 4-20mA, RS-485, and GPIO.

## Manufacturing

- Gerber files should be exported in **X2 format**.
- Always include a **Pick and Place (Centroid) file** and **BOM** in the manufacturing folder of each project.
