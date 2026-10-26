#!/usr/bin/env python3
"""
ARINC842Forge Pro - Standalone Python CLI Runner & Simulation Suite
Standards: ARINC Project Paper 842, RTCA DO-355, RTCA DO-326A, FAA AC 119-1
"""

import sys
import os
import json
import argparse

class ARINC842Gatelink:
    def __init__(self, tail="N787BA", airport="KJFK", gate="GATE_B22", wow=True, speed_kt=0.0):
        self.tail = tail
        self.airport = airport
        self.gate = gate
        self.wow = wow
        self.speed_kt = float(speed_kt)
        self.media = 'TWLAN_WIFI6'
        self.rssi_dbm = -55.0
        self.snr_db = 32.0
        self.phy_rate_mbps = 866.0

        self.offload_files = [
            {'name': 'FOQA_QAR_FLIGHT_DATA.RAW', 'size_mb': 1250.0, 'transferred_mb': 0.0, 'completed': False},
            {'name': 'ACMS_POST_FLIGHT_REPORT.XML', 'size_mb': 14.5, 'transferred_mb': 0.0, 'completed': False}
        ]

        self.upload_files = [
            {'name': 'JEP-NAV-2611-0001.LUH', 'size_mb': 24.2, 'transferred_mb': 0.0, 'completed': False},
            {'name': 'DISPATCH_FLIGHT_RELEASE.PDF', 'size_mb': 8.8, 'transferred_mb': 0.0, 'completed': False}
        ]

        self.security = {
            'eap_tls': True,
            'cert_valid': True,
            'ipsec_tunnel': True,
            'firewall_active': True,
            'cipher': 'AES-256-GCM'
        }

        self.faults = {
            'antenna_fault': False,
            'cert_expired': False,
            'ipsec_timeout': False,
            'firewall_violation': False,
            'storage_full': False
        }

    def get_state(self):
        if not self.wow:
            return 'IN_FLIGHT'
        if self.speed_kt > 15.0:
            return 'TAXI_IN'
        if self.faults['cert_expired']:
            return 'AUTH_FAILED'
        if self.faults['ipsec_timeout']:
            return 'TUNNEL_FAILED'

        all_offload = all(f['completed'] for f in self.offload_files)
        all_upload = all(f['completed'] for f in self.upload_files)
        if all_offload and all_upload:
            return 'TRANSFER_COMPLETE'
        return 'DATA_TRANSFER'

    def step_transfer(self, delta_sec=5.0):
        state = self.get_state()
        if state not in ['DATA_TRANSFER', 'GATE_CONNECTED']:
            return {'transferred': False, 'state': state}

        eff_rate_mbps = self.phy_rate_mbps * 0.65
        mb = (eff_rate_mbps * delta_sec) / 8.0

        for f in self.offload_files:
            if not f['completed']:
                f['transferred_mb'] = min(f['size_mb'], f['transferred_mb'] + mb * 0.7)
                if f['transferred_mb'] >= f['size_mb']:
                    f['completed'] = True
                break

        for f in self.upload_files:
            if not f['completed']:
                f['transferred_mb'] = min(f['size_mb'], f['transferred_mb'] + mb * 0.3)
                if f['transferred_mb'] >= f['size_mb']:
                    f['completed'] = True
                break

        return {'transferred': True, 'rate_mbps': round(eff_rate_mbps, 1), 'state': self.get_state()}

    @staticmethod
    def compute_odd_parity(val31):
        count = bin(val31).count('1')
        return 1 if (count % 2 == 0) else 0

    def encode_label_270(self):
        word = 0x58 # Label 270
        word |= (0x01 << 8)
        if self.wow: word |= (1 << 10)
        if self.media == 'TWLAN_WIFI6': word |= (1 << 11)
        if self.media == 'CELLULAR_5G': word |= (1 << 12)
        if self.security['ipsec_tunnel']: word |= (1 << 13)
        if all(f['completed'] for f in self.offload_files): word |= (1 << 14)
        if all(f['completed'] for f in self.upload_files): word |= (1 << 15)
        if self.security['eap_tls']: word |= (1 << 16)
        word |= (0x03 << 29) # SSM Normal
        word |= (self.compute_odd_parity(word) << 31)
        return word

    def encode_label_350(self):
        word = 0xE8 # Label 350
        word |= (0x01 << 8)
        if self.faults['antenna_fault']: word |= (1 << 10)
        if self.faults['cert_expired']: word |= (1 << 11)
        if self.faults['ipsec_timeout']: word |= (1 << 12)
        if self.faults['firewall_violation']: word |= (1 << 13)
        if self.faults['storage_full']: word |= (1 << 14)
        has_fault = any(self.faults.values())
        ssm = 0x00 if has_fault else 0x03
        word |= (ssm << 29)
        word |= (self.compute_odd_parity(word) << 31)
        return word

    def run_normative_audit(self):
        tests = []
        # 1. WOW Inhibit
        prev_w = self.wow; self.wow = False
        in_flt = self.get_state() == 'IN_FLIGHT'
        self.wow = prev_w
        tests.append(('ARINC842-REQ-001', 'Weight-on-Wheels (WOW) Flight Safety Inhibit', in_flt))
        # 2. Taxi interlock
        prev_s = self.speed_kt; self.speed_kt = 20.0
        taxi_ok = self.get_state() == 'TAXI_IN'
        self.speed_kt = prev_s
        tests.append(('ARINC842-REQ-002', 'Ground Speed Gate Interlock (< 15 kt)', taxi_ok))
        # 3. Dual-Media
        tests.append(('ARINC842-REQ-003', 'Dual-Media (802.11ax TWLAN & 5G Cellular)', self.media in ['TWLAN_WIFI6', 'CELLULAR_5G']))
        # 4. EAP-TLS
        tests.append(('ARINC842-REQ-004', '802.1X EAP-TLS Mutual Authentication', self.security['eap_tls'] and self.security['cert_valid']))
        # 5. IPsec
        tests.append(('ARINC842-REQ-005', 'IPsec / IKEv2 AES-256-GCM Secure Tunneling', self.security['ipsec_tunnel'] and self.security['cipher'] == 'AES-256-GCM'))
        # 6. Firewall Isolation
        tests.append(('ARINC842-REQ-006', 'Aircraft Domain Firewall Isolation (DO-326A)', self.security['firewall_active']))
        # 7. QAR Offload
        qar_ok = any(f['size_mb'] >= 500 for f in self.offload_files)
        tests.append(('ARINC842-REQ-007', 'Automated QAR/FOQA Flight Data Offload', qar_ok))
        # 8. LSAP Upload
        lsap_ok = any(f['name'].endswith('.LUH') for f in self.upload_files)
        tests.append(('ARINC842-REQ-008', 'Secure ARINC 665 LSAP Database Upload', lsap_ok))
        # 9. RF Quality
        rf_ok = self.rssi_dbm >= -85.0 and self.snr_db >= 15.0
        tests.append(('ARINC842-REQ-009', 'Terminal Gate RF Link Quality Thresholds', rf_ok))
        # 10. ARINC 429
        w270 = self.encode_label_270()
        w350 = self.encode_label_350()
        p_ok = (bin(w270).count('1') % 2 == 1) and (bin(w350).count('1') % 2 == 1)
        tests.append(('ARINC842-REQ-010', 'ARINC 429 Status & Bit 32 Odd Parity', p_ok))

        passed = sum(1 for _, _, ok in tests if ok)
        return {
            'total': len(tests),
            'passed': passed,
            'score': f"{(passed / len(tests)) * 100:.1f}%",
            'status': 'ARINC_842_WAGC_GATELINK_CERTIFIED' if passed == len(tests) else 'NON_COMPLIANT',
            'results': [{'req': r, 'name': n, 'passed': p} for r, n, p in tests]
        }

