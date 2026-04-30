# Sovereign Ag-Infrastructure Stack (SAIS)

> **The Linux of the Field. The Farm is the Launchpad.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Status: Active Development](https://img.shields.io/badge/Status-Active%20Development-green.svg)]()
[![Architecture: Federated Edge](https://img.shields.io/badge/Architecture-Federated%20Edge-orange.svg)]()
[![GPU: Adreno 702 GF(48)](https://img.shields.io/badge/GPU-Adreno%20702%20GF(48)-purple.svg)]()

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

The node uses a **Dual-Core Edge Controller** design, optimized for the [Arduino UNO Q](docs/HARDWARE_SPEC.md) (STM32U585 + QRB2210) to provide a complete, low-cost ($165) entry point:

| Layer | Component | Role |
|---|---|---|
| **Controller (Real-Time)** | STM32U585 / ESP32-S3 | Deterministic I/O: gate motors, pumps, livestock sensors, nutrient dosing |
| **SCADA/Compute (Intelligence)** | QRB2210 / i.MX 8M | Containerized logic: MQTT broker, DDS middleware, ZKP Auditor, C2 Dashboard |
| **Enclosure** | IP67 die-cast, fanless | Field-deployable, no moving parts, no consumables |
| **Storage** | Onboard eMMC | No SD cards; rated for continuous write cycles |
| **Power** | Solar + LiFePO4 battery | Off-grid operation indefinitely |

### The Intelligence Layer

SAIS solves the cognitive overload of traditional SCADA systems by acting as an **active farm intelligence agent**. The `sais-intelligence` container runs entirely at the edge:
- **Edge Inference (TinyML):** Runs anomaly detection and predictive maintenance models on raw telemetry.
- **Local Knowledge Graph (RAG):** A vector database containing agronomic best practices, historical logs, and equipment manuals.
- **On-Device LLM:** Synthesizes anomalies and RAG context into natural-language alerts for the farmer, explaining every automated decision it makes.

### Autonomous Drone Swarms (Artificial Bats)

SAIS extends its intelligence to the sky. By integrating the [Adaptive Engine's PSMSL core](docs/ADAPTIVE_AUDIO_INTEGRATION.md), SAIS enables **autonomous, decentralized drone swarms operating as artificial bats**. 
- Drones use **ultrasonic echolocation** (10ms FM chirps) to navigate GPS-denied environments like dense crop canopies or indoor habitats.
- The swarm coordinates via a peer-to-peer DDS mesh, using acoustic Grassmann curvature to maintain formation without a central ground station.
- The swarm acts as a collective ultrasonic sensor array for non-contact soil moisture and biomass estimation.

### NGC Quantum-Inspired Edge GPU

The Uno Q's **Adreno 702 GPU** is the most powerful and underutilized component in the SAIS hardware stack. By integrating the [NGC-Quantum-CUDA / GeoFlow kernels](docs/NGC_QUANTUM_INTEGRATION.md), SAIS deploys quantum-inspired GF(48) geometric computation directly to the edge — achieving up to **1,100x speedup** over CPU-only baselines with no cloud dependency.

| Uno Q Component | Role | NGC Quantum Contribution |
|---|---|---|
| STM32U585 MCU | Real-time sensor ingestion | Basic PSMSL anomaly detection |
| Cortex-A53 (Linux) | Intelligence Layer orchestration | GeoFlow pipeline management |
| **Adreno 702 GPU** | **Edge quantum acceleration** | **GF(48) packed kernels — Grover's search, hyperspectral fusion, curvature analysis** |

The Leibniz-Bocker curvature metric ($\Omega$) produced by the GPU forms the mathematically provable basis for the **Proof of Stewardship** report, signed by the Auditor Container for the Carbon-Plus bond market.

### The Auditor Container

Every sensor reading and actuator command is cryptographically signed using a private key stored in the node's secure enclave. These records form an **immutable ledger of stewardship**.

This ledger is the foundation of the **"Proof of Stewardship" report** — the verified ecological data that financial institutions need to issue Carbon-Plus bonds, bypassing the legacy MRV industry entirely.

---

## Farm-to-Orbit

A farm operating in a high-variability, off-grid environment is mathematically identical to a lunar greenhouse. The same engineering constraints apply: extreme latency tolerance, resource scarcity management, zero dependency on external infrastructure, and cryptographically verifiable operational data.

Every hour a Sovereign Node spends in a field is a stress test that validates its readiness for off-earth deployment. SAIS is being built for the farm. It is being designed for orbit.

---

## Repository Structure

```
sais/
├── docs/
│   ├── ARCHITECTURE.md               # Full system architecture reference
│   ├── STRATEGIC_VISION.md           # Farm-to-Orbit strategic vision document
│   ├── HARDWARE_SPEC.md              # Hardware BOM and enclosure spec (UNO Q focus)
│   ├── SCADA_SECURITY_SPEC.md        # NASA Life-Support Grade security spec
│   ├── INTELLIGENCE_LAYER.md         # Edge AI, RAG, and On-Device LLM design
│   ├── DRONE_SWARM_CAPABILITIES.md   # Ultrasonic echolocation swarm architecture
│   ├── ADAPTIVE_AUDIO_INTEGRATION.md # PSMSL Adaptive Engine integration plan
│   ├── NGC_INTEGRATION_PLAN.md       # NGC GeoFlow kernel integration plan
│   ├── NGC_QUANTUM_INTEGRATION.md    # GF(48) quantum-inspired Adreno GPU integration
│   └── STRATEGIC_INTEGRATION_ASSESSMENT.md  # Full ecosystem audit (48 repos)
├── firmware/
│   ├── components/
│   │   └── adaptive-engine/          # PSMSL core for structural/acoustic analysis
│   └── README.md
├── hardware/                         # Enclosure designs, PCB schematics, BOM
├── software/                         # Containerized software stack
├── scripts/                          # Deployment, provisioning, and OTA scripts
├── CONTRIBUTING.md                   # How to contribute
├── CODE_OF_CONDUCT.md                # Community standards
├── SECURITY.md                       # Security policy and responsible disclosure
└── LICENSE                           # GNU AGPL v3
```

---

## Engineering Roadmap

### Sprint 1: "Iron" — Gateway Hardware
**Deliverable:** A prototype Sovereign Node (UNO Q) in an IP67 enclosure, validated for 30 days of continuous off-grid operation.

### Sprint 2: "Plumbing" — DDS/MQTT Mesh
**Deliverable:** A functional mesh of three Sovereign Nodes communicating without a server, surviving a complete network blackout, and autonomously executing an irrigation cycle.

### Sprint 3: "Sovereignty" — The Auditor Container
**Deliverable:** A locally hosted C2 Dashboard rendering a cryptographically signed "Proof of Stewardship" report from live node data.

---

## Contributing

SAIS is an open project. Contributions are welcome across all layers: firmware, hardware design, containerized software, documentation, and protocol specification.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before submitting a pull request.

---

## License

SAIS is released under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This means any derivative work — including network-deployed services — must also be released under the same license. This is a deliberate choice: it prevents corporations from taking the open-source core, wrapping it in a proprietary service, and selling it back to the farmers it was built to liberate.

See [`LICENSE`](LICENSE) for the full text.

---

*Nathanael J. Bocker, 2026 all rights reserved*
