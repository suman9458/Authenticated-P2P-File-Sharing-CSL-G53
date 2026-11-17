"""
Unit Tests for Cryptographic Engine (CSL-G53)
Verifies RSA-2048, AES-256-CBC, and SHA-256 integrity verification.
"""

import unittest
import os
import secrets
from crypto.engine import CryptoEngine


class TestCryptoEngine(unittest.TestCase):
    def setUp(self):
        self.alice = CryptoEngine(key_size=2048)
        self.bob = CryptoEngine(key_size=2048)

    def test_rsa_key_generation(self):
        self.assertEqual(self.alice.key_size, 2048)
        self.assertIsNotNone(self.alice.public_key)
        self.assertIsNotNone(self.alice.private_key)

        fp = CryptoEngine.get_key_fingerprint(self.alice.public_key)
        self.assertTrue(len(fp) > 0)
        self.assertIn(":", fp)

    def test_rsa_oaep_session_key_exchange(self):
        # Alice generates AES-256 key & IV
        session_key, iv = CryptoEngine.generate_aes_session_key()
        self.assertEqual(len(session_key), 32)  # 256 bits
        self.assertEqual(len(iv), 16)          # 128 bits

        # Alice encrypts session key for Bob using Bob's RSA public key
        enc_key = CryptoEngine.rsa_encrypt_session_key(session_key, self.bob.public_key)
        self.assertNotEqual(enc_key, session_key)

        # Bob decrypts session key using his RSA private key
        dec_key = self.bob.rsa_decrypt_session_key(enc_key)
        self.assertEqual(dec_key, session_key)

    def test_rsa_pss_digital_signature(self):
        message = b"Authenticated P2P Transmission - Academic Mini Project CSL-G53"
        sig = self.alice.sign_data(message)

        # Bob verifies signature with Alice's public key
        is_valid = CryptoEngine.verify_signature(message, sig, self.alice.public_key)
        self.assertTrue(is_valid)

        # Verification fails if message is altered
        tampered_msg = message + b"!"
        is_invalid = CryptoEngine.verify_signature(tampered_msg, sig, self.alice.public_key)
        self.assertFalse(is_invalid)

    def test_aes_256_cbc_encryption_decryption(self):
        key, iv = CryptoEngine.generate_aes_session_key()
        plaintext = b"This is a top-secret classified engineering document for RTU Cyber Security Lab."

        ciphertext = self.alice.aes_encrypt(plaintext, key, iv)
        self.assertNotEqual(ciphertext, plaintext)

        decrypted = self.bob.aes_decrypt(ciphertext, key, iv)
        self.assertEqual(decrypted, plaintext)

    def test_sha256_integrity_and_tamper_detection(self):
        key, iv = CryptoEngine.generate_aes_session_key()
        original_data = b"Confidential Research Findings and Source Code"

        original_hash = CryptoEngine.compute_sha256(original_data)
        ciphertext = self.alice.aes_encrypt(original_data, key, iv)

        # Case 1: Untampered transmission
        decrypted = self.bob.aes_decrypt(ciphertext, key, iv)
        decrypted_hash = CryptoEngine.compute_sha256(decrypted)
        self.assertTrue(CryptoEngine.verify_integrity(decrypted_hash, original_hash))

        # Case 2: Injected bit-flip tampering attack
        tampered_ciphertext = CryptoEngine.simulate_tampering(ciphertext, bit_flip_offset=5)
        self.assertNotEqual(tampered_ciphertext, ciphertext)

        tampered_decrypted = self.bob.aes_decrypt(tampered_ciphertext, key, iv)
        tampered_hash = CryptoEngine.compute_sha256(tampered_decrypted)

        # SHA-256 avalanche effect ensures hashes do not match
        self.assertFalse(CryptoEngine.verify_integrity(tampered_hash, original_hash))


if __name__ == "__main__":
    unittest.main()