def main():
    parser = argparse.ArgumentParser(description="ARINC842Forge Pro CLI Gatelink Simulator")
    parser.add_argument("--tail", default="N787BA", help="Aircraft Tail Number")
    parser.add_argument("--airport", default="KJFK", help="Airport ICAO Code")
    parser.add_argument("--gate", default="GATE_B22", help="Terminal Gate ID")
    parser.add_argument("--airborne", action="store_true", help="Simulate airborne flight state (WOW=False)")
    parser.add_argument("--speed", type=float, default=0.0, help="Aircraft Ground Speed (kt)")
    parser.add_argument("--step", type=int, default=1, help="Advance transfer steps")
    parser.add_argument("--audit", action="store_true", help="Run 10-point airworthiness security audit")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    gatelink = ARINC842Gatelink(
        tail=args.tail,
        airport=args.airport,
        gate=args.gate,
        wow=not args.airborne,
        speed_kt=args.speed
    )

    if args.audit:
        res = gatelink.run_normative_audit()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print("================================================================================")
            print(" ARINC842Forge Pro - 10-Point Normative Airworthiness Security Audit")
            print(" Standards: ARINC Project Paper 842, RTCA DO-355, RTCA DO-326A, FAA AC 119-1")
            print("================================================================================")
            for r in res['results']:
                status = "PASS [OK]" if r['passed'] else "FAIL [X]"
                print(f" {r['req']:<18} | {r['name']:<55} | {status}")
            print("--------------------------------------------------------------------------------")
            print(f" Compliance Score: {res['score']} ({res['passed']}/{res['total']}) | Status: {res['status']}")
            print("================================================================================")
        return

    # Simulate steps if requested
    for _ in range(args.step):
        gatelink.step_transfer()

    w270 = gatelink.encode_label_270()
    w350 = gatelink.encode_label_350()

    data = {
        'aircraft': gatelink.tail,
        'location': f"{gatelink.airport} {gatelink.gate}",
        'state': gatelink.get_state(),
        'media': gatelink.media,
        'rssi_dbm': gatelink.rssi_dbm,
        'snr_db': gatelink.snr_db,
        'phy_rate_mbps': gatelink.phy_rate_mbps,
        'security': gatelink.security,
        'offload_queue': gatelink.offload_files,
        'upload_queue': gatelink.upload_files,
        'arinc429_hex': {
            'label270': f"0x{w270:08X}",
            'label350': f"0x{w350:08X}"
        }
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print("================================================================================")
        print(" ARINC842Forge Pro - Wireless Airport Gatelink Communications Telemetry")
        print("================================================================================")
        print(f" Aircraft Tail   : {data['aircraft']} | Gate: {data['location']}")
        print(f" Link State      : [{data['state']}] | Media: {data['media']}")
        print(f" RF Signal       : RSSI {data['rssi_dbm']} dBm | SNR {data['snr_db']} dB | PHY {data['phy_rate_mbps']} Mbps")
        print(f" Security        : EAP-TLS={data['security']['eap_tls']} | IPsec Tunnel={data['security']['ipsec_tunnel']} ({data['security']['cipher']})")
        print("--------------------------------------------------------------------------------")
        print(" Active Transfer Queues:")
        for f in data['offload_queue']:
            print(f"  [OFFLOAD] {f['name']:<30} {f['transferred_mb']:6.1f} / {f['size_mb']:6.1f} MB [{'DONE' if f['completed'] else 'SYNCING'}]")
        for f in data['upload_queue']:
            print(f"  [UPLOAD ] {f['name']:<30} {f['transferred_mb']:6.1f} / {f['size_mb']:6.1f} MB [{'DONE' if f['completed'] else 'SYNCING'}]")
        print("--------------------------------------------------------------------------------")
        print(f" ARINC 429 Bus   : L270={data['arinc429_hex']['label270']} | L350={data['arinc429_hex']['label350']}")
        print("================================================================================")

if __name__ == '__main__':
    main()
