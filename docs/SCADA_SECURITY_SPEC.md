# SAIS SCADA Standards & Security Specification

**Version:** 0.2.0-draft
**Status:** Active Development
**Designation:** Tier 1 Critical Infrastructure / Life Support Grade

---

## Overview

The Sovereign Ag-Infrastructure Stack (SAIS) is designed to operate as **Tier 1 Critical Infrastructure**. Because the SAIS architecture is designed to scale from terrestrial agriculture to closed-loop orbital habitats (the "Farm-to-Orbit" thesis), its security and reliability requirements exceed standard industrial IoT.

SAIS security and functional safety are mapped directly against the most stringent international standards for aerospace and critical infrastructure: **DO-178C (Airborne Software)**, **IEC 61508 SIL 4 (Functional Safety)**, **NASA-STD-8739.8 (Software Assurance)**, and **IEC 62443 (ICS Security)**.

This document defines the mandatory safety architecture, fault tolerance mechanisms, cryptographic standards, and network segmentation rules for all SAIS deployments.

---

## 1. Functional Safety & Aerospace Standards Compliance

SAIS architecture is designed to comply with the following life-support grade standards:

### 1.1 DO-178C (Software Considerations in Airborne Systems)
SAIS Controller Layer firmware targets **Design Assurance Level A (DAL A)** [1], the highest level of rigor, applied when software failure could cause a catastrophic failure condition (e.g., loss of life support).
- **Robust Partitioning:** The RTOS (Zephyr) must guarantee strict spatial (memory) and temporal (CPU time) partitioning between tasks to prevent cascading failures.
- **Traceability:** Every line of source code and object code must be traceable to a specific safety requirement.

### 1.2 IEC 61508 SIL 4 (Functional Safety)
SAIS targets **Safety Integrity Level 4 (SIL 4)** [2], the highest risk reduction level.
- **Hardware Fault Tolerance (HFT):** The system must tolerate at least one dangerous hardware fault without loss of the safety function.
- **Diagnostic Coverage:** The system must implement continuous self-diagnostics to detect latent faults before they become dangerous.

### 1.3 NASA-STD-8739.8 (Software Assurance and Safety)
SAIS adopts NASA's systematic approach to software safety [3]:
- **Hazard Analysis:** All software components are evaluated for their potential to cause or contribute to a system hazard.
- **Independent Verification & Validation (IV&V):** Safety-critical logic is verified independently of the development team.

---

## 2. Fault-Tolerant Architecture

To meet NASA ECLSS (Environmental Control and Life Support System) standards [4], SAIS implements rigorous fault detection, isolation, and recovery (FDIR) mechanisms.

### 2.1 Triple Modular Redundancy (TMR)
For critical control loops (e.g., oxygen generation, water recovery, or critical irrigation), SAIS supports **Triple Modular Redundancy (TMR)** at the Controller Layer [5].
- Three independent MCU cores (or three independent tasks on a robustly partitioned RTOS) compute the control output simultaneously.
- A hardware or software voter circuit compares the outputs. If one core disagrees, its output is masked, and the fault is logged.

### 2.2 Independent Hardware Watchdog
Software watchdogs are insufficient for life-support grade systems. SAIS mandates an **independent, external hardware watchdog timer** [6].
- The MCU must send a specific, cryptographically signed "heartbeat" sequence to the external watchdog at precise intervals.
- If the MCU hangs, enters an infinite loop, or sends an incorrect sequence, the hardware watchdog physically cuts power to the MCU and forces a hard reset.

### 2.3 Safe State Fallback
If the Controller Layer experiences an unrecoverable fault, all physical actuators (valves, pumps, relays) must default to a **mechanically defined safe state** (e.g., normally closed valves) without requiring software intervention.

---

## 3. Network Architecture: The Purdue Model

SAIS enforces a strict interpretation of the **Purdue Enterprise Reference Architecture (PERA)** [7], adapted for edge-native deployments.

| Purdue Level | SAIS Component | Trust Level | Security Controls |
|---|---|---|---|
| **Level 0 (Physical Process)** | Sensors, Actuators, Motors | Implicit Trust (Physical) | Physical tamper evidence, IP67 enclosures |
| **Level 1 (Basic Control)** | Controller Layer (STM32U585 MCU) | High Trust (Real-Time) | Zephyr RTOS, deterministic execution, no external network access |
| **Level 2 (Supervisory Control)** | SCADA/Compute Layer (QRB2210 MPU) | Medium Trust (Local) | Debian Linux, Docker/k3s, local MQTT broker, DDS middleware |
| **Level 3 (Site Operations)** | Local Mesh (LoRa / Wi-Fi) | Low Trust (Encrypted) | Mutual TLS 1.3, AES-256-GCM, certificate-based auth |
| **Level 4/5 (Enterprise/Cloud)** | C2 Dashboard / Auditor Container | Zero Trust | ZKP verification, OADA API, outbound-only connections |

**Critical Rule:** Level 1 (Controller Layer) **never** connects directly to Level 4/5 (Cloud). All external communication must pass through the Level 2 (Compute Layer) conduit.

---

## 4. Cryptographic Standards

