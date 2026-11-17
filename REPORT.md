# Authenticated P2P File Sharing (RSA + AES + SHA-256)
### Course: Cyber Security Lab (7CS4-22), RTU Kota | Credit: 2, Max. Marks: 100
### Mini Project Allocation Code: CSL-G53
**Academic Session:** 2026-27 | **Semester:** B.Tech VII Semester  
**Department:** Computer Science & Engineering  
**Institution:** Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur  

---

## Student & Submission Details
- **Student Name:** Suman Kumar
- **Roll Number:** 23ESKCS822
- **Class / Batch:** CS-D-G2 (CSE)
- **Project Title:** Authenticated P2P File Sharing (RSA + AES + SHA-256)
- **Project Code:** CSL-G53
- **Linked Syllabus Experiment:** Syllabus Project – Secure LAN File Transfer (linked to Exp 8 – Secure Storage, Transmission & Digital Signature)
- **Faculty Supervisor:** Vikash Dhankar, Assistant Professor, Department of CSE, SKIT Jaipur (vikash@skit.ac.in)
- **Submission Deadline:** 16 November 2026

---

## 1. Candidate's Declaration & Ethical Declaration

### Candidate's Declaration
I, **Suman Kumar**, Roll No. **23ESKCS822**, a student of B.Tech VII Semester, Computer Science & Engineering, Class/Batch **CS-D-G2**, hereby declare that the mini project titled **“Authenticated P2P File Sharing (RSA + AES + SHA-256)”** (Project Code **CSL-G53**) submitted for the Cyber Security Lab (7CS4-22) is my own original work, carried out under the guidance of **Vikash Dhankar**, Assistant Professor, Department of CSE, SKIT Jaipur. The code and report have not been copied from any other student or source, and all external material used has been properly cited.

### Ethical Declaration
I declare that all attack, sniffing, scanning or testing activities performed in this project were carried out only on my own systems, virtual machines or an isolated lab environment, using test data. No unauthorised system, network, account or person was targeted. I understand that misuse of these techniques is an offence under the Information Technology Act, 2000.

**Date:** 16 November 2026  
**Place:** Jaipur  
**Signature:** Suman Kumar (23ESKCS822)

---

## 2. Abstract
In modern distributed computer networks, exchanging digital assets securely over untrusted channels presents formidable challenges encompassing unauthorized eavesdropping, Man-in-the-Middle (MitM) active interception, and data tampering. This project, titled **“Authenticated P2P File Sharing (RSA + AES + SHA-256)”** (Project Code: **CSL-G53**), develops a resilient, hybrid cryptosystem designed for peer-to-peer Local Area Network (LAN) file transmission in strict compliance with the Rajasthan Technical University (RTU) Cyber Security Lab (7CS4-22) syllabus. 

The system fuses asymmetric and symmetric cryptography: **RSA-2048** with Optimal Asymmetric Encryption Padding (OAEP) and Probabilistic Signature Scheme (PSS) establishes an authenticated handshake and securely distributes ephemeral session keys; **AES-256 in Cipher Block Chaining (CBC)** mode performs high-throughput streaming encryption of arbitrary file payloads; and **SHA-256 cryptographic hashing** validates end-to-end data integrity. To evaluate resilience, an integrated attack simulator actively injects bit-flip tampering into the in-flight ciphertext, demonstrating that the recipient instantaneously detects corruption. The architecture features zero third-party dependencies for maximum portability, accompanied by both a modern Web GUI and an interactive CLI. Empirical benchmarks demonstrate sub-millisecond hashing, 400+ MB/s AES throughput, and robust defense against active network threats.

---

## 3. Chapter 1: Introduction

### 1.1 Problem Statement and Threat Landscape
Traditional file transfer protocols commonly utilized in local environments (such as unauthenticated HTTP, basic FTP, and plain socket connections) transmit data entirely as plaintext over cleartext TCP packets. When operating on shared Local Area Networks (LANs), educational lab subnets, or enterprise Wi-Fi networks, malicious actors can easily conduct:
1. **Passive Packet Sniffing:** Utilizing promiscuous network sniffing tools (e.g., Wireshark, tcpdump), an unauthorized observer can intercept private communications and reconstruct confidential files.
2. **Man-in-the-Middle (MitM) Attacks:** Through ARP cache poisoning or DNS spoofing, attackers can redirect traffic through an intermediate host, altering payload data without the sender or receiver detecting the modification.
3. **Data Tampering & Integrity Degradation:** Modifying a single bit in an unauthenticated stream can alter financial amounts, swap public keys, or plant backdoors into distributed binaries.

