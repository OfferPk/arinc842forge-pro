/**
 * ARINC842Forge Pro - Core Wireless Airport Gatelink Communications (WAGC) Engine
 * Standards: ARINC Project Paper 842, RTCA DO-355, RTCA DO-326A, FAA AC 119-1, IEEE 802.11ax / 3GPP 5G
 * 
 * Provides:
 * - Weight-on-Wheels (WOW) & Ground Speed gate interlock state machine
 * - 802.11ax TWLAN & 5G cellular dual-media airport surface link simulation
 * - 802.1X EAP-TLS mutual authentication & X.509 certificate validation
 * - IPsec / IKEv2 AES-256-GCM secure tunnel management
 * - High-speed bidirectional transfer: QAR/FOQA flight data offload & ARINC 665 LSAP upload
 * - Airport terminal gate RF roaming model (RSSI, SNR, PHY rate, packet loss)
 * - ARINC 429 digital bus serialization (Labels 270, 350) with Bit 32 odd parity
 */

class ARINC842Engine {
  constructor(options = {}) {
    this.tailNumber = options.tailNumber || 'N787BA';
    this.airlineCode = options.airlineCode || 'UAL'; // United Airlines
    this.airportCode = options.airportCode || 'KJFK'; // JFK Terminal 7
    this.gateId = options.gateId || 'GATE_B22';

    // Aircraft Ground Interlocks
    this.weightOnWheels = options.weightOnWheels !== undefined ? options.weightOnWheels : true;
    this.groundSpeedKt = options.groundSpeedKt !== undefined ? options.groundSpeedKt : 0.0;
    this.parkingBrakeSet = options.parkingBrakeSet !== undefined ? options.parkingBrakeSet : true;

    // RF Link Parameters
    this.activeMedia = options.activeMedia || 'TWLAN_WIFI6'; // 'TWLAN_WIFI6' or 'CELLULAR_5G'
    this.rssiDbm = options.rssiDbm || -55.0; // dBm (-50 excellent, -85 weak)
    this.snrDb = options.snrDb || 32.0;     // dB
    this.phyRateMbps = options.phyRateMbps || 866.0; // Mbps
    
    // Transfer Queues
    this.offloadQueue = [
      { id: 'QAR-LOG-20261015', name: 'FOQA_QAR_FLIGHT_DATA.RAW', sizeMb: 1250.0, transferredMb: 0.0, status: 'PENDING' },
      { id: 'ACMS-RPT-0082', name: 'ACMS_POST_FLIGHT_REPORT.XML', sizeMb: 14.5, transferredMb: 0.0, status: 'PENDING' }
    ];

    this.uploadQueue = [
      { id: 'LSAP-AIRAC-2611', name: 'JEP-NAV-2611-0001.LUH', sizeMb: 24.2, transferredMb: 0.0, status: 'PENDING' },
      { id: 'EFB-FLT-RELEASE', name: 'DISPATCH_FLIGHT_RELEASE_KJFK_EGLL.PDF', sizeMb: 8.8, transferredMb: 0.0, status: 'PENDING' }
    ];

    // Security & State
    this.state = 'GATE_CONNECTED'; // 'IN_FLIGHT', 'TAXI_IN', 'GATE_CONNECTED', 'AUTHENTICATING', 'TUNNEL_ACTIVE', 'DATA_TRANSFER', 'TRANSFER_COMPLETE'
    this.security = {
      eapTlsAuthenticated: true,
      certExpiryValid: true,
      ipsecTunnelEstablished: true,
      firewallIsolationActive: true,
      encryptionCipher: 'AES-256-GCM'
    };

    this.faults = {
      rfAntennaFault: false,
      certExpired: false,
      ipsecHandshakeTimeout: false,
      gatewayFirewallViolation: false,
      storageFull: false
    };

    this.evaluateStateMachine();
  }

  // --- State Machine & Gate Interlocks ---

  evaluateStateMachine() {
    // Flight safety interlock: In-flight radio inhibition
    if (!this.weightOnWheels) {
      this.state = 'IN_FLIGHT';
      this.security.eapTlsAuthenticated = false;
      this.security.ipsecTunnelEstablished = false;
      return this.state;
    }

    if (this.groundSpeedKt > 15.0) {
      this.state = 'TAXI_IN';
      return this.state;
    }

    if (this.faults.certExpired) {
      this.state = 'AUTH_FAILED';
      this.security.eapTlsAuthenticated = false;
      this.security.ipsecTunnelEstablished = false;
      return this.state;
    }

    if (this.faults.ipsecHandshakeTimeout) {
      this.state = 'TUNNEL_FAILED';
      this.security.ipsecTunnelEstablished = false;
      return this.state;
    }

    // Nominal progression
    this.security.eapTlsAuthenticated = true;
    this.security.ipsecTunnelEstablished = true;

    const allOffloadDone = this.offloadQueue.every(f => f.status === 'COMPLETED');
    const allUploadDone = this.uploadQueue.every(f => f.status === 'COMPLETED');

    if (allOffloadDone && allUploadDone) {
      this.state = 'TRANSFER_COMPLETE';
    } else {
      this.state = 'DATA_TRANSFER';
    }

    return this.state;
  }

  // --- High-Speed Transfer Simulation ---

