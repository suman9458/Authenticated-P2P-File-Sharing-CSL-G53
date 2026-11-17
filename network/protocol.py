"""
Framed Protocol Specification for Authenticated P2P File Transfer (CSL-G53)
Implements length-prefixed JSON messaging over TCP sockets.
"""

import json
import struct
import socket
from typing import Optional, Dict, Any


# 4-byte network byte-order integer for frame length
HEADER_STRUCT = struct.Struct(">I")
HEADER_SIZE = HEADER_STRUCT.size

# Protocol Message Types
MSG_HELLO = "HELLO"
MSG_HELLO_ACK = "HELLO_ACK"
MSG_KEY_EXCHANGE = "KEY_EXCHANGE"
MSG_KEY_EXCHANGE_ACK = "KEY_EXCHANGE_ACK"
MSG_FILE_HEADER = "FILE_HEADER"
MSG_FILE_CHUNK = "FILE_CHUNK"
MSG_FILE_COMPLETE = "FILE_COMPLETE"
MSG_VERIFY_RESULT = "VERIFY_RESULT"
MSG_ERROR = "ERROR"


def send_msg(sock: socket.socket, msg_dict: Dict[str, Any]) -> None:
    """Encodes and sends a length-prefixed JSON message over the socket."""
    json_bytes = json.dumps(msg_dict).encode("utf-8")
    header = HEADER_STRUCT.pack(len(json_bytes))
    sock.sendall(header + json_bytes)


def recv_msg(sock: socket.socket) -> Optional[Dict[str, Any]]:
    """Receives a length-prefixed JSON message from the socket."""
    header_data = _recv_all(sock, HEADER_SIZE)
    if not header_data:
        return None

    msg_len = HEADER_STRUCT.unpack(header_data)[0]
    json_bytes = _recv_all(sock, msg_len)
    if not json_bytes:
        return None

    return json.loads(json_bytes.decode("utf-8"))


def _recv_all(sock: socket.socket, length: int) -> Optional[bytes]:
    """Helper to receive exact number of bytes across multiple TCP chunks."""
    buffer = bytearray()
    while len(buffer) < length:
        packet = sock.recv(length - len(buffer))
        if not packet:
            return None
        buffer.extend(packet)
    return bytes(buffer)

