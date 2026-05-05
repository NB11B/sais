# SAIS Enclosure & Mechanical Framework

This directory contains the mechanical design files for the Sovereign Node housing and mounting hardware.

## Enclosure Specifications

- **Material:** Die-cast Aluminum (AlSi12 or equivalent).
- **Rating:** IP67 minimum.
- **Thermal:** The enclosure acts as the primary heat sink for high-power components. Surface finish must allow for effective thermal contact (e.g., clear alodine or milled mating surfaces).

## Mounting Patterns

- **Standard VESA:** 75x75mm or 100x100mm mounting holes for pole/wall mounting.
- **DIN Rail:** Support for standard 35mm DIN rail mounting via adapter plate.

## Thermal Management

- Thermal Interface Material (TIM) must be used between the controller PCB and the enclosure bosses.
- Targeted thermal resistance: < 5°C/W from component junction to enclosure exterior.

## Files

- `*.step`: Master 3D models for assembly and CNC/molding.
- `*.dxf`: 2D drawings for panel cutouts and labeling.
- `*.pdf`: Assembly drawings and torque specifications.