  /**
   * Simulates progress step across active transfer queues based on current PHY throughput
   */
  stepTransfer(deltaSeconds = 2.0) {
    this.evaluateStateMachine();
    if (this.state !== 'DATA_TRANSFER' && this.state !== 'GATE_CONNECTED') {
      return { transferred: false, state: this.state };
    }

    // Effective throughput roughly 65% of PHY link rate
    const effectiveThroughputMbps = this.phyRateMbps * 0.65;
    const mbPerStep = (effectiveThroughputMbps * deltaSeconds) / 8.0;

    // Advance Offload Queue
    const activeOffload = this.offloadQueue.find(f => f.status !== 'COMPLETED');
    if (activeOffload) {
      activeOffload.status = 'TRANSFERRING';
      activeOffload.transferredMb = Math.min(activeOffload.sizeMb, activeOffload.transferredMb + mbPerStep * 0.7);
      if (activeOffload.transferredMb >= activeOffload.sizeMb) {
        activeOffload.status = 'COMPLETED';
      }
    }

    // Advance Upload Queue
    const activeUpload = this.uploadQueue.find(f => f.status !== 'COMPLETED');
    if (activeUpload) {
      activeUpload.status = 'TRANSFERRING';
      activeUpload.transferredMb = Math.min(activeUpload.sizeMb, activeUpload.transferredMb + mbPerStep * 0.3);
      if (activeUpload.transferredMb >= activeUpload.sizeMb) {
        activeUpload.status = 'COMPLETED';
      }
    }

    this.evaluateStateMachine();
    return {
      transferred: true,
      effectiveThroughputMbps: parseFloat(effectiveThroughputMbps.toFixed(1)),
      state: this.state
    };
  }

  // --- ARINC 429 Bus Protocol Serialization ---

  static computeOddParity(val31) {
    let count = 0;
    for (let i = 0; i < 31; i++) {
      if ((val31 >>> i) & 1) count++;
    }
    return (count % 2 === 0) ? 1 : 0;
  }

  /**
   * Encodes ARINC 429 Label 270: Gatelink Discrete Status Word
   */
  encodeLabel270() {
    this.evaluateStateMachine();
    let word = 0x58; // Label 270 octal reversed = 0x58
    const sdi = 0x01; // System 1
    word |= (sdi << 8);

    if (this.weightOnWheels) word |= (1 << 10);              // Bit 11: WOW Active
    if (this.activeMedia === 'TWLAN_WIFI6') word |= (1 << 11);// Bit 12: Wi-Fi Connected
    if (this.activeMedia === 'CELLULAR_5G') word |= (1 << 12); // Bit 13: 5G Connected
    if (this.security.ipsecTunnelEstablished) word |= (1 << 13); // Bit 14: IPsec Tunnel Active
    
    const allOffloadDone = this.offloadQueue.every(f => f.status === 'COMPLETED');
    const allUploadDone = this.uploadQueue.every(f => f.status === 'COMPLETED');
    if (allOffloadDone) word |= (1 << 14);                   // Bit 15: QAR Offload Complete
    if (allUploadDone) word |= (1 << 15);                    // Bit 16: LSAP Upload Complete
    if (this.security.eapTlsAuthenticated) word |= (1 << 16); // Bit 17: EAP-TLS Auth Valid

    // SSM: Normal Operation (11)
    word |= (0x03 << 29);
    const parity = ARINC842Engine.computeOddParity(word);
    word |= (parity << 31);

    return {
      label: '270',
      labelOctal: '270',
      description: 'Gatelink Ground Communications Discrete Status Word',
      rawHex: '0x' + (word >>> 0).toString(16).toUpperCase().padStart(8, '0'),
      rawUint32: word >>> 0,
      parityBit: parity,
      state: this.state
    };
  }

  /**
   * Encodes ARINC 429 Label 350: Gatelink BITE & Security Fault Word
   */
  encodeLabel350() {
    let word = 0xE8; // Label 350 octal reversed = 0xE8
    const sdi = 0x01;
    word |= (sdi << 8);

    if (this.faults.rfAntennaFault) word |= (1 << 10);        // Bit 11: Antenna Fault
    if (this.faults.certExpired) word |= (1 << 11);           // Bit 12: Cert Expired
    if (this.faults.ipsecHandshakeTimeout) word |= (1 << 12); // Bit 13: IPsec Timeout
    if (this.faults.gatewayFirewallViolation) word |= (1 << 13); // Bit 14: Firewall Trip
    if (this.faults.storageFull) word |= (1 << 14);           // Bit 15: Storage Full

    const hasFault = Object.values(this.faults).some(f => f === true);
    const ssm = hasFault ? 0x00 : 0x03; // Failure Warning (00) vs Normal (11)
    word |= (ssm << 29);
    const parity = ARINC842Engine.computeOddParity(word);
    word |= (parity << 31);

    return {
      label: '350',
      labelOctal: '350',
      description: 'Gatelink BITE & Airworthiness Security Fault Word',
      rawHex: '0x' + (word >>> 0).toString(16).toUpperCase().padStart(8, '0'),
      rawUint32: word >>> 0,
      parityBit: parity,
      hasFault: hasFault,
      ssmStatus: hasFault ? 'Failure Warning (00)' : 'Normal Operation (11)'
    };
  }

  getTelemetry() {
    this.evaluateStateMachine();
    return {
      tailNumber: this.tailNumber,
      airport: `${this.airportCode} ${this.gateId}`,
      state: this.state,
      interlocks: {
        weightOnWheels: this.weightOnWheels,
        groundSpeedKt: this.groundSpeedKt,
        parkingBrakeSet: this.parkingBrakeSet
      },
      rfLink: {
        media: this.activeMedia,
        rssiDbm: this.rssiDbm,
        snrDb: this.snrDb,
        phyRateMbps: this.phyRateMbps,
        signalQuality: this.rssiDbm >= -65 ? 'EXCELLENT' : (this.rssiDbm >= -75 ? 'GOOD' : 'MARGINAL')
      },
      security: this.security,
      queues: {
        offload: this.offloadQueue,
        upload: this.uploadQueue
      },
      faults: this.faults,
      arinc429: {
        label270: this.encodeLabel270(),
        label350: this.encodeLabel350()
      }
    };
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ARINC842Engine };
}
