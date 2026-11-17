"""
Integration Tests for P2P End-to-End File Transfer (CSL-G53)
Tests bidirectional peer-to-peer file transfer over network sockets.
"""

import unittest
import os
import time
import shutil
from network.peer import P2PPeer
from crypto.engine import CryptoEngine


class TestP2PFileTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alice_recv = "received_files_alice"
        cls.bob_recv = "received_files_bob"
        os.makedirs(cls.alice_recv, exist_ok=True)
        os.makedirs(cls.bob_recv, exist_ok=True)
        os.makedirs("test_data", exist_ok=True)

        cls.alice = P2PPeer(node_name="Alice-Node", host="127.0.0.1", port=5901, save_dir=cls.alice_recv)
        cls.bob = P2PPeer(node_name="Bob-Node", host="127.0.0.1", port=5902, save_dir=cls.bob_recv)

        cls.alice.start_server()
        cls.bob.start_server()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.alice.stop_server()
        cls.bob.stop_server()
        shutil.rmtree(cls.alice_recv, ignore_errors=True)
        shutil.rmtree(cls.bob_recv, ignore_errors=True)
        shutil.rmtree("test_data", ignore_errors=True)

    def test_end_to_end_secure_transfer(self):
        # Create a sample payload file
        test_file = os.path.join("test_data", "classified_report.txt")
        test_content = (
            b"CONFIDENTIAL CYBER SECURITY LAB (7CS4-22) SUBMISSION\n"
            b"Student: Suman Kumar (23ESKCS822)\n"
            b"Project: Authenticated P2P File Sharing (CSL-G53)\n"
            b"Payload: RSA-2048 Asymmetric Key Exchange + AES-256 Symmetric Cipher + SHA-256 Integrity Verification.\n"
        )
        with open(test_file, "wb") as f:
            f.write(test_content)

        orig_hash = CryptoEngine.compute_sha256(test_content)

        # Alice sends file to Bob
        result = self.alice.send_file(
            target_host="127.0.0.1",
            target_port=5902,
            filepath=test_file,
            simulate_tampering=False
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["expected_sha256"], orig_hash)

        # Verify Bob received the file and contents match exactly
        received_path = os.path.join(self.bob_recv, "classified_report.txt")
        self.assertTrue(os.path.exists(received_path))

        with open(received_path, "rb") as f:
            recv_content = f.read()

        self.assertEqual(recv_content, test_content)
        self.assertEqual(CryptoEngine.compute_sha256(recv_content), orig_hash)


if __name__ == "__main__":
    unittest.main()

