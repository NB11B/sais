# SAIS Hardware

This directory contains the hardware development layer for SAIS field nodes, sensor packages, enclosure work, PCB planning, wiring references, and repeatable bring-up procedures.

SAIS hardware should be understandable by a new developer, teachable to a field operator, repeatable on a bench, and visible through the established dashboard telemetry path.

The hardware section is not a separate repository and is not a second architecture. It is the practical hardware layer inside the existing SAIS repo.

## Hardware Development Goal

Every hardware module should answer four questions:

```text
1. What does this hardware do?
2. How is it wired?
3. How does firmware talk to it?
4. What telemetry does it publish into SAIS?
```

The preferred development pattern is:

```text
sense
validate
package
publish
observe in dashboard
```

## Current Hardware Focus

The first simple teachable node is:

```text
modules/gps_perimeter_node/
```

This node reports GPS position, temperature, humidity, and node health into the SAIS telemetry model. It is intentionally low risk because it observes and reports. It does not actuate relays, pumps, valves, gates, or power routing hardware.

## Directory Structure

```text
hardware/
├── README.md
├── HARDWARE_DEVELOPMENT_STANDARD.md
├── HARDWARE_MODULE_TEMPLATE.md
├── TELEMETRY_FIELD_MAP.md
├── modules/
│   └── gps_perimeter_node/
│       ├── README.md
│       ├── module_contract.md
│       ├── wiring.md
│       ├── telemetry.md
│       ├── test_plan.md
│       ├── fault_handling.md
│       └── firmware_notes.md
├── examples/
│   └── gps_perimeter_node_minimal/
│       ├── README.md
│       └── config.example.json
├── enclosure/
├── pcb/
├── bom/
└── datasheets/
```

Planned mechanical and PCB content remains part of this section:

```text
hardware/
├── enclosure/          # IP67 enclosure mechanical drawings, STEP, DXF
├── pcb/                # PCB schematics and layouts, KiCad
│   ├── controller/     # ESP32-S3 or edge-controller carrier board
│   ├── power/          # Power management, solar, battery, and regulator boards
│   └── io/             # Industrial I/O breakout board, M12, 4-20 mA, RS-485
├── bom/                # Bill of Materials, CSV and interactive HTML BOM
└── datasheets/         # Key component datasheets
```

## Hardware Module Rule

A hardware module is not complete when it works once. It is complete when it can be explained, wired, tested, faulted, and observed.

Each module should include:

```text
README.md
module_contract.md
wiring.md
telemetry.md
test_plan.md
fault_handling.md
firmware_notes.md
```

## Dashboard Telemetry Rule

Every hardware module must identify the SAIS telemetry fields it produces.

For live observations that fit the current API, field nodes should publish to:

```text
POST /api/observations
```

For richer node health, GPS fix quality, firmware status, battery health, and transport status, the module should document the intended dashboard telemetry object even if the endpoint is still planned.

## Design Tools

- PCB design: KiCad 7.x or newer
- Mechanical design: FreeCAD or equivalent
- BOM management: KiCad BOM export plus interactive HTML BOM plugin
- Firmware targets: ESP32, ESP32-S3, Arduino UNO Q, STM32-class controllers, and future Linux edge nodes

## Design Principles

- Field-first: hardware exists to answer operational farm and ranch questions.
- Offline-first: hardware must remain useful without cloud dependency.
- Explainable: every module must be teachable from its own documents.
- Repeatable: bring-up and tests must be runnable by another developer.
- Visible: faults and readings should appear in logs and dashboard telemetry.
- Safe by default: failed sensors should produce visible faults, not silent behavior.
- Configurable: node identity, pins, thresholds, and publish intervals should not be hidden in unexplained code.

## Contributing

Hardware contributions are welcome across sensor modules, enclosure improvements, PCB revisions, field wiring, firmware examples, and test procedures.

New hardware modules should follow [`HARDWARE_MODULE_TEMPLATE.md`](HARDWARE_MODULE_TEMPLATE.md) and the standard in [`HARDWARE_DEVELOPMENT_STANDARD.md`](HARDWARE_DEVELOPMENT_STANDARD.md).

See the root [`CONTRIBUTING.md`](../CONTRIBUTING.md) for general contribution guidelines.

---

Copyright © 2026 Nathanael J. Bocker. Licensed under AGPL-3.0.