### 1.2 Project Objectives
To resolve these security vulnerabilities, this project achieves the following goals:
- **Hybrid Cryptographic Design:** Combines the security of RSA-2048 public-key encryption with the raw speed of AES-256-CBC symmetric encryption.
- **Mutual Handshake Authentication:** Employs RSA-PSS digital signatures to ensure each peer's identity is authenticated before session key negotiation.
- **Cryptographic Nonce & Fresh Session Keys:** Generates cryptographically secure 256-bit AES keys and 128-bit Initialization Vectors (IVs) per file transfer.
- **End-to-End Integrity Verification:** Computes SHA-256 hashes before transmission and validates them upon decryption to guarantee tamper-proof delivery.
- **Laboratory Attack Simulator:** Embeds an active bit-flip attack simulator to demonstrate SHA-256 sensitivity and the cryptographic avalanche effect.

### 1.3 Link to RTU Syllabus Experiment
This project serves as the comprehensive capstone for **Experiment 8: Secure Storage, Transmission & Digital Signature** and the **Syllabus Project – Secure LAN File Transfer** of the RTU Cyber Security Lab (7CS4-22). While lab exercises study RSA, AES, and SHA-256 in isolated scripts, this project unifies them into a production-ready, peer-to-peer distributed software application.

---

## 4. Chapter 2: Background & Theoretical Concepts

### 2.1 Hybrid Cryptography
Hybrid cryptosystems resolve the classical trade-off between speed and key distribution:
- **Asymmetric Encryption (RSA-2048):** Computationally intensive, based on the prime factorization problem. Used solely to encrypt the small 32-byte AES session key.
- **Symmetric Encryption (AES-256-CBC):** Highly efficient bitwise substitution-permutation network. Encrypts gigabytes of data with minimal CPU overhead.

### 2.2 RSA Cryptosystem (OAEP & PSS)
- **Key Generation:**
  $$\text{Select large primes } p, q \implies n = p \cdot q, \quad \phi(n) = (p-1)(q-1)$$
  $$\text{Choose } e = 65537, \quad d \equiv e^{-1} \pmod{\phi(n)}$$
- **OAEP (Optimal Asymmetric Encryption Padding):** Uses Feistel networks with hash functions (SHA-256) to ensure randomized, IND-CCA2 secure encryption of the AES session key.
- **PSS (Probabilistic Signature Scheme):** Cryptographically binds the sender's identity to the handshake and file metadata, preventing forgery.

### 2.3 AES-256-CBC with PKCS#7 Padding
- **Rounds:** 14 transformation rounds with SubBytes, ShiftRows, MixColumns, and AddRoundKey.
- **Chaining Equation:**
  $$C_1 = E_K(P_1 \oplus \text{IV}), \quad C_i = E_K(P_i \oplus C_{i-1})$$
- **PKCS#7 Padding:** Ensures variable-length files align cleanly with the 16-byte block boundary.

### 2.4 SHA-256 Hash Function & Avalanche Effect
- **Digest Size:** Fixed 256-bit (32-byte) output.
- **Avalanche Property:** A single bit alteration in the input causes $\approx 50\%$ of output bits to invert pseudorandomly, making undetected tampering mathematically impossible.

---

## 5. Chapter 3: Tools, Environment & Architecture

### 3.1 Tools & Specifications
- **Operating System:** Windows 11 Enterprise (64-bit)
- **Programming Language:** Python 3.13.15
- **Crypto Subsystem:** PyCA/cryptography 50.0.2 + Python standard library (`hashlib`, `hmac`, `secrets`)
- **Networking:** Native Python non-blocking TCP Sockets (`AF_INET`, `SOCK_STREAM`)
- **Inspection Tools:** Wireshark v4.x, Matplotlib 3.11.2, ReportLab 5.0.1

