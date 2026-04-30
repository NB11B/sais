# SAIS Hardware — Enclosure, PCB, and BOM

This directory contains all hardware design files for the Sovereign Node physical assembly.

## Contents (Planned)

```
hardware/
├── enclosure/          # IP67 die-cast enclosure mechanical drawings (STEP, DXF)
├── pcb/                # PCB schematics and layouts (KiCad)
│   ├── controller/     # ESP32-S3 carrier board
│   ├── power/          # Power management and MPPT interface board
│   └── io/             # Industrial I/O breakout board (M12 connectors, 4-20mA, RS-485)
├── bom/                # Bill of Materials (CSV, interactive HTML BOM)
└── datasheets/         # Key component datasheets
```

## Design Tools

- **PCB Design:** KiCad 7.x (open-source)
- **Mechanical Design:** FreeCAD (open-source) or equivalent
- **BOM Management:** KiCad BOM export + interactive HTML BOM plugin

## Design Principles

- All PCB designs use **through-hole or industrial-grade SMD components** rated for −40°C to +85°C.
- All external connectors are **M12 circular, IP67-rated**.
- The PCB layout must allow the die-cast enclosure to serve as the primary heat sink for the i.MX 8M SBC. Thermal interface material (TIM) pads are specified in the mechanical drawings.
- No SD card slots. Storage is exclusively eMMC, soldered directly to the SBC.

## Contributing

Hardware contributions (enclosure improvements, PCB revisions, alternative SBC carrier boards) are welcome. Please follow the KiCad design rules defined in `pcb/design_rules.kicad_dru` and include updated BOM files with any PCB changes.

See the root [`CONTRIBUTING.md`](../CONTRIBUTING.md) for general contribution guidelines.

---

*Nathanael J. Bocker, 2026 all rights reserved*
