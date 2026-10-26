# ARINC Project Paper 842 Wireless Airport Gatelink Communications (WAGC) Technical Specification

**Document ID**: ARINC842-SPEC-2026-v1.0  
**Normative References**: ARINC Project Paper 842, RTCA DO-355, RTCA DO-326A, FAA AC 119-1, EASA ED-204A  
**Classification**: Commercial Aircraft Avionics & Ground Systems Technical Standard

---

## 1\. Executive Summary & Operational Scope

The **ARINC Project Paper 842 (Wireless Airport Gatelink Communications \- WAGC)** defines standard protocols, RF architectures, physical interfaces, interlocks, and security boundaries enabling high-bandwidth commercial aircraft data exchange while parked at airport terminal gates or ramp stands.

Modern commercial aircraft generate upwards of 1.25 GB of flight operational quality assurance (FOQA) and Quick Access Recorder (QAR) telemetry per flight leg. Simultaneously, airline flight operations necessitate uploading multi-megabyte ARINC 665 Loadable Software Airplane Parts (LSAP), Flight Management System (FMS) navigation databases, Electronic Flight Bag (EFB) data revisions, and in-flight entertainment (IFE) operational media. ARINC 842 replaces physical umbilical cables with secure, autonomous gigabit wireless links.

---

## 2\. Mandatory Gate Safety Interlocks

In compliance with ARINC 842 and airframe airworthiness certification standards, the WAGC transceiver strictly implements triple-redundant safety interlocks to prevent high-power transmission or unauthorized avionics software changes during flight or active taxiing:

1. **Weight-on-Wheels (WOW) / Ground Sensing Switch**:  
   - Discrete hardware interlock wired to Main Landing Gear (MLG) squat switches.  
   - Any in-flight condition (WOW \= Airborne / 0\) immediately shuts down the WAGC transmitter and closes all IP tunnels.  
2. **Ground Speed Threshold Interlock**:  
   - Aircraft ground speed must remain strictly below 15.0 knots for initial ramp scanning and taxiway connection.  
   - For safety-critical software uploads (ARINC 665 LSAP to EEC/FMC), ground speed must be exactly 0.0 knots.  
3. **Parking Brake / Stand Proximity**:  
   - High-throughput bulk transfers require verified stand positioning (Gate Stanchion RF zone, range \< 15 meters) and parking brake engagement.

---

## 3\. Physical & Data Link Layer Specifications

ARINC 842 supports multi-carrier wireless and wired stanchion media:

- **Primary Wireless**: IEEE 802.11ac / 802.11ax operating in the 5 GHz U-NII aeronautical and commercial bands (Channels 36–165). Channel bandwidth: 20/40/80 MHz. MIMO 2x2 or 4x4.  
- **Secondary / Alternate Wireless**: Private Airport Cellular 5G NR Standalone (SA) in dedicated airport surface frequencies.  
- **Wired Stanchion Backup**: Gigabit Ethernet / Optical link via passenger boarding bridge (PBB) stanchion.

---

## 4\. Airworthiness Security Architecture (RTCA DO-355 & DO-326A)

The interface between airport wireless infrastructure and commercial aircraft avionics is classified as an external security perimeter under **RTCA DO-355 ("Information Security Guidance for Continuing Airworthiness")**:

1. **Mutual Authentication**: IEEE 802.1X with EAP-TLS utilizing X.509 v3 digital certificates (RSA-4096 or ECDSA P-384). Aircraft and Ground Security Gateways (GSG) verify certificate chains against airline PKI trust anchors.  
2. **Tunnel Encryption**: IPsec Encapsulating Security Payload (ESP) operating in Tunnel Mode with AES-256-GCM cipher and HMAC-SHA384 data integrity verification.  
3. **Avionics Domain Isolation**:  
   - WAGC terminates in the Aircraft Information Services Domain (AISD) or Passenger Information and Entertainment Services Domain (PIESD).  
   - Strict packet-filtering firewalls prevent routable traffic into the Aircraft Control Domain (ACD) or Flight Critical Bus without cryptographic verification and pilot consent.

---

## 5\. ARINC 429 Discrete Bus Word Formatting

The WAGC LRU outputs health, link margin, and operational status onto the aircraft low-speed (12.5–14.5 kbps) ARINC 429 avionics bus:

- **Label 270 (Octal)**: WAGC System Status, Transmit Enable/Inhibit, WOW interlock state, IPsec link health, and Error flags.  
- **Label 350 (Octal)**: Signal Margin (RSSI / SNR in dB) and Normalized Link Quality Factor (0–100%).  
- All bus words mandate **Bit 32 Odd Parity** verification before glass-cockpit ingestion.