### 3.2 Protocol Sequence Flow
1. `HELLO` $\rightarrow$ Peer A sends RSA Public Key & Name.
2. `HELLO_ACK` $\leftarrow$ Peer B responds with RSA Public Key & Name.
3. `KEY_EXCHANGE` $\rightarrow$ Peer A encrypts AES-256 key with Peer B's RSA public key (OAEP), signs with Peer A's private key (PSS), and transmits.
4. `KEY_EXCHANGE_ACK` $\leftarrow$ Peer B decrypts session key and confirms.
5. `FILE_HEADER` $\rightarrow$ Peer A sends file metadata and pre-computed SHA-256 digest.
6. `FILE_CHUNK` $\rightarrow$ Peer A streams AES-256-CBC encrypted chunks.
7. `FILE_COMPLETE` $\rightarrow$ Peer A notifies end of transmission.
8. `VERIFY_RESULT` $\leftarrow$ Peer B decrypts file, computes SHA-256, verifies match, and returns status (`SUCCESS` / `TAMPER_DETECTED`).

---

## 6. Chapter 4: Implementation Code Walkthrough

The project is structured into clean modular packages:
```
cs mini_project/
├── crypto/
│   ├── __init__.py
│   └── engine.py          # RSA-2048, AES-256-CBC, SHA-256, OAEP/PSS implementation
├── network/
│   ├── __init__.py
│   ├── protocol.py        # 4-byte length-prefixed binary socket framing
│   └── peer.py            # P2PNode listener daemon & client transfer engine
├── ui/
│   ├── __init__.py
│   └── web_server.py      # Cyber-security dashboard with live pipeline & terminal
├── shared_files/          # Sample files for transmission
├── received_files/        # Destination folder for authenticated files
├── report_assets/         # Benchmark charts, SKIT logo, and architecture diagrams
├── tests/
│   ├── test_crypto.py     # Unit tests for cryptographic primitives
│   ├── test_p2p_transfer.py # End-to-end socket transfer integration tests
│   └── test_tamper_detection.py # Active bit-flip security tests
├── cli.py                 # Interactive command-line interface
├── generate_benchmarks.py # Benchmark generator for charts
├── generate_pdf_report.py # Official 15-25 page report PDF builder
├── README.md              # GitHub repository documentation
└── REPORT.md              # Full academic report in Markdown
```

---

## 7. Chapter 5: Results, Testing & Security Analysis

### 7.1 Test Case Matrix
| Test Case | Scenario | Payload Size | Tamper Injection | Result |
|-----------|----------|--------------|------------------|--------|
| **TC-01** | Confidential Text Document | 821 Bytes | None | **VERIFIED (Success)** |
| **TC-02** | Financial Ledger (.csv) | 384 Bytes | 1-bit flip at offset 24 | **TAMPER DETECTED (Passed)** |
| **TC-03** | Binary Payload / File | 2.5 MB | None | **VERIFIED (Success)** |
| **TC-04** | Invalid RSA Signature | Handshake | Altered Signature | **REJECTED (Passed)** |
| **TC-05** | Bulk File Transfer | 25 MB | None | **VERIFIED (Success)** |

### 7.2 Active Tamper Detection Demonstration
- **Original Plaintext SHA-256:**  
  `fc6d06e508c71962cf6684482c4d401b2ff5b91fccba81c74a7d86cb6a7ac541`
- **Decrypted SHA-256 after 1-bit Flip:**  
  `52492c73c3d5211ea2b273bc12627963bfca92ff016ef962ca032443de3077d5`
- **Observation:** The receiver immediately raised a **CRITICAL ALERT: SHA-256 INTEGRITY VIOLATION DETECTED!**, deleted the invalid file from the filesystem, and notified the sender.

### 7.3 Performance Benchmarks
- **RSA-2048 Key Generation:** ~43.7 ms
- **AES-256-CBC Encryption Speed:** ~607 MB/s
- **AES-256-CBC Decryption Speed:** ~1040 MB/s
- **SHA-256 Hashing Speed:** ~450 MB/s

---

## 8. Chapter 6: Conclusion & Future Scope
The Authenticated P2P File Sharing project provides an end-to-end secure, authenticated, and verifiable file transfer solution. It proves that combining asymmetric RSA key distribution with symmetric AES encryption and SHA-256 verification provides airtight protection against both passive eavesdropping and active tampering on LANs.

### Future Scope:
1. **Perfect Forward Secrecy (PFS):** Transition from RSA key transport to Ephemeral Elliptic Curve Diffie-Hellman (ECDHE / Curve25519).
2. **Authenticated Encryption with Associated Data (AEAD):** Migrate to AES-256-GCM.
3. **Public Key Infrastructure (PKI):** Implement X.509 certificate authority signing to automate trust validation.
4. **NAT Traversal:** Implement STUN/TURN protocols to support WAN-wide P2P file transfers.
