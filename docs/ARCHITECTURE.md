# SAIS System Architecture Reference

**Version:** 0.1.0-draft
**Status:** Active Development

---

## Overview

The Sovereign Ag-Infrastructure Stack (SAIS) is a federated, edge-native system. Its fundamental architectural unit is the **Sovereign Node** — a self-contained, solar-powered edge controller that manages a closed-loop resource environment (farm, ranch, habitat) without any dependency on external WAN connectivity or cloud services.

Multiple nodes form a **Sovereign Mesh** — a peer-to-peer network that operates autonomously as a collective, with no central broker or coordinator.

---

## Design Constraints

All architectural decisions are subordinate to four inviolable constraints:

| Constraint | Definition |
|---|---|
| **Resilience** | Zero percent dependency on external WAN or cloud infrastructure. The system must function indefinitely in a fully disconnected state. |
| **Autonomy** | Deterministic, real-time control of physical actuators must never be interrupted by software failures in the intelligence layer. |
| **Sovereignty** | Operational data is stored and processed locally. No raw data leaves the node without explicit operator authorization. |
| **Verifiability** | All operational events are cryptographically signed and timestamped, creating an immutable, auditable record of system state. |

---

## Node Architecture

### Layer 1: Controller Layer (Real-Time)

**Hardware:** Espressif ESP32-S3 (or equivalent RTOS-capable microcontroller)

**Operating System:** FreeRTOS

**Responsibilities:**
- High-frequency sensor polling (soil moisture, temperature, flow rate, livestock proximity, atmospheric sensors)
- Deterministic actuator control (gate motors, irrigation valves, nutrient pumps, lighting)
- Pre-programmed automation sequence execution (irrigation schedules, feeding cycles)
- Watchdog timer management — the Controller Layer must never halt

**Key Design Requirement:** The Controller Layer operates completely independently of the SCADA/Compute Layer. It communicates with the intelligence layer via a defined serial/SPI interface, but it does not depend on it. If the SCADA/Compute Layer crashes, reboots, or is being updated, the Controller Layer continues executing its automation sequences without interruption.

**Interface to Layer 2:** UART/SPI bridge with a defined message schema. The Controller Layer publishes sensor readings and accepts actuator commands. It does not expose any network interface.

---

### Layer 2: SCADA/Compute Layer (Intelligence)

**Hardware:** NXP i.MX 8M (or equivalent industrial-grade SBC)

**Operating System:** Linux (containerized)

**Storage:** Industrial eMMC (minimum 32 GB). SD cards are explicitly prohibited due to their failure rate under continuous write cycles.

**Container Runtime:** containerd or equivalent lightweight OCI-compatible runtime

**Containers:**

| Container | Function |
|---|---|
| `sais-broker` | Local MQTT broker for intra-node sensor/actuator message routing |
| `sais-dds` | DDS middleware (Eclipse Cyclone DDS or RTI Connext) for inter-node mesh communication |
| `sais-oada` | OADA API server — exposes node data in OADA-compliant format for authorized consumers |
| `sais-auditor` | Cryptographic signing pipeline — signs all operational events and maintains the immutable ledger |
| `sais-dashboard` | C2 Dashboard — local web interface for operator monitoring and control |
| `sais-ota` | OTA update agent — manages signed firmware and container image updates |

**Secure Enclave:** ARM TrustZone on the i.MX 8M is used to store the node's cryptographic private key. The key is never exposed to the application layer. All signing operations are performed inside the secure enclave.

---

### Physical Enclosure

| Specification | Requirement |
|---|---|
| **IP Rating** | IP67 (dust-tight, waterproof to 1 m for 30 min) |
| **Thermal Management** | Fanless; die-cast chassis acts as passive heat sink |
| **Operating Temperature** | −30°C to +70°C (industrial grade) |
| **Mounting** | DIN rail, fence post, or surface mount |
| **Power Input** | 12–48V DC (solar + battery compatible) |
| **Connectors** | Industrial M12 circular connectors (IP67-rated) |

---

### Power Architecture

Each node is designed for indefinite off-grid operation:

- **Solar Input:** 12V or 24V solar panel array (sizing depends on load profile)
- **Battery:** LiFePO4 chemistry (preferred for cycle life and thermal stability)
- **Power Management:** MPPT charge controller with load output control
- **Power Budget:** The Controller Layer (ESP32-S3) draws < 500 mW. The SCADA/Compute Layer (i.MX 8M) draws 3–8 W depending on load. Total node power budget: < 15 W under full operation.
- **Sleep/Wake:** The SCADA/Compute Layer implements configurable sleep/wake cycles to reduce power consumption during low-activity periods. The Controller Layer remains active at all times.

---

## Mesh Architecture

