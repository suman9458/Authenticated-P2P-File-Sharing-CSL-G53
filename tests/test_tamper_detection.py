"""
Security & Tamper Detection Tests for P2P File Transfer (CSL-G53)
Verifies that any Man-in-the-Middle bit modification causes integrity check failure.
"""

import unittest
import os
import time
import shutil
from network.peer import P2PPeer
from crypto.engine import CryptoEngine


class TestTamperDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alice_recv = "received_files_tamper_alice"
        cls.bob_recv = "received_files_tamper_bob"
        os.makedirs(cls.alice_recv, exist_ok=True)
        os.makedirs(cls.bob_recv, exist_ok=True)
        os.makedirs("test_tamper_data", exist_ok=True)

        cls.alice = P2PPeer(node_name="Alice-Tester", host="127.0.0.1", port=5911, save_dir=cls.alice_recv)
        cls.bob = P2PPeer(node_name="Bob-Tester", host="127.0.0.1", port=5912, save_dir=cls.bob_recv)

        cls.alice.start_server()
        cls.bob.start_server()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.alice.stop_server()
        cls.bob.stop_server()
        shutil.rmtree(cls.alice_recv, ignore_errors=True)
        shutil.rmtree(cls.bob_recv, ignore_errors=True)
        shutil.rmtree("test_tamper_data", ignore_errors=True)

    def test_bit_flip_tampering_detected(self):
        # Create test document
        test_file = os.path.join("test_tamper_data", "bank_transfer_order.txt")
        test_content = b"TRANSFER $50,000 USD TO ACCOUNT #987654321 - AUTHORIZED BY CFO."
        with open(test_file, "wb") as f:
            f.write(test_content)

        orig_hash = CryptoEngine.compute_sha256(test_content)

        # Alice sends file to Bob with active simulated bit-flip tampering
        result = self.alice.send_file(
            target_host="127.0.0.1",
            target_port=5912,
            filepath=test_file,
            simulate_tampering=True
        )

        # Assert that the recipient detected tampering
        self.assertEqual(result["status"], "TAMPER_DETECTED")
        self.assertNotEqual(result["computed_sha256"], orig_hash)


if __name__ == "__main__":
    unittest.main()

