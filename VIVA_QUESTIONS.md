# Comprehensive Viva-Voce Preparation Guide
### Project Title: Authenticated P2P File Sharing (RSA + AES + SHA-256)
### Project Code: CSL-G53 | Course: Cyber Security Lab (7CS4-22)
### Student: Suman Kumar (Roll No: 23ESKCS822) | SKIT Jaipur

---

## Part 1: Core Cryptographic Architecture & Project Understanding

### Q1: What is the main objective of your project (CSL-G53)?
**Answer:**  
The main objective is to implement an **Authenticated Peer-to-Peer (P2P) Secure File Sharing System** for local area networks. It solves three critical security problems:
1. **Confidentiality:** Preventing unauthorized eavesdropping using **AES-256-CBC**.
2. **Key Distribution & Authenticity:** Securing the session key exchange and preventing Man-in-the-Middle (MitM) attacks using **RSA-2048 (OAEP encryption and PSS digital signatures)**.
3. **Integrity:** Ensuring the file was not altered in transit using **SHA-256 cryptographic hashing**.

---

### Q2: Why did you use Hybrid Cryptography instead of using RSA for the entire file?
**Answer:**  
RSA is an asymmetric algorithm based on modular exponentiation of large numbers ($2048$ bits). It is computationally expensive and slow (typically $< 1\text{ MB/s}$), and it cannot directly encrypt arbitrary-sized files (an RSA-2048 key with OAEP padding can only encrypt up to $214$ bytes in a single block).  
Conversely, **AES-256** is a symmetric block cipher that operates hundreds of times faster ($> 500\text{ MB/s}$ on modern CPUs) and can handle files of arbitrary size, but it requires a pre-shared secret key.  
**Hybrid cryptography combines the best of both worlds:** We use RSA-2048 only once during the initial handshake to securely exchange a fresh, random 256-bit AES session key, and then use AES-256 to encrypt the actual file payload at maximum speed.

---

### Q3: Which RTU Cyber Security Lab experiment does this project link to?
**Answer:**  
It is directly linked to **Experiment 8: Secure Storage, Transmission & Digital Signature** and the syllabus mini-project designation **"Secure LAN File Transfer"**. Experiment 8 requires evaluating RSA, AES, and SHA algorithms. My project integrates these isolated theoretical concepts into a complete, working P2P network software application.

---

### Q4: Explain the step-by-step cryptographic handshake and transmission sequence.
**Answer:**  
1. **Handshake (`HELLO` / `HELLO_ACK`):** The sender and receiver exchange identities and their RSA-2048 public keys in PEM format.
2. **Session Key Generation:** The sender generates a cryptographically random 256-bit AES session key and a 16-byte Initialization Vector (IV) using `secrets.token_bytes()`.
3. **Key Encapsulation & Signing (`KEY_EXCHANGE`):** The sender encrypts the AES session key using the receiver's RSA public key with **OAEP padding**, and signs the encapsulated bundle with its own RSA private key using **PSS padding**.
4. **Key Decryption:** The receiver verifies the sender's signature, and decrypts the session key using its own RSA private key.
5. **Pre-Transmission Hashing (`FILE_HEADER`):** The sender computes the SHA-256 hash digest of the original plaintext file and signs the metadata.
6. **Encrypted Streaming (`FILE_CHUNK`):** The sender encrypts the file using AES-256 in CBC mode with PKCS#7 padding and streams 32 KB chunks over the TCP socket.
7. **Decryption & Integrity Verification (`VERIFY_RESULT`):** The receiver decrypts the stream using the AES session key, computes the SHA-256 hash of the decrypted data, and compares it to the expected hash from the header. If they match, the file is saved as **VERIFIED**; if they differ, a **TAMPER DETECTED** security alert is triggered.

---

### Q5: What padding schemes did you use for RSA and why?
**Answer:**  
- **For Encryption:** We used **OAEP (Optimal Asymmetric Encryption Padding)** with SHA-256 Mask Generation Function (MGF1). Textbook RSA ($c = m^e \pmod n$) is deterministic and vulnerable to chosen-ciphertext attacks. OAEP injects cryptographic randomness, achieving IND-CCA2 security.
- **For Digital Signatures:** We used **PSS (Probabilistic Signature Scheme)** with SHA-256. PSS introduces randomized salt before hashing and exponentiation, provably protecting against signature forgery and mathematical reduction attacks.

---

### Q6: Why is CBC (Cipher Block Chaining) mode used instead of ECB (Electronic Codebook) mode in AES?
**Answer:**  
In **ECB mode**, each 16-byte plaintext block is encrypted independently with the same key. As a result, identical plaintext blocks always produce identical ciphertext blocks, preserving structural patterns (such as the famous ECB Penguin vulnerability).  
In **CBC mode**, each plaintext block is XORed with the preceding ciphertext block before encryption ($C_i = E_K(P_i \oplus C_{i-1})$), and the first block is XORed with a unique random **Initialization Vector (IV)**. This ensures that repeated plaintext patterns result in completely random, pseudorandom ciphertext.

