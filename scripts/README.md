# SAIS Scripts — Deployment, Provisioning, and Operations

This directory contains scripts for deploying, provisioning, and operating Sovereign Nodes and Sovereign Meshes.

## Planned Scripts

| Script | Purpose |
|---|---|
| `provision-node.sh` | Initial node provisioning: generate cryptographic identity, configure secure enclave, set node metadata |
| `deploy-stack.sh` | Deploy the full containerized software stack to a node |
| `update-node.sh` | Trigger an OTA update on one or more nodes in the mesh |
| `generate-report.sh` | Manually trigger a Proof of Stewardship report from a node |
| `mesh-status.sh` | Display the health and connectivity status of all nodes in a mesh |
| `export-ledger.sh` | Export the cryptographic audit ledger from a node for external verification |
| `backup-node.sh` | Back up node configuration and audit ledger to an encrypted archive |

## Usage Philosophy

All scripts are designed to be:

- **Idempotent:** Running a script multiple times produces the same result as running it once.
- **Non-destructive by default:** Scripts that modify node state require explicit confirmation flags.
- **Auditable:** All script actions that modify node state are logged to the audit ledger.
- **Offline-capable:** Scripts operate over the local LAN/mesh and do not require internet connectivity.

## Contributing

See the root [`CONTRIBUTING.md`](../CONTRIBUTING.md). Scripts must be POSIX-compliant shell (bash 4+) and include inline documentation for all parameters and expected behaviors.

---

*Nathanael J. Bocker, 2026 all rights reserved*
