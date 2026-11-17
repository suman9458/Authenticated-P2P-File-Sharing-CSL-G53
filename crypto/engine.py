"""
Cryptographic Engine for Authenticated P2P File Sharing (CSL-G53)
Implements Hybrid Cryptography:
1. RSA-2048: Asymmetric key exchange & digital signatures (OAEP & PSS)
2. AES-256-CBC: High-throughput symmetric file encryption with PKCS#7 padding
3. SHA-256: Cryptographic hashing for file integrity verification
"""

import os
import secrets
import hashlib
from typing import Tuple, Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class CryptoEngine:
    """Core cryptographic engine handling RSA, AES-256, and SHA-256 operations."""

    def __init__(self, key_size: int = 2048):
        self.key_size = key_size
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        self.public_key = self.private_key.public_key()

    # -------------------------------------------------------------------------
    # RSA Key Management & Serialization
    # -------------------------------------------------------------------------
    def export_public_key_pem(self) -> str:
        """Exports the public key in PEM format."""
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_bytes.decode('utf-8')

    def export_private_key_pem(self) -> str:
        """Exports the private key in PEM format."""
        pem_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem_bytes.decode('utf-8')

    @staticmethod
    def load_public_key_pem(pem_str: str) -> rsa.RSAPublicKey:
        """Loads an RSA public key from PEM string."""
        return serialization.load_pem_public_key(pem_str.encode('utf-8'))

    @staticmethod
    def get_key_fingerprint(public_key: rsa.RSAPublicKey) -> str:
        """Calculates a formatted SHA-256 fingerprint for an RSA public key."""
        der_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        digest = hashlib.sha256(der_bytes).hexdigest().upper()
        return ":".join(digest[i:i+2] for i in range(0, 32, 2))

    # -------------------------------------------------------------------------
    # RSA Asymmetric Encryption & Decryption (OAEP Padding)
    # -------------------------------------------------------------------------
    @staticmethod
    def rsa_encrypt_session_key(session_key: bytes, peer_public_key: rsa.RSAPublicKey) -> bytes:
        """
        Encrypts symmetric session key using peer's RSA public key with OAEP padding.
        OAEP (Optimal Asymmetric Encryption Padding) prevents chosen-ciphertext attacks.
        """
        return peer_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def rsa_decrypt_session_key(self, encrypted_session_key: bytes) -> bytes:
        """
        Decrypts symmetric session key using local RSA private key with OAEP padding.
        """
        return self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    # -------------------------------------------------------------------------
    # RSA Digital Signatures (PSS Padding)
    # -------------------------------------------------------------------------
    def sign_data(self, data: bytes) -> bytes:
        """
        Signs binary data using local RSA private key and PSS padding with SHA-256.
        """
        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    @staticmethod
    def verify_signature(data: bytes, signature: bytes, peer_public_key: rsa.RSAPublicKey) -> bool:
        """
        Verifies digital signature against binary data using peer's RSA public key.
        Returns True if authentic, False otherwise.
        """
        try:
            peer_public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # AES-256 Symmetric Key & Cipher Operations (CBC Mode + PKCS#7)
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_aes_session_key() -> Tuple[bytes, bytes]:
        """
        Generates a cryptographically strong 256-bit (32-byte) AES key
        and a 128-bit (16-byte) Initialization Vector (IV).
        """
        key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        return key, iv

    @staticmethod
    def _pad_pkcs7(data: bytes, block_size: int = 16) -> bytes:
        """Applies PKCS#7 padding to align with AES block size."""
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)

    @staticmethod
    def _unpad_pkcs7(data: bytes) -> bytes:
        """Validates and strips PKCS#7 padding."""
        if not data:
            raise ValueError("Cannot unpad empty data buffer")
        padding_len = data[-1]
        if padding_len < 1 or padding_len > 16:
            raise ValueError("Invalid PKCS#7 padding length")
        if data[-padding_len:] != bytes([padding_len] * padding_len):
            raise ValueError("Corrupted PKCS#7 padding sequence")
        return data[:-padding_len]

    def aes_encrypt(self, plaintext: bytes, key: bytes, iv: bytes) -> bytes:
        """
        Encrypts plaintext using AES-256 in CBC mode with PKCS#7 padding.
        """
        padded_data = self._pad_pkcs7(plaintext)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()

    def aes_decrypt(self, ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        """
        Decrypts ciphertext using AES-256 in CBC mode and validates PKCS#7 padding.
        """
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return self._unpad_pkcs7(padded_plaintext)

    # -------------------------------------------------------------------------
    # SHA-256 Integrity Verification
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Computes hexadecimal SHA-256 hash digest of a byte sequence."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def compute_file_sha256(filepath: str, chunk_size: int = 65536) -> str:
        """Computes hexadecimal SHA-256 hash digest of a file in chunks."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def verify_integrity(computed_hash: str, expected_hash: str) -> bool:
        """Constant-time comparison of SHA-256 digests to prevent timing attacks."""
        return secrets.compare_digest(computed_hash.lower(), expected_hash.lower())

    # -------------------------------------------------------------------------
    # Tamper Simulation Tool (for Lab Demo & Security Evaluation)
    # -------------------------------------------------------------------------
    @staticmethod
    def simulate_tampering(ciphertext: bytes, bit_flip_offset: int = 10) -> bytes:
        """
        Simulates an active Man-in-the-Middle (MitM) tamper attack by flipping
        a single bit in the ciphertext to demonstrate SHA-256 tamper detection.
        """
        if not ciphertext:
            return ciphertext
        buf = bytearray(ciphertext)
        idx = min(bit_flip_offset, len(buf) - 1)
        buf[idx] ^= 0x01  # Flip least significant bit
        return bytes(buf)

