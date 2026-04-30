# SAIS SCADA Standards & Security Specification

**Version:** 0.1.0-draft
**Status:** Active Development

---

## Overview

The Sovereign Ag-Infrastructure Stack (SAIS) is designed to operate as **Tier 1 Critical Infrastructure**. While its primary application is agricultural, the architecture assumes that the compromise of a Sovereign Node could result in catastrophic physical damage (e.g., destruction of crops, flooding, or life-support failure in closed-loop environments).

Therefore, SAIS security is not treated as "IoT security." It is treated as **Industrial Control System (ICS) security**, mapped directly against the most stringent international standards for critical infrastructure: **IEC 62443**, **NIST SP 800-82 Rev 3**, and **NERC CIP**.

This document defines the mandatory security architecture, cryptographic standards, and network segmentation rules for all SAIS deployments.

---

## 1. Standards Compliance Mapping

SAIS architecture is designed to comply with the following critical infrastructure standards:

### 1.1 IEC 62443 (Industrial Communication Networks)
IEC 62443 is the definitive international standard for ICS security [1]. SAIS implements the core tenets of this standard:
- **Zones and Conduits (IEC 62443-3-2):** The network is strictly segmented into trust zones. Communication between zones is only permitted through defined, encrypted conduits.
- **Security Levels (IEC 62443-3-3):** SAIS targets **Security Level 3 (SL 3)** by default: protection against intentional violation using sophisticated means, extended resources, and ICS-specific skills.

### 1.2 NIST SP 800-82 Rev 3 (Guide to OT Security)
NIST SP 800-82 provides the framework for securing Operational Technology (OT) [2]. SAIS adheres to its primary directives:
- **Separation of IT and OT:** The SAIS Controller Layer (OT) is physically and logically isolated from external networks.
- **Least Privilege:** Containers and RTOS tasks operate with the absolute minimum permissions required.
- **Secure Remote Access:** All remote C2 dashboard access requires mutual authentication and encrypted tunnels.

### 1.3 NERC CIP (Critical Infrastructure Protection)
While NERC CIP is specific to the North American bulk power system [3], SAIS adopts its rigorous requirements for **Electronic Security Perimeters (CIP-005)** and **Systems Security Management (CIP-007)**, ensuring that SAIS nodes could theoretically be deployed in power grid applications without architectural changes.

---

## 2. Network Architecture: The Purdue Model

SAIS enforces a strict interpretation of the **Purdue Enterprise Reference Architecture (PERA)** [4], adapted for edge-native deployments.

| Purdue Level | SAIS Component | Trust Level | Security Controls |
|---|---|---|---|
| **Level 0 (Physical Process)** | Sensors, Actuators, Motors | Implicit Trust (Physical) | Physical tamper evidence, IP67 enclosures |
| **Level 1 (Basic Control)** | Controller Layer (STM32U585 MCU) | High Trust (Real-Time) | Zephyr RTOS, deterministic execution, no external network access |
| **Level 2 (Supervisory Control)** | SCADA/Compute Layer (QRB2210 MPU) | Medium Trust (Local) | Debian Linux, Docker/k3s, local MQTT broker, DDS middleware |
| **Level 3 (Site Operations)** | Local Mesh (LoRa / Wi-Fi) | Low Trust (Encrypted) | Mutual TLS 1.3, AES-256-GCM, certificate-based auth |
| **Level 4/5 (Enterprise/Cloud)** | C2 Dashboard / Auditor Container | Zero Trust | ZKP verification, OADA API, outbound-only connections |

**Critical Rule:** Level 1 (Controller Layer) **never** connects directly to Level 4/5 (Cloud). All external communication must pass through the Level 2 (Compute Layer) conduit.

---

## 3. Cryptographic Standards

SAIS mandates modern, quantum-resistant-capable cryptographic primitives. Legacy protocols (TLS 1.1, SSL, SHA-1, MD5) are strictly prohibited at the compiler level.

### 3.1 Data in Transit (Conduits)
- **Protocol:** TLS 1.3 is mandatory for all IP-based communication [5].
- **Authentication:** Mutual TLS (mTLS) using X.509 certificates. Both the client and the server must cryptographically prove their identity before a connection is established.
- **Cipher Suites:** AES-256-GCM or ChaCha20-Poly1305.
- **LoRa Mesh:** For non-IP LoRa communication, payloads are encrypted using AES-128-CTR with rotating session keys derived from a pre-shared master key.

