# Contributing to SAIS

Thank you for your interest in contributing to the Sovereign Ag-Infrastructure Stack. SAIS is a community-driven project, and contributions across all layers — firmware, hardware, software, documentation, and protocol design — are welcome and valued.

## Before You Begin

Please read the [`README.md`](README.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) to understand the project's design philosophy and the four inviolable constraints that govern all architectural decisions:

1. **Resilience** — Zero dependency on external WAN or cloud infrastructure.
2. **Autonomy** — Deterministic real-time control must never be interrupted by the intelligence layer.
3. **Sovereignty** — No raw data leaves the node without explicit operator authorization.
4. **Verifiability** — All operational events are cryptographically signed and immutable.

Any contribution that violates these constraints will not be merged, regardless of its technical merit.

## How to Contribute

### Reporting Issues

Use the GitHub Issues tracker to report bugs, request features, or flag documentation gaps. Please include:

- A clear, descriptive title.
- The component affected (firmware, hardware, software, docs).
- Steps to reproduce (for bugs) or a clear use-case description (for features).
- Any relevant logs, schematics, or screenshots.

### Submitting Pull Requests

1. **Fork** the repository and create a branch from `main`.
2. **Name your branch** descriptively: `feat/ota-update-mechanism`, `fix/esp32-watchdog-timer`, `docs/auditor-spec`.
3. **Write clear commit messages** that describe what changed and why.
4. **Test your changes** before submitting. For firmware, provide evidence of hardware testing. For software, include unit tests. For documentation, verify all technical claims.
5. **Open a Pull Request** against `main` with a description of the change, the motivation, and any relevant context.

### Contribution Areas

| Area | Description | Skills Needed |
|---|---|---|
| **Firmware** | ESP32-S3 RTOS control loops, sensor drivers, actuator interfaces | C/C++, FreeRTOS, embedded systems |
| **Hardware** | Enclosure design, PCB schematics, BOM optimization, power management | KiCad, mechanical CAD, electronics |
| **Software** | Container definitions, DDS middleware, OADA mapping, C2 Dashboard, Auditor | Python, Rust, Go, Docker, web |
| **Protocol** | DDS QoS profiles, Micro XRCE-DDS bridge, OADA schema extensions | Distributed systems, protocol design |
| **Cryptography** | ZKP signing pipeline, TrustZone integration, key management | Cryptography, ARM TrustZone, Rust |
| **Documentation** | Architecture docs, hardware guides, deployment tutorials | Technical writing |
| **Testing** | Field testing, hardware validation, integration testing | Any of the above |

## Code Standards

- **Firmware (C/C++):** Follow the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html). All RTOS tasks must have documented stack size, priority, and timing guarantees.
- **Software (Python/Rust/Go):** Follow the idiomatic style guide for the language. All containers must have a defined resource budget (CPU, RAM, storage).
- **Documentation:** Written in Markdown. Technical claims must be sourced. Architecture decisions must explain the reasoning, not just the outcome.

## Security

If you discover a security vulnerability, **do not open a public issue**. Please follow the responsible disclosure process described in [`SECURITY.md`](SECURITY.md).

## Code of Conduct

All contributors are expected to follow the [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). SAIS is built on the principle that the people who grow food and manage land deserve tools that work for them. That principle extends to how we treat each other in this community.

---

*Nathanael J. Bocker, 2026 all rights reserved*
