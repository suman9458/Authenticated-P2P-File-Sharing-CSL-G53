# Authenticated P2P File Sharing (RSA + AES + SHA-256)

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Course](https://img.shields.io/badge/RTU%20Kota-Cyber%20Security%20Lab%20(7CS4--22)-green.svg)](https://www.rtu.ac.in/)
[![Project Code](https://img.shields.io/badge/Project%20ID-CSL--G53-orange.svg)](#)

A resilient, hybrid cryptosystem for secure peer-to-peer (P2P) file sharing across Local Area Networks (LANs). Developed for the **Cyber Security Lab (7CS4-22)** at **Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur** (Affiliated to Rajasthan Technical University, Kota).

---

## 👨‍🎓 Project Information
- **Student Name:** Suman Kumar
- **Roll Number:** `23ESKCS822`
- **Class / Batch:** `CS-D-G2` (CSE)
- **Semester:** B.Tech VII Semester | **Session:** 2026-27
- **Project Code:** `CSL-G53`
- **Assigned Title:** Authenticated P2P File Sharing (RSA + AES + SHA-256)
- **Linked Syllabus Experiment:** Syllabus Project – Secure LAN File Transfer (linked to Exp 8 – Secure Storage, Transmission & Digital Signature)
- **Supervisor:** Mr. Vikash Dhankar, Assistant Professor, Dept. of CSE, SKIT Jaipur

---

## 🛡️ Cryptographic Architecture

The system implements an IND-CCA2 secure **Hybrid Cryptosystem** combining asymmetric and symmetric cryptography:

```
+-----------------------------------------------------------------------------------------+
|                                    PEER A (SENDER)                                      |
+-----------------------------------------------------------------------------------------+
                                             |
             1. Exchange Public Keys & Verify RSA Fingerprints (RSA-2048)
                                             |
                                             v
                      2. Generate Fresh 256-bit AES Session Key & 16B IV
                                             |
                                             v
                    3. Encapsulate Key: RSA-OAEP(AES_Key, Peer_B_PubKey)
                       Digital Signature: RSA-PSS(Key_Bundle, PrivKey_A)
                                             |
                                             v
                    4. Pre-transmission Hashing: SHA-256(Plaintext_File)
                                             |
                                             v
                      5. Encrypt File Stream: AES-256-CBC with PKCS#7
                                             |
                                             v
        [TCP Socket Streaming - 4-Byte Length-Prefixed Binary Framed Protocol]
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                   PEER B (RECEIVER)                                     |
+-----------------------------------------------------------------------------------------+
                                             |
              6. Verify Signature & Decrypt Session Key using RSA-OAEP
                                             |
                                             v
                     7. Decrypt File Payload using AES-256-CBC Session Key
                                             |
                                             v
                       8. Recompute SHA-256 Digest of Decrypted File
                                             |
                                             v
       9. Compare Expected vs Computed Digest:
          ├── MATCH       --> Mark VERIFIED & Commit File to Disk
          └── MISMATCH    --> Raise CRITICAL ALERT: TAMPER DETECTED & Discard
```

### Security Primitives Used
1. **RSA-2048 (Asymmetric Cryptosystem):**
   - **Key Size:** 2048 bits ($e = 65537$).
   - **Encryption Scheme:** OAEP (Optimal Asymmetric Encryption Padding) with SHA-256 MGF1.
   - **Authentication:** PSS (Probabilistic Signature Scheme) digital signatures.
2. **AES-256-CBC (Symmetric Block Cipher):**
   - **Key Size:** 256 bits (32 bytes generated via CSPRNG `secrets.token_bytes`).
   - **Block Mode:** CBC (Cipher Block Chaining) with unique 16-byte random IV.
   - **Padding:** PKCS#7 block alignment.
3. **SHA-256 (Cryptographic Hash Function):**
   - **Digest Length:** 256 bits (32 bytes / 64 hex characters).
   - **Integrity:** Constant-time verification preventing timing attacks.
4. **Active Tamper Simulator:**
   - Injects in-flight bit-flip corruption into ciphertext to demonstrate SHA-256 avalanche detection.

---

## 🚀 Quickstart & Usage

### Prerequisites
- Python 3.9+ (Python 3.13 recommended)
- `cryptography` library:
  ```bash
  pip install cryptography
  ```

### Option 1: Web GUI Dashboard (Recommended for Live Demo)
Run an interactive cyber security dashboard in your browser:

1. **Launch Peer 1 (Receiver / Node A):**
   ```bash
   python ui/web_server.py --name "Alice-Node" --peer-port 5001 --web-port 8080
   ```
   Open **http://127.0.0.1:8080** in your browser.

2. **Launch Peer 2 (Sender / Node B):**
   ```bash
   python ui/web_server.py --name "Bob-Node" --peer-port 5002 --web-port 8081
   ```
   Open **http://127.0.0.1:8081** in another browser window.

3. **Transfer Files:**
   - In Bob's dashboard, enter Target Port `5001`.
   - Select `shared_files/confidential_document.txt`.
   - Click **Initiate Authenticated Transfer**.
   - Watch the animated cryptographic pipeline, live security logs, and integrity verification badge!

4. **Demonstrate Tamper Detection:**
   - Check the **"Simulate Man-in-the-Middle Attack"** checkbox.
   - Click **Initiate Authenticated Transfer**.
   - Watch Alice immediately detect the SHA-256 mismatch and trigger a **CRITICAL ALERT: TAMPER DETECTED**.

---

### Option 2: Interactive Terminal CLI
You can also run headless peers directly via terminal:

1. **Start Receiver Node:**
   ```bash
   python cli.py listen --name "Peer-Bob" --port 5001
   ```

2. **Send File (Normal Secure Transfer):**
   ```bash
   python cli.py send --name "Peer-Alice" --target-port 5001 --file shared_files/confidential_document.txt
   ```

3. **Send File with Active Tamper Injection:**
   ```bash
   python cli.py send --name "Peer-Alice" --target-port 5001 --file shared_files/financial_ledger.csv --tamper
   ```

---

## 🧪 Automated Testing
Run the comprehensive test suite verifying RSA, AES, SHA-256, socket transfers, and tamper detection:

```bash
python -m unittest discover tests -v
```

Output:
```
test_aes_256_cbc_encryption_decryption (test_crypto.TestCryptoEngine) ... ok
test_rsa_key_generation (test_crypto.TestCryptoEngine) ... ok
test_rsa_oaep_session_key_exchange (test_crypto.TestCryptoEngine) ... ok
test_rsa_pss_digital_signature (test_crypto.TestCryptoEngine) ... ok
test_sha256_integrity_and_tamper_detection (test_crypto.TestCryptoEngine) ... ok
test_end_to_end_secure_transfer (test_p2p_transfer.TestP2PFileTransfer) ... ok
test_bit_flip_tampering_detected (test_tamper_detection.TestTamperDetection) ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.756s

OK
```

---

## 📊 Empirical Benchmarks
Generate performance benchmarks and figures:
```bash
python generate_benchmarks.py
```
- **RSA-2048 Key Generation:** ~43.7 ms
- **AES-256-CBC Encryption Speed:** ~607 MB/s
- **AES-256-CBC Decryption Speed:** ~1040 MB/s
- **SHA-256 Hashing Throughput:** ~450 MB/s

---

## 📁 Repository Structure
```
cs mini_project/
├── crypto/
│   ├── __init__.py
│   └── engine.py             # RSA-2048, AES-256-CBC, SHA-256, OAEP/PSS implementation
├── network/
│   ├── __init__.py
│   ├── protocol.py           # 4-byte length-prefixed binary socket framing
│   └── peer.py               # P2PNode listener daemon & client transfer engine
├── ui/
│   ├── __init__.py
│   └── web_server.py         # Cyber-security dashboard with live pipeline & terminal
├── shared_files/             # Sample files for transmission
├── received_files/           # Destination folder for authenticated files
├── report_assets/            # Benchmark charts, SKIT logo, and architecture diagrams
├── tests/
│   ├── test_crypto.py        # Unit tests for cryptographic primitives
│   ├── test_p2p_transfer.py    # End-to-end socket transfer integration tests
│   └── test_tamper_detection.py# Active bit-flip security tests
├── cli.py                    # Interactive command-line interface
├── generate_benchmarks.py    # Benchmark generator for charts
├── generate_pdf_report.py    # Official 15-25 page report PDF builder
├── 23ESKCS822_SumanKumar_CSL-G53.pdf # Official 19-Page Academic Report
├── REPORT.md                 # Full academic report in Markdown
├── VIVA_QUESTIONS.md         # 15+ Comprehensive Viva-Voce Questions & Answers
└── README.md                 # Project documentation
```

---

## 📜 Academic Deliverables
Per the official Cyber Security Lab guidelines:
1. **Printed Project Report:** 19 pages, A4 size, Times New Roman (16pt/14pt/12pt, 1.5 line spacing), bottom-center page numbers, official front page and declarations.
2. **Soft Copy ZIP:** `23ESKCS822_SumanKumar_CSL-G53.zip` containing the complete source code and `23ESKCS822_SumanKumar_CSL-G53.pdf`.
3. **Working Live Demo & Viva:** Fully prepared with GUI, CLI, and comprehensive viva guide.

---

## ⚖️ Ethical & Legal Declaration
All network transmissions, packet inspections, and simulated attacks were performed strictly on isolated local loopback sockets using dummy test data. No unauthorized networks, systems, or accounts were targeted. All activities comply with the Information Technology Act, 2000.