---

### Q7: What is the purpose of the Initialization Vector (IV) in AES-CBC? Does it need to be kept secret?
**Answer:**  
The IV ensures that encrypting the same file twice with the same key produces completely different ciphertext each time.  
**No, the IV does not need to be kept secret.** It is transmitted alongside the ciphertext. However, it must be **unpredictable and unique** (generated using a cryptographically secure pseudo-random number generator, CSPRNG) for each encryption operation.

---

### Q8: What is PKCS#7 padding, and why is it necessary for AES?
**Answer:**  
AES is a block cipher that strictly operates on 16-byte (128-bit) blocks. Files rarely have an exact multiple of 16 bytes. **PKCS#7** pads the data so its length becomes a multiple of 16. If $k$ bytes are needed ($1 \le k \le 16$), the value $k$ is repeated $k$ times (e.g., if 3 bytes are needed, `0x03 0x03 0x03` is appended). Even if the file is already a multiple of 16 bytes, a full 16-byte padding block (`0x10` repeated 16 times) is added to ensure unambiguous unpadding.

---

### Q9: What are the security properties of SHA-256?
**Answer:**  
1. **Pre-image Resistance (One-Way):** Given a hash $H$, it is computationally impossible to find the input $M$ such that $\text{SHA-256}(M) = H$.
2. **Second Pre-image Resistance (Weak Collision Resistance):** Given input $M_1$, it is infeasible to find a different input $M_2$ such that $\text{SHA-256}(M_1) = \text{SHA-256}(M_2)$.
3. **Collision Resistance (Strong):** It is infeasible to find any two arbitrary distinct inputs $M_1 \ne M_2$ that produce the same digest.
4. **Avalanche Effect:** Flipping even a single bit in the input changes approximately 50% of the bits in the 256-bit output digest.

---

### Q10: How does your system detect Man-in-the-Middle (MitM) tampering?
**Answer:**  
In our demonstration, we implemented an active **Tamper Simulation Mode** that flips a single bit in the ciphertext during transit over the network.  
When the receiver decrypts this tampered ciphertext, AES-256 error propagation distorts the decrypted plaintext. When the receiver recomputes the SHA-256 digest of the resulting plaintext, the avalanche effect yields an entirely different hash. When compared with the sender's authenticated header hash, the mismatch is detected immediately, the file is rejected, and a **CRITICAL INTEGRITY VIOLATION** alert is raised.

---

### Q11: How do you prevent a Man-in-the-Middle attacker from substituting their own public key?
**Answer:**  
In our implementation, peers can verify public keys using **SHA-256 Public Key Fingerprints** (displayed on the Web GUI and CLI). Furthermore, the sender digitally signs the key exchange and file metadata with its private key. In enterprise networks, this is extended by having a trusted **Certificate Authority (CA)** issue signed X.509 digital certificates to each peer.

---

### Q12: Why did you use length-prefixed socket framing instead of sending raw data?
**Answer:**  
TCP is a stream-oriented protocol, not a message-oriented protocol. A call to `sock.send()` does not guarantee that a single `sock.recv()` will read the exact same message boundary; packets can be fragmented or concatenated together.  
To prevent fragmentation bugs, our protocol prepends a **4-byte big-endian integer** indicating the exact length of the incoming frame (`struct.pack('>I', length)`). The receiver always reads exactly that many bytes, guaranteeing complete and isolated protocol messages.

---

### Q13: What happens if an attacker captures the transmission in Wireshark?
**Answer:**  
All packets traveling over TCP are encrypted:
- The session key is encrypted with RSA-OAEP.
- The file payload is encrypted with AES-256-CBC.
In Wireshark, the attacker sees only random, high-entropy ciphertext hex bytes. No plaintext content, confidential filenames, or encryption keys can be extracted from the packet capture.

---

### Q14: What is Perfect Forward Secrecy (PFS), and how can this project be enhanced with it?
**Answer:**  
In simple RSA key transport, if an attacker records all encrypted traffic over months and later steals the recipient's long-term RSA private key, they can decrypt all historical AES session keys and read past files.  
**Perfect Forward Secrecy (PFS)** guarantees that compromising a long-term private key does not compromise past session keys. We can achieve PFS by upgrading the key exchange from static RSA to **Ephemeral Diffie-Hellman (ECDHE / Curve25519)**, where new temporary keys are generated for each session and discarded immediately after use.

---

### Q15: What is the difference between AES-CBC + SHA-256 and AES-GCM?
**Answer:**  
AES-CBC provides confidentiality, while SHA-256 provides integrity verification (an "Encrypt-and-Hash" / "Encrypt-then-MAC" model).  
**AES-GCM (Galois/Counter Mode)** is an **Authenticated Encryption with Associated Data (AEAD)** cipher. It combines counter-mode encryption with a Galois Message Authentication Code (GMAC) within a single primitive, verifying both authenticity and confidentiality simultaneously with hardware acceleration. Transitioning to AES-GCM is one of the future scope enhancements identified in Chapter 6.

