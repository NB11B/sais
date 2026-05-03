# Security Policy

## Scope

The SAIS security policy covers all components of the Sovereign Ag-Infrastructure Stack, including:

- ESP32-S3 RTOS firmware (Controller Layer)
- NXP i.MX 8M containerized software stack (SCADA/Compute Layer)
- DDS/OADA communication protocol implementation
- Cryptographic Auditor Container and ZKP signing pipeline
- C2 Dashboard and local web interface
- OTA update mechanism

## Current Implementation Status

| Area | Current | Target | Status |
|---|---|---|---|
| Network binding | Default localhost, explicit `SAIS_BIND_LAN=true` for LAN | Same | ✅ Implemented |
| Request limits | 1 MB body limit, CORS restricted, security headers | Same | ✅ Implemented |
| Admin access | Bearer token for all mutating routes | RBAC + sessions | 🟡 Basic |
| Payload validation | Pydantic schemas with ID regex, timestamp skew, numeric bounds, GeoJSON limits | Same + canonical signing | ✅ Implemented |
| XSS prevention | Safe DOM construction (textContent) on all dashboard templates | Same | ✅ Implemented |
| Node identity | Pending registry, quarantine (no card gen for unaccepted) | Signed node certs | 🟡 Partial |
| Telemetry integrity | Admin token gate, quarantine for unaccepted nodes | Signed canonical JSON, sequence counters | 🔴 Not hardened |
| Audit log | Normal SQLite rows | Hash-chained append-only signed ledger | 🔴 Not hardened |
| Actuators | Not implemented | Field-safe authorization with operator confirmation | ⬜ Blocked |

## Security Design Principles

> **The following describes the target architecture.** See the status table above for what is currently implemented in the codebase.

SAIS is designed with security as a structural property, not a feature layer:

- **Cryptographic identity at the hardware level:** Each node's private key is stored in the ARM TrustZone secure enclave on the i.MX 8M. Keys are never exposed to the application layer.
- **Container isolation:** Each logical function runs in an isolated container. A compromise of one container cannot directly propagate to others.
- **No external attack surface by default:** The node exposes no services to the WAN. The C2 Dashboard is accessible only on the local LAN/mesh. External access requires explicit operator configuration.
- **Immutable audit log:** The cryptographic ledger is append-only and tamper-evident. Any attempt to modify historical records will invalidate the chain of signatures.
- **OTA integrity verification:** All firmware and container updates are signed and verified before installation. An update with an invalid signature is rejected and the node continues operating on the current version.

## Supported Versions

As SAIS is in active development, security patches are applied to the `main` branch. Once stable releases are tagged, this policy will be updated to reflect supported version ranges.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Security vulnerabilities in SAIS are particularly sensitive because the system controls physical actuators (pumps, gate motors, nutrient dosing systems) and manages cryptographic keys used for ecological financial instruments. A vulnerability in these systems could have real-world physical and financial consequences.

To report a vulnerability, please open a **GitHub Security Advisory** via the repository's Security tab. Include:

1. A clear description of the vulnerability and the affected component.
2. Steps to reproduce or a proof-of-concept (where safe to provide).
3. The potential impact (e.g., unauthorized actuator control, key extraction, data forgery).
4. Any suggested mitigations you have identified.

You will receive an acknowledgment within 72 hours. We aim to triage and respond to all reports within 14 days.

## Disclosure Policy

Once a vulnerability is confirmed and a fix is developed, SAIS will:

1. Release a patched version.
2. Publish a security advisory describing the vulnerability, its impact, and the fix.
3. Credit the reporter (unless they request anonymity).

We do not pursue legal action against researchers who report vulnerabilities in good faith and follow this policy.

---

*Nathanael J. Bocker, 2026 all rights reserved*
