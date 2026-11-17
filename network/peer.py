"""
P2P Peer Node Implementation (CSL-G53)
Supports concurrent bidirectional file transfers, cryptographic handshakes,
streaming AES-256-CBC file transfer, SHA-256 verification, and active tamper testing.
"""

import os
import socket
import threading
import base64
import time
from typing import Optional, Callable, Dict, Any, List

from crypto.engine import CryptoEngine
from network.protocol import (
    send_msg, recv_msg,
    MSG_HELLO, MSG_HELLO_ACK,
    MSG_KEY_EXCHANGE, MSG_KEY_EXCHANGE_ACK,
    MSG_FILE_HEADER, MSG_FILE_CHUNK,
    MSG_FILE_COMPLETE, MSG_VERIFY_RESULT, MSG_ERROR
)


class P2PPeer:
    """Represents an authenticated P2P file sharing node."""

    def __init__(
        self,
        node_name: str = "Peer-Node",
        host: str = "127.0.0.1",
        port: int = 5001,
        save_dir: str = "received_files",
        log_callback: Optional[Callable[[str, str], None]] = None
    ):
        self.node_name = node_name
        self.host = host
        self.port = port
        self.save_dir = save_dir
        self.log_callback = log_callback

        os.makedirs(self.save_dir, exist_ok=True)

        # Initialize local cryptographic engine (generates 2048-bit RSA keypair)
        self.crypto = CryptoEngine(key_size=2048)
        self.fingerprint = CryptoEngine.get_key_fingerprint(self.crypto.public_key)

        self._server_sock: Optional[socket.socket] = None
        self._is_running = False
        self._server_thread: Optional[threading.Thread] = None

        # Transfer audit logs and state
        self.transfer_history: List[Dict[str, Any]] = []
        self.last_pipeline_state: Dict[str, Any] = {}

    def log(self, message: str, level: str = "INFO"):
        """Logs message internally and triggers optional callback."""
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        if self.log_callback:
            self.log_callback(entry, level)
        else:
            print(entry)

    # -------------------------------------------------------------------------
    # Server (Receiver Daemon)
    # -------------------------------------------------------------------------
    def start_server(self):
        """Starts background TCP listener thread."""
        if self._is_running:
            return

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(5)
        self._is_running = True

        self._server_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._server_thread.start()
        self.log(f"Server started on {self.host}:{self.port} | RSA Fingerprint: {self.fingerprint}")

    def stop_server(self):
        """Gracefully shuts down the listener socket."""
        self._is_running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        self.log("Server daemon stopped")

    def _listen_loop(self):
        """Accepts incoming P2P connections."""
        while self._is_running:
            try:
                client_sock, addr = self._server_sock.accept()
                threading.Thread(
                    target=self._handle_incoming_connection,
                    args=(client_sock, addr),
                    daemon=True
                ).start()
            except Exception:
                break

    def _handle_incoming_connection(self, sock: socket.socket, addr: tuple):
        """Executes receiver-side cryptographic handshake and file receipt."""
        client_ip = f"{addr[0]}:{addr[1]}"
        self.log(f"Incoming connection from {client_ip}", "SECURITY")

        session_key: Optional[bytes] = None
        session_iv: Optional[bytes] = None
        sender_pub_key = None
        sender_name = "Unknown"
        file_meta = None
        encrypted_chunks: List[bytes] = []

        try:
            while True:
                msg = recv_msg(sock)
                if not msg:
                    break

                mtype = msg.get("type")

                # Step 1: RSA Asymmetric Handshake
                if mtype == MSG_HELLO:
                    sender_name = msg.get("sender_name", "Remote-Peer")
                    sender_pub_pem = msg.get("public_key_pem", "")
                    sender_pub_key = CryptoEngine.load_public_key_pem(sender_pub_pem)
                    sender_fp = CryptoEngine.get_key_fingerprint(sender_pub_key)
                    self.log(f"Handshake initiated by '{sender_name}' (RSA Fingerprint: {sender_fp})", "CRYPTO")

                    # Reply with our public key
                    send_msg(sock, {
                        "type": MSG_HELLO_ACK,
                        "receiver_name": self.node_name,
                        "public_key_pem": self.crypto.export_public_key_pem()
                    })

                # Step 2: AES-256 Session Key Decapsulation & Signature Verification
                elif mtype == MSG_KEY_EXCHANGE:
                    enc_key_b64 = msg.get("encrypted_session_key", "")
                    iv_b64 = msg.get("iv", "")
                    sig_b64 = msg.get("signature", "")

                    enc_key = base64.b64decode(enc_key_b64)
                    session_iv = base64.b64decode(iv_b64)
                    sig = base64.b64decode(sig_b64)

                    # Verify digital signature over (enc_key + session_iv)
                    signed_payload = enc_key + session_iv
                    if not CryptoEngine.verify_signature(signed_payload, sig, sender_pub_key):
                        self.log("Digital signature verification failed on key exchange!", "ERROR")
                        send_msg(sock, {"type": MSG_ERROR, "error": "Signature verification failed"})
                        return

                    # Decrypt AES-256 session key using RSA private key
                    session_key = self.crypto.rsa_decrypt_session_key(enc_key)
                    self.log("AES-256 session key decrypted successfully using RSA-OAEP", "CRYPTO")

                    send_msg(sock, {"type": MSG_KEY_EXCHANGE_ACK, "status": "KEY_ACCEPTED"})

                # Step 3: File Metadata & Plaintext Hash Header
                elif mtype == MSG_FILE_HEADER:
                    file_meta = msg
                    filename = msg.get("filename", "unnamed.bin")
                    filesize = msg.get("filesize", 0)
                    expected_sha256 = msg.get("sha256", "")
                    meta_sig = base64.b64decode(msg.get("signature", ""))

                    # Verify header signature
                    meta_str = f"{filename}:{filesize}:{expected_sha256}".encode("utf-8")
                    if not CryptoEngine.verify_signature(meta_str, meta_sig, sender_pub_key):
                        self.log("File metadata signature invalid! Aborting transfer.", "ERROR")
                        send_msg(sock, {"type": MSG_ERROR, "error": "Metadata signature mismatch"})
                        return

                    self.log(f"Receiving '{filename}' ({filesize} bytes). Expected SHA-256: {expected_sha256}", "INFO")

                # Step 4: Encrypted File Chunks
                elif mtype == MSG_FILE_CHUNK:
                    chunk_data = base64.b64decode(msg.get("data", ""))
                    encrypted_chunks.append(chunk_data)

                # Step 5: Transfer Complete, AES Decryption & SHA-256 Integrity Verification
                elif mtype == MSG_FILE_COMPLETE:
                    total_encrypted = b"".join(encrypted_chunks)
                    filename = file_meta.get("filename", "received.bin")
                    expected_sha256 = file_meta.get("sha256", "")

                    dest_path = os.path.join(self.save_dir, filename)

                    # Attempt AES decryption
                    try:
                        decrypted_data = self.crypto.aes_decrypt(total_encrypted, session_key, session_iv)
                        computed_sha256 = CryptoEngine.compute_sha256(decrypted_data)
                        integrity_passed = CryptoEngine.verify_integrity(computed_sha256, expected_sha256)
                    except Exception as e:
                        # PKCS#7 unpadding error or corruption caused by bit flipping / tamper
                        decrypted_data = b""
                        computed_sha256 = "DECRYPTION_CORRUPTED"
                        integrity_passed = False
                        self.log(f"Decryption integrity failure: {str(e)}", "SECURITY")

                    history_record = {
                        "direction": "INCOMING",
                        "sender": sender_name,
                        "filename": filename,
                        "filesize": len(decrypted_data) if integrity_passed else len(total_encrypted),
                        "expected_sha256": expected_sha256,
                        "computed_sha256": computed_sha256,
                        "status": "VERIFIED" if integrity_passed else "TAMPER_DETECTED",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "filepath": dest_path if integrity_passed else None
                    }
                    self.transfer_history.append(history_record)

                    if integrity_passed:
                        with open(dest_path, "wb") as f:
                            f.write(decrypted_data)

                        self.log(f"Integrity check PASSED! Computed SHA-256 matches expected digest.", "SUCCESS")
                        self.log(f"File safely written to: {dest_path}", "SUCCESS")

                        send_msg(sock, {
                            "type": MSG_VERIFY_RESULT,
                            "status": "SUCCESS",
                            "computed_sha256": computed_sha256,
                            "expected_sha256": expected_sha256,
                            "message": "File integrity and digital signature successfully verified."
                        })
                    else:
                        self.log(f"ALERT: SHA-256 INTEGRITY VIOLATION DETECTED! File tampered in transit!", "CRITICAL")
                        send_msg(sock, {
                            "type": MSG_VERIFY_RESULT,
                            "status": "TAMPER_DETECTED",
                            "computed_sha256": computed_sha256,
                            "expected_sha256": expected_sha256,
                            "message": "Integrity violation: Computed SHA-256 does not match expected digest!"
                        })
                    break

        except Exception as e:
            self.log(f"Socket handler error: {str(e)}", "ERROR")
        finally:
            sock.close()

    # -------------------------------------------------------------------------
    # Client (Sender Workflow)
    # -------------------------------------------------------------------------
    def send_file(
        self,
        target_host: str,
        target_port: int,
        filepath: str,
        simulate_tampering: bool = False
    ) -> Dict[str, Any]:
        """
        Connects to peer and securely transfers file via RSA + AES + SHA-256 protocol.
        Optionally simulates Man-in-the-Middle bit-flip attack to test detection.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Source file not found: {filepath}")

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)

        with open(filepath, "rb") as f:
            plaintext = f.read()

        # Step 1: Pre-transmission Plaintext Hashing with SHA-256
        plaintext_sha256 = CryptoEngine.compute_sha256(plaintext)
        self.log(f"Initiating transfer of '{filename}' ({filesize} bytes)", "INFO")
        self.log(f"Computed Original File SHA-256: {plaintext_sha256}", "CRYPTO")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((target_host, target_port))

        try:
            # Step 2: Asymmetric Handshake & RSA Public Key Exchange
            self.log(f"Connecting to peer {target_host}:{target_port}...", "INFO")
            send_msg(sock, {
                "type": MSG_HELLO,
                "sender_name": self.node_name,
                "public_key_pem": self.crypto.export_public_key_pem()
            })

            hello_ack = recv_msg(sock)
            if not hello_ack or hello_ack.get("type") != MSG_HELLO_ACK:
                raise ConnectionError("Invalid handshake response from peer")

            peer_name = hello_ack.get("receiver_name", "Remote-Peer")
            peer_pub_pem = hello_ack.get("public_key_pem", "")
            peer_pub_key = CryptoEngine.load_public_key_pem(peer_pub_pem)
            peer_fp = CryptoEngine.get_key_fingerprint(peer_pub_key)
            self.log(f"Handshake established with '{peer_name}' (Peer Fingerprint: {peer_fp})", "CRYPTO")

            # Step 3: Symmetric AES-256 Session Key Generation & RSA-OAEP Encryption
            session_key, session_iv = CryptoEngine.generate_aes_session_key()
            enc_session_key = CryptoEngine.rsa_encrypt_session_key(session_key, peer_pub_key)

            # Digitally sign (enc_key + session_iv) with Sender's RSA private key
            key_sig = self.crypto.sign_data(enc_session_key + session_iv)

            self.log("Generated fresh 256-bit AES session key & IV", "CRYPTO")
            self.log("Encrypted AES key using Peer's RSA-2048 Public Key (OAEP padding)", "CRYPTO")

            send_msg(sock, {
                "type": MSG_KEY_EXCHANGE,
                "encrypted_session_key": base64.b64encode(enc_session_key).decode("utf-8"),
                "iv": base64.b64encode(session_iv).decode("utf-8"),
                "signature": base64.b64encode(key_sig).decode("utf-8")
            })

            key_ack = recv_msg(sock)
            if not key_ack or key_ack.get("type") != MSG_KEY_EXCHANGE_ACK:
                raise ConnectionError("Key exchange was rejected by peer")
            self.log("Peer verified signature and accepted AES-256 session key", "CRYPTO")

            # Step 4: Send File Metadata & Authenticated Digest Header
            meta_str = f"{filename}:{filesize}:{plaintext_sha256}".encode("utf-8")
            meta_sig = self.crypto.sign_data(meta_str)

            send_msg(sock, {
                "type": MSG_FILE_HEADER,
                "filename": filename,
                "filesize": filesize,
                "sha256": plaintext_sha256,
                "signature": base64.b64encode(meta_sig).decode("utf-8")
            })

            # Step 5: AES-256-CBC Encryption
            ciphertext = self.crypto.aes_encrypt(plaintext, session_key, session_iv)
            self.log(f"Plaintext encrypted into {len(ciphertext)} bytes AES ciphertext", "CRYPTO")

            # Active Tamper Simulation (if enabled for laboratory demonstration)
            if simulate_tampering:
                self.log("[SIMULATION ACTIVE] Injecting Bit-Flip Tampering into Ciphertext!", "WARN")
                ciphertext = CryptoEngine.simulate_tampering(ciphertext, bit_flip_offset=24)

            # Step 6: Stream Ciphertext Chunks
            chunk_size = 32768  # 32 KB chunk streaming
            total_chunks = (len(ciphertext) + chunk_size - 1) // chunk_size

            for idx in range(total_chunks):
                start = idx * chunk_size
                chunk = ciphertext[start:start + chunk_size]
                send_msg(sock, {
                    "type": MSG_FILE_CHUNK,
                    "index": idx,
                    "total": total_chunks,
                    "data": base64.b64encode(chunk).decode("utf-8")
                })

            send_msg(sock, {"type": MSG_FILE_COMPLETE})
            self.log("Encrypted file payload transmitted. Awaiting integrity verification...", "INFO")

            # Step 7: Receive Verification ACK
            result_msg = recv_msg(sock)
            if not result_msg:
                raise ConnectionError("Peer closed connection before verification")

            status = result_msg.get("status", "UNKNOWN")
            comp_hash = result_msg.get("computed_sha256", "")

            history_record = {
                "direction": "OUTGOING",
                "recipient": peer_name,
                "filename": filename,
                "filesize": filesize,
                "expected_sha256": plaintext_sha256,
                "computed_sha256": comp_hash,
                "status": status,
                "tampered_simulation": simulate_tampering,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.transfer_history.append(history_record)

            if status == "SUCCESS":
                self.log(f"Peer verified SHA-256 integrity: MATCH ({comp_hash[:16]}...)", "SUCCESS")
            else:
                self.log(f"Peer flagged integrity violation: TAMPER DETECTED ({comp_hash})", "CRITICAL")

            return history_record

        finally:
            sock.close()

