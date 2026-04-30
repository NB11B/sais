# SAIS Software — Containerized SCADA/Compute Stack

This directory contains the containerized software stack for the **SCADA/Compute Layer** of the Sovereign Node, running on the NXP i.MX 8M (or equivalent industrial SBC) under Linux.

## Container Architecture

Each logical function runs in its own isolated, locked-down OCI container. A failure or compromise of one container cannot propagate to others.

| Container | Image | Function |
|---|---|---|
| `sais-broker` | `sais/broker` | Local MQTT broker (Eclipse Mosquitto) for intra-node message routing |
| `sais-dds` | `sais/dds` | DDS middleware (Eclipse Cyclone DDS) for inter-node mesh communication |
| `sais-oada` | `sais/oada` | OADA-compliant REST API server exposing node data to authorized consumers |
| `sais-auditor` | `sais/auditor` | Cryptographic signing pipeline and immutable ledger management |
| `sais-dashboard` | `sais/dashboard` | C2 Dashboard — local web interface for operator monitoring and control |
| `sais-ota` | `sais/ota` | OTA update agent for firmware and container image management |

## Stack

- **Container Runtime:** containerd (preferred) or Docker
- **Orchestration:** Docker Compose (single-node) / k3s (multi-node, future)
- **Languages:** Python 3.11+, Rust (auditor and cryptographic components), TypeScript (dashboard)
- **MQTT Broker:** Eclipse Mosquitto
- **DDS:** Eclipse Cyclone DDS + Micro XRCE-DDS (for LoRa bridge)
- **Database:** SQLite (audit ledger, local configuration) — no external database dependencies

## Getting Started

```bash
# Prerequisites: Docker or containerd, docker-compose

cd software/

# Build all containers
docker compose build

# Start the stack
docker compose up -d

# Access the C2 Dashboard
# Open http://[node-ip]:8080 in a browser on the local network
```

## Directory Structure (Planned)

```
software/
├── broker/             # Eclipse Mosquitto configuration and container definition
├── dds/                # Cyclone DDS configuration, OADA topic mappings, QoS profiles
├── oada/               # OADA API server (Python/FastAPI)
├── auditor/            # Cryptographic signing pipeline and ledger (Rust)
├── dashboard/          # C2 Dashboard web application (TypeScript/React)
├── ota/                # OTA update agent (Python)
├── docker-compose.yml  # Full stack composition
└── .env.example        # Environment variable template
```

## Security Notes

- All containers run with **minimal Linux capabilities**. No privileged containers.
- The `sais-auditor` container communicates with the ARM TrustZone secure enclave via the kernel's TEE driver. The private key is never loaded into the container's memory space.
- The `sais-dashboard` and `sais-oada` containers bind only to the local network interface by default. WAN exposure requires explicit operator configuration.
- All inter-container communication uses the internal Docker/containerd network. No container exposes unnecessary ports to the host.

## Contributing

See the root [`CONTRIBUTING.md`](../CONTRIBUTING.md). For software contributions, please include unit tests and define the resource budget (CPU, RAM, storage) for any new container.

---

*Nathanael J. Bocker, 2026 all rights reserved*
