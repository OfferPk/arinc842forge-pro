# RTCA DO-355 & DO-326A Airworthiness Security Compliance Matrix

**Product**: ARINC842Forge Pro v1.0.0  
**Auditor Module**: `source-code/arinc842-auditor.js`  
**Standard Coverage**: RTCA DO-355, RTCA DO-326A, ARINC 842, FAA AC 119-1, EASA ED-204A

| Item \# | Audit Verification Check | Regulatory Standard | Security Objective | Engine Implementation Status |
| :---: | :---- | :---- | :---- | :---: |
| **CHK-01** | Weight-on-Wheels (WOW) Hardware Inhibit | ARINC 842 §4.1 / FAR 25.1309 | Inhibit RF transmission while airborne | **PASS (Hardware Interlock Verified)** |
| **CHK-02** | Ground Speed Limiting Threshold (\<15 kt / 0 kt) | ARINC 842 §4.2 | Inhibit bulk uploads during active high-speed taxi | **PASS (Ground Speed Interlock Verified)** |
| **CHK-03** | 802.1X EAP-TLS Mutual PKI Authentication | RTCA DO-355 §3.2 / RFC 5216 | Prevent rogue airport AP spoofing & MITM | **PASS (RSA-4096 / SHA-384 Chain Verified)** |
| **CHK-04** | IPsec ESP AES-256-GCM Tunnel Encryption | RTCA DO-355 §3.3 / FIPS 197 | Cryptographic confidentiality & tamper prevention | **PASS (AES-256-GCM & ESP Tunnel Active)** |
| **CHK-05** | Aircraft Control Domain (ACD) Network Isolation | RTCA DO-355 §3.4 / DO-326A | Strict firewall isolation of flight critical bus | **PASS (ACD Isolated; AISD Bound)** |
| **CHK-06** | ARINC 665 LSAP Digital Signature Verification | ARINC 665-5 / FAA AC 20-115D | Prevent corrupted or unapproved software loading | **PASS (SHA-256 Digest & Sig Verified)** |
| **CHK-07** | Automated Failover (802.11ac / 5G / Optical) | ARINC 842 §5.3 | Uninterrupted turn-around data offload | **PASS (Multi-Carrier Engine Verified)** |
| **CHK-08** | ARINC 429 Bit 32 Odd Parity Validation | ARINC 429-19 | Reject malformed or corrupted discrete words | **PASS (Labels 270 & 350 Parity Verified)** |
| **CHK-09** | Minimum SNR Threshold & Rate Adaptation | ARINC 842 §6.1 | Avoid packet loss and retransmissions | **PASS (Threshold ≥15 dB Enforced)** |
| **CHK-10** | Immutable FAA AC 119-1 Airworthiness Audit Trail | FAA AC 119-1 §7 / DO-355 | Continuous forensics for cyber airworthiness | **PASS (Cryptographic Log Export Active)** |

**Normative Compliance Score**: 10/10 Checks Passed (100.0% Normative Conformance)