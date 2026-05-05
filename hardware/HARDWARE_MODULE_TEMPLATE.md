# SAIS Hardware Module Template

Use this template when adding a new hardware module under `hardware/modules/`.

Create a folder named for the module:

```text
hardware/modules/<module_name>/
```

Then add the files below.

## Required Files

```text
README.md
module_contract.md
wiring.md
telemetry.md
test_plan.md
fault_handling.md
firmware_notes.md
```

## README.md

Use plain language.

Required sections:

```text
purpose
what this module teaches
what this module does
what this module does not do
recommended hardware
basic data flow
```

## module_contract.md

Define the technical boundary.

Required sections:

```text
purpose
inputs
outputs
hardware dependencies
firmware dependencies
failure modes
required telemetry
integration status
```

## wiring.md

Document physical connections.

Required sections:

```text
supported board or boards
pin map
power notes
grounding notes
signal notes
bring-up checks
```

## telemetry.md

Document what the module publishes.

Required sections:

```text
telemetry purpose
field map
SAIS observation mappings
node health mappings
example payload
expected dashboard behavior
```

## test_plan.md

Make testing repeatable.

Required sections:

```text
bench setup
boot test
sensor detection test
normal data test
fault test
telemetry test
dashboard verification
pass criteria
```

## fault_handling.md

Make failures visible.

Required sections:

```text
fault philosophy
fault codes
fault behavior
telemetry behavior during faults
recovery behavior
```

## firmware_notes.md

Keep firmware expectations teachable.

Required sections:

```text
firmware loop
libraries or drivers
configuration values
serial logs
publish interval
future hardening
```

## Module Completion Checklist

A module is ready for integration when all items are complete:

```text
[ ] README explains the module in plain language
[ ] module_contract defines inputs, outputs, dependencies, failure modes, and telemetry
[ ] wiring includes a pin map and power notes
[ ] telemetry maps module data to SAIS fields
[ ] test_plan includes normal and fault tests
[ ] fault_handling defines visible fault behavior
[ ] firmware_notes define the expected firmware pattern
[ ] example config exists when applicable
[ ] dashboard verification path is documented
```