### Communication Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│         (OADA API, C2 Dashboard, Auditor Reports)        │
├─────────────────────────────────────────────────────────┤
│                   DDS Data Space                         │
│         (Peer-to-peer, broker-less, QoS-managed)         │
├─────────────────────────────────────────────────────────┤
│              Transport Layer (per link type)             │
│   Wi-Fi (local, high-bandwidth) │ LoRa (long-range)      │
├─────────────────────────────────────────────────────────┤
│              Physical Layer                              │
│   802.11 b/g/n/ac              │ LoRa 868/915 MHz        │
└─────────────────────────────────────────────────────────┘
```

### DDS Configuration

SAIS uses **Eclipse Cyclone DDS** as the default DDS implementation for the SCADA/Compute Layer. For LoRa transport segments, **Micro XRCE-DDS** bridges the resource-constrained LoRa link to the full DDS data space.

**DDS Domains:** Each farm or habitat deployment operates within a single DDS domain. Nodes within the domain discover each other automatically via the DDS Simple Discovery Protocol (SDP). No manual configuration of peer addresses is required.

**QoS Profiles:**

| Profile | Reliability | Durability | Use Case |
|---|---|---|---|
| `sensor_telemetry` | BEST_EFFORT | VOLATILE | High-frequency sensor data |
| `actuator_command` | RELIABLE | VOLATILE | Actuator control commands |
| `audit_record` | RELIABLE | TRANSIENT_LOCAL | Cryptographic audit events |
| `system_health` | RELIABLE | TRANSIENT_LOCAL | Node health and status |

### OADA Integration

All node data is exposed via an OADA-compliant REST API served by the `sais-oada` container. This API is accessible only on the local LAN/mesh. External access requires explicit operator configuration (VPN or similar).

OADA data types used:
- `application/vnd.oada.sensor.1+json` — sensor readings
- `application/vnd.oada.event.1+json` — actuator events
- `application/vnd.oada.audit.1+json` — cryptographic audit records (SAIS extension)

---

## Cryptographic Auditor

### Signing Pipeline

Every operational event (sensor reading, actuator command, automation decision) passes through the following pipeline:

```
Event Generated
      │
      ▼
Serialize to canonical JSON (deterministic field ordering)
      │
      ▼
Hash with SHA-256
      │
      ▼
Sign hash with node private key (inside ARM TrustZone)
      │
      ▼
Append to audit ledger: { timestamp, event_type, payload_hash, signature, prev_record_hash }
      │
      ▼
Store in append-only local database
```

The `prev_record_hash` field chains each record to the previous one, making the ledger tamper-evident. Any modification to a historical record invalidates all subsequent records in the chain.

### Proof of Stewardship Report

The `sais-auditor` container periodically generates a **Proof of Stewardship** report — a structured document containing:

- A summary of operational events over the reporting period
- Aggregated sensor statistics (soil health, water usage, input quantities)
- A cryptographic proof that the ledger has not been tampered with
- The node's public key and certificate for independent verification

This report is designed to meet the evidentiary requirements of carbon credit MRV standards and can be submitted directly to ecological finance instruments without requiring a third-party auditor.

---

## OTA Update Architecture

The `sais-ota` container manages all software updates:

1. **Firmware updates (ESP32-S3):** Signed binary packages are delivered to the SCADA/Compute Layer and flashed to the Controller Layer via the defined serial interface. The Controller Layer validates the signature before applying the update and maintains a rollback partition.
2. **Container image updates:** New container images are pulled, verified against a signed manifest, and applied atomically. If the new container fails its health check, the previous version is automatically restored.
3. **Update delivery:** Updates can be delivered via local LAN (operator-initiated), mesh propagation (node-to-node), or direct connection when WAN is available. All update packages are signed by the project's release key and verified before installation.

---

## Security Architecture

| Threat | Mitigation |
|---|---|
| Physical node compromise | Tamper-evident enclosure; private key in TrustZone secure enclave; key never exposed to application layer |
| Network eavesdropping | DDS DTLS transport security; all inter-node communication encrypted |
| Unauthorized actuator control | Controller Layer only accepts commands from authenticated SCADA/Compute Layer via local interface |
| Audit record forgery | Append-only ledger; hash-chained records; signatures verified against node public key |
| Malicious OTA update | All updates signed by release key; signature verified before installation; automatic rollback on failure |
| Container escape | Containers run with minimal privileges; seccomp profiles applied; no privileged containers |

---

## Aerospace Applicability

The SAIS architecture is designed to be directly applicable to off-earth habitat life-support systems. The mapping is as follows:

| SAIS Component | Aerospace Equivalent |
|---|---|
| Sovereign Node | Habitat subsystem controller |
| Controller Layer (RTOS) | Life-support actuator controller |
| SCADA/Compute Layer | Habitat management computer |
| DDS Mesh | Habitat internal data bus |
| Auditor Container | Mission safety monitor / flight recorder |
| Proof of Stewardship | Mission safety certification log |
| C2 Dashboard | Habitat operator interface |

Every hour of field operation accumulates validated operational data that directly supports aerospace certification processes.

---

*Nathanael J. Bocker, 2026 all rights reserved*