SAIS mandates modern, quantum-resistant-capable cryptographic primitives. Legacy protocols (TLS 1.1, SSL, SHA-1, MD5) are strictly prohibited at the compiler level.

### 4.1 Data in Transit (Conduits)
- **Protocol:** TLS 1.3 is mandatory for all IP-based communication [8].
- **Authentication:** Mutual TLS (mTLS) using X.509 certificates. Both the client and the server must cryptographically prove their identity before a connection is established.
- **Cipher Suites:** AES-256-GCM or ChaCha20-Poly1305.
- **LoRa Mesh:** For non-IP LoRa communication, payloads are encrypted using AES-128-CTR with rotating session keys derived from a pre-shared master key.

### 4.2 Data at Rest
- **Storage Encryption:** The eMMC storage on the Compute Layer must be encrypted using LUKS (Linux Unified Key Setup) with AES-256-XTS.
- **Key Storage:** Cryptographic keys must be stored in a hardware secure enclave. On the UNO Q, this is handled by the STM32U585 TrustZone [9]. On the i.MX 8M, it is handled by the ARM TrustZone.

---

## 5. Firmware Security & OTA Updates

OTA updates are the most critical vulnerability vector in edge IoT [10]. SAIS implements a secure OTA pipeline designed to prevent "bricking" in remote or orbital environments.

### 5.1 Secure Boot
Secure Boot is mandatory for all SAIS production nodes.
- **Mechanism:** The bootloader (e.g., MCUboot for Zephyr [11]) verifies the cryptographic signature of the firmware image before execution.
- **Failure State:** If the signature is invalid, the device halts and enters a secure recovery mode. It will not boot compromised code.

### 5.2 A/B Partitioning and Automatic Rollback
- **Signed Payloads:** All firmware and container updates must be cryptographically signed by the SAIS deployment authority.
- **A/B Partitioning:** Updates are written to an inactive partition. The bootloader verifies the signature, boots from the new partition, and monitors for crashes.
- **Automatic Rollback:** If the new firmware fails to initialize the watchdog timer within 60 seconds, the bootloader automatically rolls back to the known-good partition.

---

## 6. Zero-Trust Micro-Segmentation

SAIS assumes that the network is always hostile. The Compute Layer implements **Zero-Trust Micro-Segmentation** [12]:
- **Container Isolation:** Every service (MQTT broker, DDS node, Auditor, NGC engine) runs in an isolated container with a read-only root filesystem.
- **Network Policies:** Containers can only communicate with explicitly whitelisted peers. For example, the Auditor Container can read from the MQTT broker but cannot access the external internet directly.
- **No Inbound Ports:** The Sovereign Node does not expose any listening ports to the external internet. All C2 communication is established via outbound, persistent, mutually authenticated tunnels (e.g., WireGuard or Cloudflare Tunnels).

---

## 7. References

[1] Wikipedia, "DO-178C," *wikipedia.org*. [Online]. Available: https://en.wikipedia.org/wiki/DO-178C
[2] Wikipedia, "IEC 61508," *wikipedia.org*. [Online]. Available: https://en.wikipedia.org/wiki/IEC_61508
[3] NASA, "Software Assurance and Software Safety Standard," *standards.nasa.gov*. [Online]. Available: https://standards.nasa.gov/standard/NASA/NASA-STD-87398
[4] NASA, "Environmental Control and Life Support Systems (ECLSS)," *nasa.gov*. [Online]. Available: https://www.nasa.gov/reference/environmental-control-and-life-support-systems-eclss/
[5] NASA, "Software Triple Redundancy," *llis.nasa.gov*. [Online]. Available: https://llis.nasa.gov/lesson/18803
[6] NASA, "Redundant Verification of Critical Command Timing," *llis.nasa.gov*. [Online]. Available: https://llis.nasa.gov/lesson/559
[7] Fortinet, "What Is the Purdue Model for ICS Security?," *fortinet.com*. [Online]. Available: https://www.fortinet.com/resources/cyberglossary/purdue-model
[8] eMudhra, "TLS for IoT & Smart Infrastructure," *emudhra.com*. [Online]. Available: https://emudhra.com/en-us/blog/tls-and-iot-security-safeguarding-connected-devices-in-the-uae-with-emudhra
[9] STMicroelectronics, "Secure boot solution for STM32U5 on Zephyr," *community.st.com*. [Online]. Available: https://community.st.com/t5/stm32-mcus-embedded-software/secure-boot-solution-for-stm32u5-on-zephyr/td-p/818075
[10] Mender, "Over-the-air (OTA) update best practices for industrial IoT," *mender.io*. [Online]. Available: https://mender.io/resources/reports-and-guides/ota-updates-best-practices
[11] Zephyr Project, "MCUboot Security Part 1," *zephyrproject.org*. [Online]. Available: https://www.zephyrproject.org/mcuboot-security-part-1/
[12] Zero Networks, "What is Microsegmentation? The Ultimate Guide to Zero Trust," *zeronetworks.com*. [Online]. Available: https://zeronetworks.com/blog/what-is-microsegmentation-our-definitive-guide

---

*Nathanael J. Bocker, 2026 all rights reserved*
