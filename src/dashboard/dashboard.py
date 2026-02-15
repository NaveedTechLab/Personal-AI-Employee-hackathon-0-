#!/usr/bin/env python3
"""
Personal AI Employee - Web Dashboard
=====================================
Simple web interface to monitor and control the AI Employee.

Run: python dashboard.py
Open: http://localhost:8080
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Load environment
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent  # repo root
VAULT_PATH = PROJECT_ROOT / "demo_vault"

class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler for the dashboard."""

    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
            self.send_dashboard()
        elif self.path == "/api/status":
            self.send_api_status()
        elif self.path == "/api/emails":
            self.send_api_emails()
        elif self.path == "/api/pending":
            self.send_api_pending()
        elif self.path.startswith("/api/file/"):
            self.send_file_content()
        else:
            self.send_error(404, "Not Found")

    def send_json(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def send_api_status(self):
        """Send system status."""
        status = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                "gmail": "connected" if os.getenv("GMAIL_ADDRESS") else "not configured",
                "openrouter": "connected" if os.getenv("OPENAI_API_KEY") else "not configured",
                "linkedin": "configured" if os.getenv("LINKEDIN_CLIENT_ID") else "not configured",
                "twitter": "configured" if os.getenv("TWITTER_CLIENT_ID") else "not configured",
                "odoo": "configured" if os.getenv("ODOO_URL") else "not configured",
            },
            "vault_path": str(VAULT_PATH),
            "counts": self.get_counts()
        }
        self.send_json(status)

    def get_counts(self):
        """Get file counts from vault."""
        counts = {
            "needs_action": 0,
            "pending_approval": 0,
            "done": 0,
            "inbox": 0
        }

        for folder, key in [
            ("Needs_Action", "needs_action"),
            ("Pending_Approval", "pending_approval"),
            ("Done", "done"),
            ("Inbox", "inbox")
        ]:
            folder_path = VAULT_PATH / folder
            if folder_path.exists():
                counts[key] = len(list(folder_path.rglob("*.md")))

        return counts

    def send_api_emails(self):
        """Get processed emails."""
        emails = []
        email_path = VAULT_PATH / "Needs_Action" / "Gmail"

        if email_path.exists():
            for f in sorted(email_path.glob("*.md"), reverse=True)[:20]:
                content = f.read_text()
                # Parse frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        emails.append({
                            "filename": f.name,
                            "path": str(f),
                            "preview": parts[2][:200] if len(parts) > 2 else "",
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                        })

        self.send_json({"emails": emails, "count": len(emails)})

    def send_api_pending(self):
        """Get pending approvals."""
        pending = []
        pending_path = VAULT_PATH / "Pending_Approval"

        if pending_path.exists():
            for f in sorted(pending_path.glob("*.md"), reverse=True):
                pending.append({
                    "filename": f.name,
                    "path": str(f),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })

        self.send_json({"pending": pending, "count": len(pending)})

    def send_file_content(self):
        """Get file content."""
        filename = urllib.parse.unquote(self.path.replace("/api/file/", ""))
        filepath = VAULT_PATH / "Needs_Action" / "Gmail" / filename

        if filepath.exists() and filepath.is_file():
            self.send_json({
                "filename": filename,
                "content": filepath.read_text(),
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
            })
        else:
            self.send_json({"error": "File not found"})

    def send_dashboard(self):
        """Send the main dashboard HTML."""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal AI Employee - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { text-align: center; color: #888; margin-bottom: 40px; }

        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }

        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .card:hover { transform: translateY(-5px); box-shadow: 0 10px 40px rgba(0,212,255,0.2); }

        .card h3 { font-size: 0.9em; color: #888; margin-bottom: 10px; text-transform: uppercase; }
        .card .value { font-size: 2.5em; font-weight: bold; }
        .card.green .value { color: #00ff88; }
        .card.blue .value { color: #00d4ff; }
        .card.yellow .value { color: #ffcc00; }
        .card.red .value { color: #ff4757; }

        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .status-item {
            background: rgba(255,255,255,0.03);
            padding: 15px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; }
        .status-dot.green { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .status-dot.yellow { background: #ffcc00; }
        .status-dot.red { background: #ff4757; }

        .section { margin-bottom: 30px; }
        .section h2 { margin-bottom: 20px; font-size: 1.5em; }

        .email-list { background: rgba(255,255,255,0.03); border-radius: 15px; overflow: hidden; }
        .email-item {
            padding: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            cursor: pointer;
            transition: background 0.3s;
        }
        .email-item:hover { background: rgba(0,212,255,0.1); }
        .email-item h4 { margin-bottom: 5px; color: #00d4ff; }
        .email-item p { color: #888; font-size: 0.9em; }

        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1a2e;
            padding: 30px;
            border-radius: 15px;
            max-width: 800px;
            max-height: 80vh;
            overflow: auto;
            width: 90%;
        }
        .modal-close {
            float: right;
            font-size: 1.5em;
            cursor: pointer;
            color: #888;
        }
        .modal-close:hover { color: #fff; }
        pre {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
            overflow-x: auto;
            white-space: pre-wrap;
        }

        .refresh-btn {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            color: #fff;
            font-size: 1em;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover { opacity: 0.9; }

        .timestamp { text-align: center; color: #555; margin-top: 30px; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personal AI Employee</h1>
        <p class="subtitle">Autonomous Digital FTE Dashboard - Platinum Tier</p>

        <button class="refresh-btn" onclick="loadData()">Refresh Data</button>

        <div class="grid">
            <div class="card blue">
                <h3>Needs Action</h3>
                <div class="value" id="needs-action">-</div>
            </div>
            <div class="card yellow">
                <h3>Pending Approval</h3>
                <div class="value" id="pending-approval">-</div>
            </div>
            <div class="card green">
                <h3>Completed</h3>
                <div class="value" id="done">-</div>
            </div>
            <div class="card">
                <h3>Inbox</h3>
                <div class="value" id="inbox">-</div>
            </div>
        </div>

        <div class="section">
            <h2>Services Status</h2>
            <div class="status-grid" id="services-grid"></div>
        </div>

        <div class="section">
            <h2>Recent Emails (AI Processed)</h2>
            <div class="email-list" id="email-list">
                <div class="email-item"><p>Loading...</p></div>
            </div>
        </div>

        <p class="timestamp" id="timestamp"></p>
    </div>

    <div class="modal" id="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <h2 id="modal-title">Email Details</h2>
            <pre id="modal-content"></pre>
        </div>
    </div>

    <script>
        async function loadData() {
            // Load status
            const status = await fetch('/api/status').then(r => r.json());
            document.getElementById('needs-action').textContent = status.counts.needs_action;
            document.getElementById('pending-approval').textContent = status.counts.pending_approval;
            document.getElementById('done').textContent = status.counts.done;
            document.getElementById('inbox').textContent = status.counts.inbox;
            document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleString();

            // Load services
            const servicesGrid = document.getElementById('services-grid');
            servicesGrid.innerHTML = '';
            for (const [name, state] of Object.entries(status.services)) {
                const isGreen = state === 'connected' || state === 'configured';
                servicesGrid.innerHTML += `
                    <div class="status-item">
                        <div class="status-dot ${isGreen ? 'green' : 'yellow'}"></div>
                        <span>${name}: ${state}</span>
                    </div>
                `;
            }

            // Load emails
            const emails = await fetch('/api/emails').then(r => r.json());
            const emailList = document.getElementById('email-list');
            if (emails.emails.length === 0) {
                emailList.innerHTML = '<div class="email-item"><p>No processed emails yet</p></div>';
            } else {
                emailList.innerHTML = emails.emails.map(e => `
                    <div class="email-item" onclick="showFile('${e.filename}')">
                        <h4>${e.filename}</h4>
                        <p>${e.preview.substring(0, 100)}...</p>
                    </div>
                `).join('');
            }
        }

        async function showFile(filename) {
            const data = await fetch('/api/file/' + encodeURIComponent(filename)).then(r => r.json());
            document.getElementById('modal-title').textContent = filename;
            document.getElementById('modal-content').textContent = data.content || data.error;
            document.getElementById('modal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') closeModal();
        });

        // Load data on page load
        loadData();

        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>'''

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

def run_dashboard(port=9000):
    """Run the dashboard server."""
    print("=" * 60)
    print("  PERSONAL AI EMPLOYEE - WEB DASHBOARD")
    print("=" * 60)
    print(f"\n  Open in browser: http://localhost:{port}")
    print(f"  Or: http://127.0.0.1:{port}")
    print("\n  Press Ctrl+C to stop\n")
    print("=" * 60)

    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
        server.shutdown()

if __name__ == "__main__":
    run_dashboard()
