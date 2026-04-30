# Sovereign Ag-Infrastructure Stack (SAIS)

> **The Linux of the Field. The Farm is the Launchpad.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-green.svg)]()
[![Architecture: Federated Edge](https://img.shields.io/badge/Architecture-Federated%20Edge-orange.svg)]()

SAIS is a decentralized, edge-native, open-source operating system for managing closed-loop resource environments. It is designed to run autonomously on a solar-powered, ruggedized edge node deployed in any field, ranch, or off-grid environment — with zero dependency on cloud infrastructure, corporate servers, or subscription services.

**The farmer owns the hardware. The farmer owns the data. The farmer owns the intelligence.**

---

## The Problem

The current agricultural technology stack is built against the farmer:

- **Input monopolies** control seeds, chemicals, and commodity pricing simultaneously, trapping farmers in a permanent margin squeeze.
- **Cloud-dependent farm management software** extracts operational data from farmers and sells the aggregated intelligence back to the market — often to the same corporations squeezing the farmer's margins.
- **Centralized architectures** create single points of failure: if the WAN link goes down, the farm goes dark.
- **Legacy carbon markets** are paralyzed by greenwashing scandals and prohibitively expensive manual verification, locking farmers out of ecological finance.

SAIS is the engineering alternative. It is not a protest. It is a replacement.

---

## The Solution: The Sovereign Node

A **Sovereign Node** is a self-contained, solar-powered edge controller that manages a farm's complete digital nervous system without ever needing to contact a central server.

### Hardware Architecture

The node uses a **Dual-Core Edge Controller** design:

| Layer | Component | Role |
|---|---|---|
| **Controller (Real-Time)** | ESP32-S3 (RTOS) | Deterministic I/O: gate motors, pumps, livestock sensors, nutrient dosing |
| **SCADA/Compute (Intelligence)** | NXP i.MX 8M (Industrial SBC) | Containerized logic: MQTT broker, DDS middleware, ZKP Auditor, C2 Dashboard |
| **Enclosure** | IP67 die-cast, fanless | Field-deployable, no moving parts, no consumables |
| **Storage** | Industrial eMMC | No SD cards; rated for continuous write cycles |
| **Power** | Solar + LiFePO4 battery | Off-grid operation indefinitely |

### Communication Protocol

SAIS uses **DDS (Data Distribution Service)** — the same peer-to-peer middleware used in aerospace flight control, NATO military systems, and ROS 2 robotics — as its communication backbone. There is no central broker. If any node fails, the mesh continues operating.

Data structures are mapped to **OADA (Open Agricultural Data Alliance)** schemas, ensuring interoperability with any OADA-compliant application without custom drivers.

### The C2 Dashboard

The Command and Control Dashboard runs locally on the node, accessible via any browser on the local LAN or mesh. It operates as a **Federated Orchestrator**: it sends code to the nodes; the nodes return only results. Raw sensor data never leaves the node without explicit operator authorization.

### The Auditor Container

Every sensor reading and actuator command is cryptographically signed using a private key stored in the node's ARM TrustZone secure enclave. These records form an **immutable ledger of stewardship** — a machine-generated, cryptographically verifiable history of what happened on this land, when, and with what inputs.

This ledger is the foundation of the **"Proof of Stewardship" report** — the verified ecological data that financial institutions need to issue Carbon-Plus bonds, bypassing the legacy MRV industry entirely.

---

## Farm-to-Orbit

A farm operating in a high-variability, off-grid environment is mathematically identical to a lunar greenhouse. The same engineering constraints apply: extreme latency tolerance, resource scarcity management, zero dependency on external infrastructure, and cryptographically verifiable operational data.

Every hour a Sovereign Node spends in a field is a stress test that validates its readiness for off-earth deployment. SAIS is being built for the farm. It is being designed for orbit.

---

## Repository Structure

```
sais/
├── docs/                    # Architecture, specifications, and strategic documents
│   ├── ARCHITECTURE.md      # Full system architecture reference
│   ├── STRATEGIC_VISION.md  # Farm-to-Orbit strategic vision document
│   ├── HARDWARE_SPEC.md     # Hardware bill of materials and enclosure spec
│   ├── PROTOCOL_SPEC.md     # DDS/OADA communication protocol specification
│   └── AUDITOR_SPEC.md      # Cryptographic auditor and ZKP signing specification
├── firmware/                # ESP32-S3 RTOS firmware (Controller Layer)
│   └── README.md
├── hardware/                # Enclosure designs, PCB schematics, BOM
│   └── README.md
├── software/                # Containerized software stack (SCADA/Compute Layer)
│   └── README.md
├── scripts/                 # Deployment, provisioning, and OTA update scripts
│   └── README.md
├── CONTRIBUTING.md          # How to contribute
├── CODE_OF_CONDUCT.md       # Community standards
├── SECURITY.md              # Security policy and responsible disclosure
└── LICENSE                  # GNU AGPL v3
```

---

## Engineering Roadmap

### Sprint 1: "Iron" — Gateway Hardware
**Deliverable:** A prototype Sovereign Node in an IP67 enclosure, validated for 30 days of continuous off-grid operation.

Focus areas: power architecture, dual-core validation, secure enclave provisioning, thermal management.

### Sprint 2: "Plumbing" — DDS/MQTT Mesh
**Deliverable:** A functional mesh of three Sovereign Nodes communicating without a server, surviving a complete network blackout, and autonomously executing an irrigation or feeding cycle.

Focus areas: DDS peer discovery, LoRa/Micro XRCE-DDS bridge, OTA update mechanism, blackout scenario validation.

### Sprint 3: "Sovereignty" — The Auditor Container
**Deliverable:** A locally hosted C2 Dashboard rendering a cryptographically signed "Proof of Stewardship" report from live node data.

Focus areas: ZKP signing pipeline, OADA data mapping, dashboard UI, MRV report generation.

---

## Strategic Context

SAIS is designed to structurally undermine three incumbent failure modes:

1. **Input monopoly and the margin squeeze** — by reducing operational costs and enabling direct ecological revenue streams that bypass commodity markets.
2. **Data extractivism** — by making it architecturally impossible for any third party to access raw farm data without explicit operator authorization.
3. **Financialization of farmland** — by transforming the farm from a low-margin commodity factory into a high-margin producer of verified ecological assets, providing a viable economic path for the next generation of operators without selling the land.

For the full strategic analysis, see [`docs/STRATEGIC_VISION.md`](docs/STRATEGIC_VISION.md).

---

## Contributing

SAIS is an open project. Contributions are welcome across all layers: firmware, hardware design, containerized software, documentation, and protocol specification.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a pull request.

---

## License

SAIS is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This means any derivative work — including network-deployed services — must also be released under the same license. This is a deliberate choice: it prevents corporations from taking the open-source core, wrapping it in a proprietary service, and selling it back to the farmers it was built to liberate.

See [`LICENSE`](LICENSE) for the full text.

---

## Contact

**Nathanael J. Bocker**

---

*Nathanael J. Bocker, 2026 all rights reserved*
