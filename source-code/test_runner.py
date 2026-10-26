#!/usr/bin/env python3
"""
ARINC842Forge Pro - Automated Test Runner & Verification Suite
10 Comprehensive Verification Tests for ARINC 842 / RTCA DO-355 Compliance
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib.machinery import SourceFileLoader
cli_module = SourceFileLoader("arinc842_cli", os.path.join(os.path.dirname(__file__), "arinc842-cli.py")).load_module()
ARINC842Gatelink = cli_module.ARINC842Gatelink

class TestARINC842ForgePro(unittest.TestCase):
    def setUp(self):
        self.gatelink = ARINC842Gatelink(tail="N787BA", airport="KJFK", gate="GATE_B22", wow=True, speed_kt=0.0)

    # Test 1: WOW Inhibit
    def test_01_wow_inhibit(self):
        self.gatelink.wow = False # In-flight
        self.assertEqual(self.gatelink.get_state(), "IN_FLIGHT", "Must inhibit radios when airborne")
        self.gatelink.wow = True
        self.assertNotEqual(self.gatelink.get_state(), "IN_FLIGHT")

    # Test 2: Ground Speed Interlock
    def test_02_ground_speed_interlock(self):
        self.gatelink.speed_kt = 25.0
        self.assertEqual(self.gatelink.get_state(), "TAXI_IN", "Fast taxi must remain in TAXI_IN state")
        self.gatelink.speed_kt = 0.0
        self.assertNotEqual(self.gatelink.get_state(), "TAXI_IN")

    # Test 3: Dual-Media Selection
    def test_03_dual_media(self):
        self.assertIn(self.gatelink.media, ['TWLAN_WIFI6', 'CELLULAR_5G'])
        self.gatelink.media = 'CELLULAR_5G'
        self.assertEqual(self.gatelink.media, 'CELLULAR_5G')

    # Test 4: 802.1X EAP-TLS Authentication
    def test_04_eap_tls_authentication(self):
        self.assertTrue(self.gatelink.security['eap_tls'])
        self.assertTrue(self.gatelink.security['cert_valid'])
        # Injected cert expiry
        self.gatelink.faults['cert_expired'] = True
        self.assertEqual(self.gatelink.get_state(), 'AUTH_FAILED')
        self.gatelink.faults['cert_expired'] = False

    # Test 5: IPsec AES-256-GCM Secure Tunnel
    def test_05_ipsec_tunnel(self):
        self.assertTrue(self.gatelink.security['ipsec_tunnel'])
        self.assertEqual(self.gatelink.security['cipher'], 'AES-256-GCM')
        # Injected timeout
        self.gatelink.faults['ipsec_timeout'] = True
        self.assertEqual(self.gatelink.get_state(), 'TUNNEL_FAILED')
        self.gatelink.faults['ipsec_timeout'] = False

    # Test 6: Aircraft Domain Firewall Isolation
    def test_06_firewall_isolation(self):
        self.assertTrue(self.gatelink.security['firewall_active'], "Zero-trust firewall must isolate aircraft control domain")

    # Test 7: QAR Flight Data Offload
    def test_07_qar_offload_processing(self):
        qar = self.gatelink.offload_files[0]
        self.assertEqual(qar['name'], 'FOQA_QAR_FLIGHT_DATA.RAW')
        self.assertGreaterEqual(qar['size_mb'], 1000.0)
        # Advance transfer steps
        self.gatelink.step_transfer(delta_sec=10.0)
        self.assertGreater(qar['transferred_mb'], 0.0)

    # Test 8: ARINC 665 LSAP Database Upload
    def test_08_lsap_upload_processing(self):
        lsap = self.gatelink.upload_files[0]
        self.assertTrue(lsap['name'].endswith('.LUH'))
        self.gatelink.step_transfer(delta_sec=10.0)
        self.assertGreater(lsap['transferred_mb'], 0.0)

    # Test 9: RF Link Quality
    def test_09_rf_link_quality(self):
        self.assertGreaterEqual(self.gatelink.rssi_dbm, -85.0)
        self.assertGreaterEqual(self.gatelink.snr_db, 15.0)
        self.assertGreaterEqual(self.gatelink.phy_rate_mbps, 100.0)

    # Test 10: ARINC 429 Bit 32 Odd Parity
    def test_10_arinc429_bit32_odd_parity(self):
        w270 = self.gatelink.encode_label_270()
        w350 = self.gatelink.encode_label_350()
        self.assertEqual(bin(w270).count('1') % 2, 1, "Label 270 must have odd parity")
        self.assertEqual(bin(w350).count('1') % 2, 1, "Label 350 must have odd parity")

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestARINC842ForgePro)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\nALL 10 VERIFICATION TESTS PASSED SUCCESSFULLY.")
