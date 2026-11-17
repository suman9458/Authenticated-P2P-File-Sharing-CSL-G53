"""
Benchmark & Performance Analysis Script (CSL-G53)
Evaluates cryptographic performance of RSA, AES-256, and SHA-256,
and outputs high-resolution charts for the project report.
"""

import time
import os
import secrets
import hashlib
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

os.makedirs("report_assets", exist_ok=True)


def benchmark_rsa_keygen():
    print("[*] Benchmarking RSA Key Generation across bit lengths...")
    key_sizes = [1024, 2048, 3072, 4096]
    keygen_times = []

    for ks in key_sizes:
        start = time.perf_counter()
        _ = rsa.generate_private_key(public_exponent=65537, key_size=ks)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        keygen_times.append(elapsed)
        print(f"    RSA-{ks}: {elapsed:.2f} ms")

    plt.figure(figsize=(7, 4.5))
    bars = plt.bar([str(k) for k in key_sizes], keygen_times, color='#1f77b4', edgecolor='black')
    plt.title('RSA Key Generation Latency (ms)', fontsize=13, fontweight='bold')
    plt.xlabel('RSA Key Size (bits)', fontsize=11)
    plt.ylabel('Time (milliseconds)', fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f'{yval:.1f}ms', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig('report_assets/rsa_keygen_benchmark.png', dpi=300)
    plt.close()


def benchmark_aes_throughput():
    print("[*] Benchmarking AES-256 Throughput...")
    sizes_mb = [1, 5, 10, 25]
    enc_speeds = []
    dec_speeds = []

    key = secrets.token_bytes(32)
    iv = secrets.token_bytes(16)

    for sz in sizes_mb:
        data = secrets.token_bytes(sz * 1024 * 1024)
        
        # Encryption
        cipher_enc = Cipher(algorithms.AES(key), modes.CBC(iv))
        enc = cipher_enc.encryptor()
        start = time.perf_counter()
        ct = enc.update(data) + enc.finalize()
        enc_time = time.perf_counter() - start
        enc_speed = sz / enc_time
        enc_speeds.append(enc_speed)

        # Decryption
        cipher_dec = Cipher(algorithms.AES(key), modes.CBC(iv))
        dec = cipher_dec.decryptor()
        start = time.perf_counter()
        _ = dec.update(ct) + dec.finalize()
        dec_time = time.perf_counter() - start
        dec_speed = sz / dec_time
        dec_speeds.append(dec_speed)

        print(f"    {sz} MB -> Encrypt: {enc_speed:.1f} MB/s | Decrypt: {dec_speed:.1f} MB/s")

    plt.figure(figsize=(7, 4.5))
    plt.plot(sizes_mb, enc_speeds, marker='o', linewidth=2, color='#2ca02c', label='AES-256 Encryption')
    plt.plot(sizes_mb, dec_speeds, marker='s', linewidth=2, color='#ff7f0e', label='AES-256 Decryption')
    plt.title('AES-256-CBC Throughput vs Payload Size', fontsize=13, fontweight='bold')
    plt.xlabel('Payload Size (MB)', fontsize=11)
    plt.ylabel('Throughput (MB/s)', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig('report_assets/aes_throughput_benchmark.png', dpi=300)
    plt.close()


def benchmark_sha256_speed():
    print("[*] Benchmarking SHA-256 Hashing Speeds...")
    sizes_mb = [1, 5, 10, 25, 50]
    hash_speeds = []

    for sz in sizes_mb:
        data = secrets.token_bytes(sz * 1024 * 1024)
        start = time.perf_counter()
        _ = hashlib.sha256(data).hexdigest()
        elapsed = time.perf_counter() - start
        speed = sz / elapsed
        hash_speeds.append(speed)
        print(f"    {sz} MB -> SHA-256: {speed:.1f} MB/s ({elapsed*1000:.2f} ms)")

    plt.figure(figsize=(7, 4.5))
    bars = plt.bar([f"{s}MB" for s in sizes_mb], hash_speeds, color='#9467bd', edgecolor='black')
    plt.title('SHA-256 Hashing Throughput (MB/s)', fontsize=13, fontweight='bold')
    plt.xlabel('Buffer Size (MB)', fontsize=11)
    plt.ylabel('Throughput (MB/s)', fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 5, f'{yval:.0f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig('report_assets/sha256_benchmark.png', dpi=300)
    plt.close()


def generate_architecture_diagram():
    """Generates visual architecture diagram using Matplotlib."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axis('off')

    # Draw boxes
    boxes = [
        ("Peer A (Sender)\nAlice", 0.05, 0.55, 0.25, 0.35, '#d0e1fd'),
        ("P2P TCP Socket Channel\n(Ciphertext Only)", 0.38, 0.60, 0.24, 0.25, '#ffe0b2'),
        ("Peer B (Receiver)\nBob", 0.70, 0.55, 0.25, 0.35, '#d0e1fd'),
        ("Cryptographic Pipeline:\n1. RSA-2048 Handshake (Public Key Exch)\n2. AES-256 Session Key Encapsulation (OAEP)\n3. SHA-256 Plaintext Digest Computation\n4. Digital Signature (PSS)\n5. AES-256-CBC Stream Transmission\n6. Receiver Decryption & SHA-256 Integrity Verification",
         0.05, 0.05, 0.90, 0.40, '#e8f5e9')
    ]

    for title, x, y, w, h, col in boxes:
        rect = plt.Rectangle((x, y), w, h, facecolor=col, edgecolor='#333333', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=9.5, fontweight='bold' if 'Peer' in title or 'Channel' in title else 'normal')

    # Arrows
    ax.annotate('', xy=(0.38, 0.75), xytext=(0.30, 0.75), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=7))
    ax.annotate('', xy=(0.70, 0.75), xytext=(0.62, 0.75), arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=7))
    ax.annotate('', xy=(0.30, 0.68), xytext=(0.38, 0.68), arrowprops=dict(facecolor='blue', shrink=0.05, width=1.5, headwidth=7))
    ax.annotate('', xy=(0.62, 0.68), xytext=(0.70, 0.68), arrowprops=dict(facecolor='blue', shrink=0.05, width=1.5, headwidth=7))

    plt.title('Authenticated P2P File Sharing System Architecture (CSL-G53)', fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig('report_assets/system_architecture.png', dpi=300)
    plt.close()


if __name__ == "__main__":
    benchmark_rsa_keygen()
    benchmark_aes_throughput()
    benchmark_sha256_speed()
    generate_architecture_diagram()
    print("[+] All benchmarks and figures generated successfully!")
