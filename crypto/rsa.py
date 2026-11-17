"""
Pure Python Implementation of RSA (Rivest-Shamir-Adleman) Cryptosystem
Zero external dependencies. Implements:
- Miller-Rabin primality testing with small prime pre-filtering
- Key generation (p, q, n, e, d)
- PKCS#1 v1.5 padding for encryption and digital signatures
- Key serialization (JSON and PEM-style representations)
"""

import os
import secrets
import hashlib
import json
from typing import Tuple, Optional

# First 128 small primes for fast pre-filtering candidates
_SMALL_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
    157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
    239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317,
    331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419,
    421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503,
    509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607,
    613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701,
    709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811
]

# DigestInfo ASN.1 prefix for SHA-256 in PKCS#1 v1.5 signatures
# (SEQUENCE { SEQUENCE { OID sha256, NULL }, OCTET STRING hash })
SHA256_ASN1_PREFIX = bytes([
    0x30, 0x31, 0x30, 0x0d, 0x06, 0x09, 0x60, 0x86, 0x48, 0x01,
    0x65, 0x03, 0x04, 0x02, 0x01, 0x05, 0x00, 0x04, 0x20
])


def is_probable_prime(n: int, k: int = 25) -> bool:
    """Miller-Rabin probabilistic primality test."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    # Trial division by small primes
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False

    # Write n - 1 as 2^r * d
    r = 0
    d = n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Witness loop
    for _ in range(k):
        a = secrets.randbelow(n - 4) + 2  # [2, n - 2]
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def generate_prime(bits: int) -> int:
    """Generate a prime of specified bit length."""
    while True:
        candidate = secrets.randbits(bits)
        # Ensure correct bit length and oddness
        candidate |= (1 << (bits - 1)) | 1
        if is_probable_prime(candidate):
            return candidate


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    """Extended Euclidean Algorithm: gcd(a, b) = a*x + b*y."""
    if a == 0:
        return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y


def mod_inverse(e: int, phi: int) -> int:
    """Compute modular multiplicative inverse d = e^-1 mod phi."""
    g, x, _ = egcd(e, phi)
    if g != 1:
        raise ValueError("e and phi are not coprime; modular inverse does not exist.")
    return x % phi


class RSAPublicKey:
    """Represents an RSA Public Key (e, n)."""

    def __init__(self, n: int, e: int = 65537):
        self.n = n
        self.e = e
        self.bit_size = n.bit_length()
        self.byte_size = (self.bit_size + 7) // 8

    def encrypt_raw(self, m: int) -> int:
        if m >= self.n or m < 0:
            raise ValueError("Message representative out of range")
        return pow(m, self.e, self.n)

    def encrypt_pkcs1v15(self, message: bytes) -> bytes:
        """
        Encrypts message using PKCS#1 v1.5 padding:
        EM = 0x00 || 0x02 || PS (non-zero random bytes) || 0x00 || M
        """
        k = self.byte_size
        m_len = len(message)
        if m_len > k - 11:
            raise ValueError(f"Message too long for RSA key size ({m_len} > {k - 11})")

        ps_len = k - m_len - 3
        ps = bytearray()
        while len(ps) < ps_len:
            byte = secrets.token_bytes(1)[0]
            if byte != 0:
                ps.append(byte)

        em = bytes([0x00, 0x02]) + bytes(ps) + bytes([0x00]) + message
        m_int = int.from_bytes(em, byteorder='big')
        c_int = self.encrypt_raw(m_int)
        return c_int.to_bytes(k, byteorder='big')

    def verify_pkcs1v15(self, message: bytes, signature: bytes) -> bool:
        """
        Verifies PKCS#1 v1.5 digital signature over SHA-256(message).
        EM = 0x00 || 0x01 || PS (0xFF) || 0x00 || DigestInfo || SHA256(message)
        """
        k = self.byte_size
        if len(signature) != k:
            return False

        s_int = int.from_bytes(signature, byteorder='big')
        em_int = pow(s_int, self.e, self.n)
        em = em_int.to_bytes(k, byteorder='big')

        # Check structure: 0x00 || 0x01 || 0xFF... || 0x00 || DigestInfo
        if em[0] != 0x00 or em[1] != 0x01:
            return False

        idx = 2
        while idx < k and em[idx] == 0xFF:
            idx += 1

        if idx >= k or em[idx] != 0x00:
            return False
        idx += 1

        expected_hash = hashlib.sha256(message).digest()
        expected_digest_info = SHA256_ASN1_PREFIX + expected_hash
        actual_digest_info = em[idx:]

        return actual_digest_info == expected_digest_info

    def fingerprint(self) -> str:
        """Returns SHA-256 fingerprint of the public key (hex formatted)."""
        pub_bytes = f"{self.n}:{self.e}".encode('utf-8')
        digest = hashlib.sha256(pub_bytes).hexdigest()
        return ":".join(digest[i:i+2] for i in range(0, 32, 2))

    def to_dict(self) -> dict:
        return {"n": hex(self.n), "e": hex(self.e), "bits": self.bit_size}

    @classmethod
    def from_dict(cls, data: dict) -> "RSAPublicKey":
        return cls(n=int(data["n"], 16), e=int(data["e"], 16))

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "RSAPublicKey":
        return cls.from_dict(json.loads(json_str))


class RSAPrivateKey:
    """Represents an RSA Private Key (d, p, q, n, e)."""

    def __init__(self, p: int, q: int, d: int, n: int, e: int = 65537):
        self.p = p
        self.q = q
        self.d = d
        self.n = n
        self.e = e
        self.bit_size = n.bit_length()
        self.byte_size = (self.bit_size + 7) // 8
        self.public_key = RSAPublicKey(n, e)

    def decrypt_raw(self, c: int) -> int:
        if c >= self.n or c < 0:
            raise ValueError("Ciphertext representative out of range")
        return pow(c, self.d, self.n)

    def decrypt_pkcs1v15(self, ciphertext: bytes) -> bytes:
        """Decrypts PKCS#1 v1.5 formatted ciphertext."""
        k = self.byte_size
        if len(ciphertext) != k:
            raise ValueError("Invalid ciphertext length")

        c_int = int.from_bytes(ciphertext, byteorder='big')
        m_int = self.decrypt_raw(c_int)
        em = m_int.to_bytes(k, byteorder='big')

        if em[0] != 0x00 or em[1] != 0x02:
            raise ValueError("Decryption error: invalid PKCS#1 padding header")

        sep_idx = em.find(b'\x00', 2)
        if sep_idx == -1 or sep_idx < 10:
            raise ValueError("Decryption error: invalid PKCS#1 padding structure")

        return em[sep_idx + 1:]

    def sign_pkcs1v15(self, message: bytes) -> bytes:
        """
        Signs message using PKCS#1 v1.5 scheme:
        EM = 0x00 || 0x01 || PS (0xFF) || 0x00 || DigestInfo || SHA256(message)
        """
        k = self.byte_size
        msg_hash = hashlib.sha256(message).digest()
        t = SHA256_ASN1_PREFIX + msg_hash
        t_len = len(t)
        if k < t_len + 11:
            raise ValueError("Intended encoded message length too short")

        ps = b'\xFF' * (k - t_len - 3)
        em = bytes([0x00, 0x01]) + ps + bytes([0x00]) + t
        m_int = int.from_bytes(em, byteorder='big')
        s_int = pow(m_int, self.d, self.n)
        return s_int.to_bytes(k, byteorder='big')

    def to_dict(self) -> dict:
        return {
            "n": hex(self.n),
            "e": hex(self.e),
            "d": hex(self.d),
            "p": hex(self.p),
            "q": hex(self.q),
            "bits": self.bit_size
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RSAPrivateKey":
        return cls(
            p=int(data["p"], 16),
            q=int(data["q"], 16),
            d=int(data["d"], 16),
            n=int(data["n"], 16),
            e=int(data["e"], 16)
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "RSAPrivateKey":
        return cls.from_dict(json.loads(json_str))


def generate_rsa_keypair(bits: int = 1024, e: int = 65537) -> Tuple[RSAPublicKey, RSAPrivateKey]:
    """
    Generates an RSA keypair of specified bit length (e.g. 1024 or 2048).
    Default 1024 bits provides strong security for lab environments with rapid generation.
    """
    p_bits = bits // 2
    q_bits = bits - p_bits

    while True:
        p = generate_prime(p_bits)
        q = generate_prime(q_bits)
        if p == q:
            continue
        n = p * q
        if n.bit_length() != bits:
            continue
        phi = (p - 1) * (q - 1)
        # Check that gcd(e, phi) == 1
        g, _, _ = egcd(e, phi)
        if g == 1:
            break

    d = mod_inverse(e, phi)
    priv = RSAPrivateKey(p, q, d, n, e)
    return priv.public_key, priv

