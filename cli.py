"""
Command-Line Interface (CLI) for Authenticated P2P File Sharing (CSL-G53)
Author: Suman Kumar (Roll No: 23ESKCS822)
Cyber Security Lab (7CS4-22) - RTU Kota / SKIT Jaipur
"""

import sys
import os
import argparse
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from network.peer import P2PPeer
from crypto.engine import CryptoEngine


def print_banner():
    banner = r"""
================================================================================
     AUTHENTICATED P2P FILE SHARING SYSTEM (RSA + AES + SHA-256)
     Course: Cyber Security Lab (7CS4-22) | Project Code: CSL-G53
     Student: Suman Kumar (Roll No: 23ESKCS822) | Batch: CS-D-G2
     Institution: SKIT Jaipur (RTU Kota)
================================================================================
    """
    print(banner)


def cmd_listen(args):
    print_banner()
    peer = P2PPeer(
        node_name=args.name,
        host=args.host,
        port=args.port,
        save_dir=args.save_dir
    )
    peer.start_server()
    print(f"[*] Node '{peer.node_name}' is listening on {peer.host}:{peer.port}")
    print(f"[*] RSA-2048 Public Key Fingerprint: {peer.fingerprint}")
    print(f"[*] Saved files destination: {os.path.abspath(peer.save_dir)}")
    print("[*] Press Ctrl+C to terminate node.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping listener daemon...")
        peer.stop_server()
        print("[*] Node terminated cleanly.")


def cmd_send(args):
    print_banner()
    if not os.path.exists(args.file):
        print(f"[!] Error: File '{args.file}' does not exist.")
        sys.exit(1)

    peer = P2PPeer(node_name=args.name, host="127.0.0.1", port=0)
    print(f"[*] Initiator: {peer.node_name}")
    print(f"[*] Target Peer: {args.target_host}:{args.target_port}")
    print(f"[*] File to Transfer: {args.file} ({os.path.getsize(args.file)} bytes)")
    if args.tamper:
        print("[!] WARNING: Tamper simulation active! Ciphertext will be modified in transit.")

    try:
        result = peer.send_file(
            target_host=args.target_host,
            target_port=args.target_port,
            filepath=args.file,
            simulate_tampering=args.tamper
        )

        print("\n" + "=" * 60)
        print("                 TRANSFER SUMMARY")
        print("=" * 60)
        print(f"Status           : {result['status']}")
        print(f"File Name        : {result['filename']}")
        print(f"File Size        : {result['filesize']} bytes")
        print(f"Expected SHA-256 : {result['expected_sha256']}")
        print(f"Computed SHA-256 : {result['computed_sha256']}")
        if result['status'] == "SUCCESS":
            print("[+] INTEGRITY VERIFIED: File received and authenticated without alteration.")
        else:
            print("[!] CRITICAL SECURITY ALERT: Tampering detected! Integrity check failed.")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"[!] Transfer failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Authenticated P2P File Sharing (RSA + AES + SHA-256) - CSL-G53"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operational mode")

    # Listener mode parser
    listen_parser = subparsers.add_parser("listen", help="Run node in listening mode to receive files")
    listen_parser.add_argument("--name", default="Peer-Bob", help="Node friendly name")
    listen_parser.add_argument("--host", default="0.0.0.0", help="Binding host IP (default: 0.0.0.0)")
    listen_parser.add_argument("--port", type=int, default=5001, help="Binding TCP port (default: 5001)")
    listen_parser.add_argument("--save-dir", default="received_files", help="Folder to store received files")

    # Sender mode parser
    send_parser = subparsers.add_parser("send", help="Send an encrypted file to a remote peer")
    send_parser.add_argument("--name", default="Peer-Alice", help="Sender friendly name")
    send_parser.add_argument("--target-host", default="127.0.0.1", help="Target peer IP address")
    send_parser.add_argument("--target-port", type=int, default=5001, help="Target peer TCP port")
    send_parser.add_argument("--file", required=True, help="Path to file to transmit")
    send_parser.add_argument("--tamper", action="store_true", help="Simulate active bit-flip attack on ciphertext")

    args = parser.parse_args()

    if args.command == "listen":
        cmd_listen(args)
    elif args.command == "send":
        cmd_send(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

