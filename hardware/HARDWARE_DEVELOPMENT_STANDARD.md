# SAIS Hardware Development Standard

This standard keeps SAIS hardware development simple, explainable, repeatable, and aligned with the existing dashboard telemetry path.

The hardware section should not become a separate architecture. It should provide a disciplined way to add field nodes, sensor modules, wiring references, test procedures, and firmware patterns inside the existing SAIS repository.

## 1. Hardware Must Be Explainable

Every hardware module must include a plain-language explanation of what it does and why it exists.

A new developer should be able to open the module folder and understand:

```text
what the hardware does
what problem it helps solve
what it senses or controls
what data it publishes
how to test it
```

## 2. Hardware Must Be Teachable

Every module must identify the basic concept it teaches.

Examples:

```text
GPS perimeter node       -> position, fix quality, environmental sensing
relay bank               -> controlled switching and safe power routing
voltage sensing          -> voltage dividers, ADC scaling, calibration
weather station          -> local weather context and sensor freshness
water tank node          -> level sensing, stale data, inspection triggers
```

The goal is not just working hardware. The goal is hardware that can be explained and reproduced.

## 3. Hardware Modules Must Have a Contract

Each module must include `module_contract.md` with:

```text
purpose
inputs
outputs
hardware dependencies
firmware dependencies
failure modes
required telemetry
```

The contract is the boundary between the physical device, the firmware, and the dashboard.

## 4. Hardware Modules Must Publish Telemetry

Every hardware module must document what it publishes into SAIS.

For the current live observation path, sensor readings should map to:

```text
POST /api/observations
schema: sais.observation.v1
```

A hardware module may produce multiple observations from a single publish cycle. For example, a GPS perimeter environment node may publish:

```text
location.latitude
location.longitude
environment.temperature_c
environment.humidity_percent
health.gps.fix_valid
health.node.uptime_ms
```

If the current API does not yet accept a richer node-health packet, the module must still document the intended telemetry object so the dashboard integration can be added consistently.

## 5. Hardware Modules Must Have Repeatable Tests

Each module must include `test_plan.md`.

A useful test plan contains:

```text
boot test
sensor detection test
normal reading test
fault or unplug test
telemetry publish test
dashboard verification test
```

A test is not complete until another developer can repeat it without guessing.

## 6. Hidden Behavior Is Not Allowed

The following should not exist only inside unexplained firmware code:

```text
pin assignments
node IDs
sensor calibration constants
voltage scale factors
publish intervals
fault thresholds
relay safety rules
measurement IDs
API routes
```

They must be documented in wiring, config, telemetry, or firmware notes.

## 7. Separate Reading, Control, and Publishing

Use a simple mental model:

```text
read hardware
validate readings
build telemetry
publish telemetry
observe in dashboard
```

For actuator modules, use:

```text
read state
decide requested action
validate safety
apply hardware command
publish result
```

Hardware drivers should not hide system policy.

## 8. Faults Must Be Visible

A failed sensor should produce visible telemetry, not missing telemetry.

Examples:

```text
GPS has no fix           -> publish fix_valid = false
humidity sensor missing  -> publish sensor_valid = false
battery low              -> publish low_battery = true
publish failed           -> log telemetry_publish_failed
node rebooted            -> publish boot_count or reset reason when available
```

Silent failure makes field systems untrustworthy.

## 9. Node Identity Must Be Explicit

Each field node must have a stable identity.

Minimum identity fields:

```text
node_id
node_type
firmware_version
hardware_profile
farm_id when applicable
field_id when applicable
zone_id when applicable
```

These fields allow the dashboard, FarmGraph, and observation history to connect sensor data to a real asset.

## 10. Keep the First Version Boring

Do not start a new module with mesh networking, encryption, battery optimization, enclosure machining, and advanced fault handling all at once.

Start with:

```text
one node
one sensor set
one payload shape
one dashboard destination
one repeatable test plan
```

After that works, add hardening.

## 11. Promotion Checklist

A hardware module can be considered ready for integration when it has:

```text
README.md
module_contract.md
wiring.md
telemetry.md
test_plan.md
fault_handling.md
firmware_notes.md
example config when applicable
at least one dashboard verification path
```

## 12. Current First Module

The first module using this standard is:

```text
hardware/modules/gps_perimeter_node/
```

This module establishes the pattern for low-risk field telemetry nodes before SAIS adds higher-risk actuator and control hardware.
