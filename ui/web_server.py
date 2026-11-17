"""
Web Application Dashboard for Authenticated P2P File Sharing (CSL-G53)
Provides a visual GUI for live demonstrations, cryptographic auditing,
and tamper detection evaluation using Python's standard library.
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from typing import Dict, Any

# Ensure project root is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from network.peer import P2PPeer
from crypto.engine import CryptoEngine


HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CSL-G53 | Authenticated P2P File Sharing</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #121826;
      --card-border: #1f293d;
      --cyan: #00f0ff;
      --neon-green: #00ff88;
      --red: #ff3366;
      --yellow: #ffd000;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --code-bg: #05080f;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; }
    body { background: var(--bg); color: var(--text); padding: 20px; line-height: 1.5; }
    .header {
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 24px; background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .header h1 { font-size: 20px; font-weight: 700; color: var(--cyan); letter-spacing: 0.5px; }
    .header .meta { font-size: 13px; color: var(--text-muted); text-align: right; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
    .full-grid { grid-column: span 2; }
    .card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }
    .card-title {
      font-size: 15px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 1px; color: var(--cyan); margin-bottom: 16px;
      display: flex; align-items: center; gap: 8px;
    }
    .badge {
      display: inline-block; padding: 4px 8px; border-radius: 6px;
      font-size: 11px; font-weight: 700; text-transform: uppercase;
    }
    .badge-success { background: rgba(0,255,136,0.15); color: var(--neon-green); border: 1px solid var(--neon-green); }
    .badge-danger { background: rgba(255,51,102,0.15); color: var(--red); border: 1px solid var(--red); }
    .badge-info { background: rgba(0,240,255,0.15); color: var(--cyan); border: 1px solid var(--cyan); }
    
    .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 13px; }
    .info-label { color: var(--text-muted); }
    .info-val { font-family: monospace; color: var(--text); }
    .fingerprint { color: var(--neon-green); word-break: break-all; font-size: 12px; }

    /* Form Styles */
    .form-group { margin-bottom: 14px; }
    .form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .form-control {
      width: 100%; padding: 10px 12px; background: var(--code-bg);
      border: 1px solid var(--card-border); border-radius: 8px; color: var(--text);
      font-size: 13px; outline: none; transition: border-color 0.2s;
    }
    .form-control:focus { border-color: var(--cyan); }
    .form-row { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }
    
    .btn {
      width: 100%; padding: 12px; background: linear-gradient(135deg, #0088cc, #00f0ff);
      border: none; border-radius: 8px; color: #000; font-weight: 700;
      cursor: pointer; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;
      transition: opacity 0.2s, transform 0.1s;
    }
    .btn:hover { opacity: 0.9; }
    .btn:active { transform: scale(0.99); }
    .btn-danger { background: linear-gradient(135deg, #cc0033, #ff3366); color: #fff; }

    .checkbox-label {
      display: flex; align-items: center; gap: 10px; cursor: pointer;
      font-size: 12px; color: var(--yellow); margin-top: 10px; margin-bottom: 16px;
      background: rgba(255,208,0,0.08); padding: 10px; border-radius: 8px; border: 1px solid rgba(255,208,0,0.2);
    }

    /* Terminal Console */
    .terminal {
      background: var(--code-bg); border: 1px solid var(--card-border);
      border-radius: 8px; padding: 12px; height: 260px; overflow-y: auto;
      font-family: "Consolas", monospace; font-size: 12px; line-height: 1.6;
    }
    .log-line { margin-bottom: 4px; }
    .log-INFO { color: #8b949e; }
    .log-SECURITY { color: #ffd000; }
    .log-CRYPTO { color: #00f0ff; }
    .log-SUCCESS { color: #00ff88; font-weight: bold; }
    .log-CRITICAL { color: #ff3366; font-weight: bold; }
    .log-WARN { color: #ffd000; font-weight: bold; }

    /* Pipeline Visualization */
    .pipeline {
      display: flex; justify-content: space-between; position: relative;
      margin: 20px 0; padding: 10px 0;
    }
    .step {
      display: flex; flex-direction: column; align-items: center;
      width: 18%; position: relative; z-index: 2;
    }
    .step-circle {
      width: 36px; height: 36px; border-radius: 50%;
      background: var(--code-bg); border: 2px solid var(--card-border);
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 700; color: var(--text-muted);
      transition: all 0.3s;
    }
    .step.active .step-circle { border-color: var(--cyan); color: var(--cyan); box-shadow: 0 0 12px rgba(0,240,255,0.4); }
    .step.done .step-circle { border-color: var(--neon-green); color: var(--neon-green); background: rgba(0,255,136,0.1); }
    .step.error .step-circle { border-color: var(--red); color: var(--red); background: rgba(255,51,102,0.1); }
    .step-label { font-size: 11px; color: var(--text-muted); margin-top: 8px; text-align: center; }

    /* Tables */
    table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
    th { padding: 10px; color: var(--text-muted); border-bottom: 1px solid var(--card-border); text-transform: uppercase; font-size: 11px; }
    td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.03); }
    .hash-cell { font-family: monospace; font-size: 11px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <h1>Authenticated P2P File Sharing (RSA + AES + SHA-256)</h1>
      <div style="font-size: 12px; color: var(--neon-green); margin-top: 4px;">
        RTU Cyber Security Lab (7CS4-22) — Project Code: CSL-G53
      </div>
    </div>
    <div class="meta">
      <div><strong>Student:</strong> Suman Kumar (23ESKCS822)</div>
      <div><strong>Batch:</strong> CS-D-G2 (CSE) | SKIT Jaipur</div>
      <div><strong>Supervisor:</strong> Vikash Dhankar, Asst. Prof.</div>
    </div>
  </div>

  <div class="grid">
    <!-- Node Status Card -->
    <div class="card">
      <div class="card-title">
        <span>Node Identity & Cryptographic Keys</span>
        <span class="badge badge-info" id="node-status">Online</span>
      </div>
      <div class="info-row">
        <span class="info-label">Peer Identity:</span>
        <span class="info-val" id="node-name">Loading...</span>
      </div>
      <div class="info-row">
        <span class="info-label">Listening Address:</span>
        <span class="info-val" id="node-addr">127.0.0.1:5001</span>
      </div>
      <div class="info-row">
        <span class="info-label">Asymmetric Algorithm:</span>
        <span class="info-val">RSA-2048 (OAEP Encryption + PSS Signing)</span>
      </div>
      <div class="info-row">
        <span class="info-label">Symmetric Cipher:</span>
        <span class="info-val">AES-256-CBC (PKCS#7 Padding)</span>
      </div>
      <div class="info-row">
        <span class="info-label">Integrity Algorithm:</span>
        <span class="info-val">SHA-256 (256-bit Digest)</span>
      </div>
      <div class="info-row" style="flex-direction: column; gap: 4px;">
        <span class="info-label">RSA-2048 Public Key Fingerprint:</span>
        <span class="fingerprint" id="node-fp">...</span>
      </div>
    </div>

    <!-- Send File Card -->
    <div class="card">
      <div class="card-title">
        <span>Encrypted P2P Transmission Station</span>
      </div>
      <form id="transfer-form" onsubmit="handleSend(event)">
        <div class="form-row">
          <div class="form-group">
            <label>Target Peer Host:</label>
            <input type="text" id="target-host" class="form-control" value="127.0.0.1" required>
          </div>
          <div class="form-group">
            <label>Target TCP Port:</label>
            <input type="number" id="target-port" class="form-control" value="5002" required>
          </div>
        </div>
        <div class="form-group">
          <label>Payload File Path / Sample File:</label>
          <input type="text" id="file-path" class="form-control" placeholder="shared_files/demo.txt" value="shared_files/demo.txt" required>
        </div>
        
        <label class="checkbox-label">
          <input type="checkbox" id="tamper-check">
          <span><strong>Simulate Man-in-the-Middle Attack:</strong> Inject bit-flip corruption in transit to evaluate SHA-256 tamper detection.</span>
        </label>

        <button type="submit" class="btn" id="send-btn">Initiate Authenticated Transfer</button>
      </form>
    </div>

    <!-- Cryptographic Pipeline Visualizer -->
    <div class="card full-grid">
      <div class="card-title">Cryptographic Lifecycle Pipeline</div>
      <div class="pipeline">
        <div class="step done" id="pipe-1">
          <div class="step-circle">1</div>
          <div class="step-label">RSA Handshake<br>& Key Exchange</div>
        </div>
        <div class="step done" id="pipe-2">
          <div class="step-circle">2</div>
          <div class="step-label">AES-256 Key<br>Encapsulation (OAEP)</div>
        </div>
        <div class="step done" id="pipe-3">
          <div class="step-circle">3</div>
          <div class="step-label">SHA-256 Plaintext<br>Digest Hashing</div>
        </div>
        <div class="step done" id="pipe-4">
          <div class="step-circle">4</div>
          <div class="step-label">AES-256-CBC Stream<br>Transmission</div>
        </div>
        <div class="step done" id="pipe-5">
          <div class="step-circle">5</div>
          <div class="step-label">Receiver Decrypt<br>& SHA-256 Check</div>
        </div>
      </div>
    </div>

    <!-- Live Event Terminal -->
    <div class="card">
      <div class="card-title">Security & Protocol Audit Log</div>
      <div class="terminal" id="terminal"></div>
    </div>

    <!-- Transfer History Table -->
    <div class="card">
      <div class="card-title">Audit History & Verification Records</div>
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Dir</th>
              <th>File</th>
              <th>Expected SHA-256</th>
              <th>Computed SHA-256</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="history-body">
            <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No transfers recorded yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    let lastLogCount = 0;

    async function updateStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('node-name').textContent = data.node_name;
        document.getElementById('node-addr').textContent = `${data.host}:${data.port}`;
        document.getElementById('node-fp').textContent = data.fingerprint;
      } catch (e) {
        console.error("Status fetch failed", e);
      }
    }

    async function updateLogs() {
      try {
        const res = await fetch('/api/logs');
        const logs = await res.json();
        const term = document.getElementById('terminal');
        term.innerHTML = logs.map(line => {
          let cls = 'log-INFO';
          if (line.includes('[SECURITY]')) cls = 'log-SECURITY';
          else if (line.includes('[CRYPTO]')) cls = 'log-CRYPTO';
          else if (line.includes('[SUCCESS]')) cls = 'log-SUCCESS';
          else if (line.includes('[CRITICAL]')) cls = 'log-CRITICAL';
          else if (line.includes('[WARN]')) cls = 'log-WARN';
          return `<div class="log-line ${cls}">${escapeHtml(line)}</div>`;
        }).join('');
        term.scrollTop = term.scrollHeight;
      } catch (e) {
        console.error("Log fetch failed", e);
      }
    }

    async function updateHistory() {
      try {
        const res = await fetch('/api/history');
        const history = await res.json();
        const tbody = document.getElementById('history-body');
        if (history.length === 0) return;

        tbody.innerHTML = history.slice().reverse().map(item => {
          const isVerified = item.status === 'SUCCESS' || item.status === 'VERIFIED';
          const badgeClass = isVerified ? 'badge-success' : 'badge-danger';
          const badgeText = isVerified ? 'VERIFIED' : 'TAMPER DETECTED';
          return `
            <tr>
              <td>${item.timestamp.split(' ')[1] || item.timestamp}</td>
              <td><span class="badge badge-info">${item.direction}</span></td>
              <td><strong>${escapeHtml(item.filename)}</strong></td>
              <td class="hash-cell" title="${item.expected_sha256}">${item.expected_sha256}</td>
              <td class="hash-cell" title="${item.computed_sha256}">${item.computed_sha256}</td>
              <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            </tr>
          `;
        }).join('');
      } catch (e) {
        console.error("History fetch failed", e);
      }
    }

    async function handleSend(e) {
      e.preventDefault();
      const sendBtn = document.getElementById('send-btn');
      sendBtn.disabled = true;
      sendBtn.textContent = "Executing Cryptographic Pipeline...";

      const targetHost = document.getElementById('target-host').value;
      const targetPort = parseInt(document.getElementById('target-port').value);
      const filePath = document.getElementById('file-path').value;
      const tamper = document.getElementById('tamper-check').checked;

      try {
        const res = await fetch('/api/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_host: targetHost,
            target_port: targetPort,
            filepath: filePath,
            tamper: tamper
          })
        });
        const result = await res.json();
        if (result.error) {
          alert("Transfer Failed: " + result.error);
        }
      } catch (err) {
        alert("Transfer Error: " + err.message);
      } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = "Initiate Authenticated Transfer";
        updateLogs();
        updateHistory();
      }
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Polling loops
    updateStatus();
    setInterval(updateLogs, 1000);
    setInterval(updateHistory, 1500);
  </script>
</body>
</html>
"""


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the Web UI."""

    peer_node: P2PPeer = None
    log_store = []

    def log_message(self, format, *args):
        # Suppress standard HTTP request logging in terminal to keep it clean
        pass

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))

        elif url.path == "/api/status":
            data = {
                "node_name": self.peer_node.node_name,
                "host": self.peer_node.host,
                "port": self.peer_node.port,
                "fingerprint": self.peer_node.fingerprint,
                "transfer_count": len(self.peer_node.transfer_history)
            }
            self._send_json(data)

        elif url.path == "/api/logs":
            self._send_json(self.log_store[-100:])

        elif url.path == "/api/history":
            self._send_json(self.peer_node.transfer_history)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/send":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                params = json.loads(body_bytes.decode("utf-8"))
                target_host = params.get("target_host", "127.0.0.1")
                target_port = int(params.get("target_port", 5002))
                filepath = params.get("filepath", "")
                tamper = bool(params.get("tamper", False))

                # Create sample file if filepath does not exist yet
                if not os.path.exists(filepath):
                    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(
                            f"Sample Cyber Security Payload - Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"Project CSL-G53: Authenticated P2P File Sharing\n"
                            f"Student: Suman Kumar (23ESKCS822)\n"
                            .encode("utf-8")
                        )

                # Execute transmission in background thread
                def _do_send():
                    try:
                        self.peer_node.send_file(
                            target_host=target_host,
                            target_port=target_port,
                            filepath=filepath,
                            simulate_tampering=tamper
                        )
                    except Exception as err:
                        self.peer_node.log(f"Send error: {str(err)}", "ERROR")

                threading.Thread(target=_do_send, daemon=True).start()
                self._send_json({"status": "Transfer initiated"})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def run_web_dashboard(
    peer_name: str = "Suman-Node",
    peer_port: int = 5001,
    web_port: int = 8080,
    save_dir: str = "received_files"
):
    """Launches P2P node and interactive web dashboard."""
    log_store = []

    def on_log(entry: str, level: str):
        log_store.append(entry)
        print(entry)

    # Initialize and start P2P node
    peer = P2PPeer(
        node_name=peer_name,
        host="127.0.0.1",
        port=peer_port,
        save_dir=save_dir,
        log_callback=on_log
    )
    peer.start_server()

    # Configure Web Server handler
    DashboardRequestHandler.peer_node = peer
    DashboardRequestHandler.log_store = log_store

    web_server = HTTPServer(("127.0.0.1", web_port), DashboardRequestHandler)
    print(f"\n" + "=" * 70)
    print(f" [*] CSL-G53 Web GUI running at: http://127.0.0.1:{web_port}")
    print(f" [*] P2P Peer listening at    : 127.0.0.1:{peer_port}")
    print(f" [*] RSA Fingerprint          : {peer.fingerprint}")
    print("=" * 70 + "\n")

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down servers...")
        peer.stop_server()
        web_server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="Suman-Node-1")
    parser.add_argument("--peer-port", type=int, default=5001)
    parser.add_argument("--web-port", type=int, default=8080)
    parser.add_argument("--save-dir", default="received_files")
    args = parser.parse_args()

    run_web_dashboard(
        peer_name=args.name,
        peer_port=args.peer_port,
        web_port=args.web_port,
        save_dir=args.save_dir
    )