### 3.2 Data at Rest
- **Storage Encryption:** The eMMC storage on the Compute Layer must be encrypted using LUKS (Linux Unified Key Setup) with AES-256-XTS.
- **Key Storage:** Cryptographic keys must be stored in a hardware secure enclave. On the UNO Q, this is handled by the STM32U585 TrustZone [6]. On the i.MX 8M, it is handled by the ARM TrustZone.

---

## 4. Hardware and Firmware Security

### 4.1 Secure Boot
Secure Boot is mandatory for all SAIS production nodes.
- **Mechanism:** The bootloader (e.g., MCUboot for Zephyr [7]) verifies the cryptographic signature of the firmware image before execution.
- **Failure State:** If the signature is invalid, the device halts and enters a secure recovery mode. It will not boot compromised code.

### 4.2 Over-The-Air (OTA) Updates
OTA updates are the most critical vulnerability vector in edge IoT [8]. SAIS implements a secure OTA pipeline:
- **Signed Payloads:** All firmware and container updates must be cryptographically signed by the SAIS deployment authority.
- **A/B Partitioning:** Updates are written to an inactive partition. The bootloader verifies the signature, boots from the new partition, and monitors for crashes.
- **Automatic Rollback:** If the new firmware fails to initialize the watchdog timer within 60 seconds, the bootloader automatically rolls back to the known-good partition.

---

## 5. Zero-Trust Micro-Segmentation

SAIS assumes that the network is always hostile. The Compute Layer implements **Zero-Trust Micro-Segmentation** [9]:
- **Container Isolation:** Every service (MQTT broker, DDS node, Auditor, NGC engine) runs in an isolated container with a read-only root filesystem.
- **Network Policies:** Containers can only communicate with explicitly whitelisted peers. For example, the Auditor Container can read from the MQTT broker but cannot access the external internet directly.
- **No Inbound Ports:** The Sovereign Node does not expose any listening ports to the external internet. All C2 communication is established via outbound, persistent, mutually authenticated tunnels (e.g., WireGuard or Cloudflare Tunnels).

---

## 6. References

[1] IEC, "IEC 62443: Industrial communication networks - Network and system security," *iec.ch*. [Online]. Available: https://en.wikipedia.org/wiki/IEC_62443
[2] NIST, "SP 800-82 Rev. 3, Guide to Operational Technology (OT) Security," *csrc.nist.gov*. [Online]. Available: https://csrc.nist.gov/pubs/sp/800/82/r3/final
[3] NERC, "North American Electric Reliability Corporation," *nerc.com*. [Online]. Available: https://www.nerc.com/
[4] Fortinet, "What Is the Purdue Model for ICS Security?," *fortinet.com*. [Online]. Available: https://www.fortinet.com/resources/cyberglossary/purdue-model
[5] eMudhra, "TLS for IoT & Smart Infrastructure," *emudhra.com*. [Online]. Available: https://emudhra.com/en-us/blog/tls-and-iot-security-safeguarding-connected-devices-in-the-uae-with-emudhra
[6] STMicroelectronics, "Secure boot solution for STM32U5 on Zephyr," *community.st.com*. [Online]. Available: https://community.st.com/t5/stm32-mcus-embedded-software/secure-boot-solution-for-stm32u5-on-zephyr/td-p/818075
[7] Zephyr Project, "MCUboot Security Part 1," *zephyrproject.org*. [Online]. Available: https://www.zephyrproject.org/mcuboot-security-part-1/
[8] Mender, "Over-the-air (OTA) update best practices for industrial IoT," *mender.io*. [Online]. Available: https://mender.io/resources/reports-and-guides/ota-updates-best-practices
[9] Zero Networks, "What is Microsegmentation? The Ultimate Guide to Zero Trust," *zeronetworks.com*. [Online]. Available: https://zeronetworks.com/blog/what-is-microsegmentation-our-definitive-guide

---

*Nathanael J. Bocker, 2026 all rights reserved*
