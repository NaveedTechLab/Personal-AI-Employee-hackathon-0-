#!/usr/bin/env python3
"""
Personal AI Employee - Interactive Dashboard (Full-Featured)
=============================================================
Production-ready web dashboard with Gmail, Twitter, LinkedIn,
WhatsApp, Odoo ERP, Meta, AI Assistant, and Vault management.

Run: python interactive_dashboard.py
Open: http://localhost:9000
"""

import os
import sys
import json
import time
import imaplib
import smtplib
import email
import hashlib
import hmac
import base64
import shutil
import traceback
import urllib.parse
import urllib.request
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Load environment
from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent  # repo root
VAULT_PATH = PROJECT_ROOT / "demo_vault"

# ============================================================
# EMAIL MANAGER - Gmail IMAP/SMTP
# ============================================================
class EmailManager:
    """Manages Gmail integration via IMAP and SMTP."""

    def __init__(self):
        self.address = os.getenv("GMAIL_ADDRESS", "")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD", "")
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def is_configured(self):
        return bool(self.address and self.app_password)

    def fetch_emails(self, count=20):
        """Fetch recent emails via IMAP."""
        if not self.is_configured():
            return {"emails": [], "error": "Gmail not configured"}
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, timeout=5)
            mail.login(self.address, self.app_password)
            mail.select("INBOX")
            _, data = mail.search(None, "ALL")
            ids = data[0].split()
            ids = ids[-count:] if len(ids) > count else ids
            ids.reverse()

            emails = []
            for eid in ids[:count]:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                if msg_data[0] is None:
                    continue
                msg = email.message_from_bytes(msg_data[0][1])
                subject = str(email.header.decode_header(msg["Subject"])[0][0] or "")
                if isinstance(subject, bytes):
                    subject = subject.decode("utf-8", errors="replace")
                sender = msg.get("From", "Unknown")
                date_str = msg.get("Date", "")
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="replace")[:500]
                            break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")[:500]

                emails.append({
                    "id": eid.decode(),
                    "subject": subject,
                    "from": sender,
                    "date": date_str,
                    "preview": body[:200]
                })

            mail.logout()
            return {"emails": emails, "count": len(emails)}
        except Exception as e:
            return {"emails": [], "error": str(e)}

    def send_email(self, to, subject, body):
        """Send email via SMTP."""
        if not self.is_configured():
            return {"success": False, "error": "Gmail not configured"}
        try:
            msg = MIMEMultipart()
            msg["From"] = self.address
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.address, self.app_password)
            server.send_message(msg)
            server.quit()
            return {"success": True, "message": f"Email sent to {to}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# SOCIAL MANAGER - Twitter/X OAuth 1.0a
# ============================================================
class SocialManager:
    """Manages Twitter/X integration with OAuth 1.0a signing."""

    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        self.api_base = "https://api.twitter.com"

    def is_configured(self):
        return bool(self.api_key and self.api_secret and self.access_token and self.access_secret)

    def _percent_encode(self, s):
        return urllib.parse.quote(str(s), safe="")

    def _generate_nonce(self):
        return hashlib.md5(str(time.time()).encode()).hexdigest()

    def _generate_signature(self, method, url, params):
        """Generate OAuth 1.0a signature."""
        sorted_params = "&".join(
            f"{self._percent_encode(k)}={self._percent_encode(v)}"
            for k, v in sorted(params.items())
        )
        base_string = f"{method}&{self._percent_encode(url)}&{self._percent_encode(sorted_params)}"
        signing_key = f"{self._percent_encode(self.api_secret)}&{self._percent_encode(self.access_secret)}"
        signature = hmac.new(
            signing_key.encode(), base_string.encode(), hashlib.sha1
        )
        return base64.b64encode(signature.digest()).decode()

    def post_tweet(self, text):
        """Post a tweet using Twitter API v2."""
        if not self.is_configured():
            return {"success": False, "error": "Twitter not configured"}
        try:
            url = f"{self.api_base}/2/tweets"
            oauth_params = {
                "oauth_consumer_key": self.api_key,
                "oauth_nonce": self._generate_nonce(),
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_timestamp": str(int(time.time())),
                "oauth_token": self.access_token,
                "oauth_version": "1.0",
            }
            signature = self._generate_signature("POST", url, oauth_params)
            oauth_params["oauth_signature"] = signature

            auth_header = "OAuth " + ", ".join(
                f'{self._percent_encode(k)}="{self._percent_encode(v)}"'
                for k, v in sorted(oauth_params.items())
            )

            payload = json.dumps({"text": text}).encode()
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Authorization", auth_header)
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
            return {"success": True, "tweet": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# WHATSAPP MANAGER - Vault-based message handling
# ============================================================
class WhatsAppManager:
    """Manages WhatsApp messages from the demo vault."""

    KEYWORDS = ["urgent", "help", "asap", "meeting", "invoice"]

    def __init__(self):
        self.message_path = VAULT_PATH / "Needs_Action" / "WhatsApp"

    def get_messages(self):
        """List WhatsApp message files from vault."""
        messages = []
        if not self.message_path.exists():
            return {"messages": [], "count": 0}

        for f in sorted(self.message_path.glob("*.md"), reverse=True):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                priority = "normal"
                for kw in self.KEYWORDS:
                    if kw.lower() in content.lower():
                        priority = "high"
                        break

                messages.append({
                    "filename": f.name,
                    "path": str(f),
                    "content": content[:500],
                    "priority": priority,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
            except Exception:
                pass

        return {"messages": messages, "count": len(messages)}

    def process_message(self, filename):
        """Process (acknowledge) a WhatsApp message."""
        src = self.message_path / filename
        if not src.exists():
            return {"success": False, "error": "Message not found"}
        try:
            done_path = VAULT_PATH / "Done" / "WhatsApp"
            done_path.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(done_path / filename))
            return {"success": True, "message": f"Processed: {filename}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_test_message(self, sender="Test User", text="Hello, this is a test message"):
        """Create a test WhatsApp message in the vault."""
        self.message_path.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"whatsapp_{ts}.md"
        content = f"""---
source: whatsapp
sender: {sender}
timestamp: {datetime.now().isoformat()}
status: needs_action
---

# WhatsApp Message from {sender}

{text}
"""
        (self.message_path / filename).write_text(content)
        return {"success": True, "filename": filename}


# ============================================================
# ODOO MANAGER - Full ERP integration with caching
# ============================================================
class OdooManager:
    """Manages Odoo ERP integration with status caching."""

    def __init__(self):
        self.url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.database = os.getenv("ODOO_DATABASE", os.getenv("ODOO_DB", ""))
        self.username = os.getenv("ODOO_USERNAME", "admin")
        self.api_key = os.getenv("ODOO_API_KEY", "")
        self._status_cache = None
        self._status_cache_time = 0
        self._CACHE_TTL = 30  # seconds

    def is_configured(self):
        return bool(self.url and self.database)

    def _fetch(self, endpoint, timeout=3):
        """Fetch data from Odoo API endpoint."""
        try:
            url = f"{self.url}/api/{endpoint}"
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}

    def get_status(self):
        """Get Odoo connection status with 30-second cache."""
        now = time.time()
        if self._status_cache and (now - self._status_cache_time) < self._CACHE_TTL:
            return self._status_cache
        try:
            url = f"{self.url}/api/summary"
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
            self._status_cache = {"connected": True, "data": data}
            self._status_cache_time = now
            return self._status_cache
        except Exception as e:
            result = {"connected": False, "error": str(e)}
            self._status_cache = result
            self._status_cache_time = now
            return result

    def get_dashboard(self):
        return self._fetch("summary")

    def get_invoices(self):
        return self._fetch("invoices")

    def get_orders(self):
        return self._fetch("orders")

    def get_partners(self):
        return self._fetch("partners")

    def get_employees(self):
        return self._fetch("employees")

    def get_leads(self):
        return self._fetch("leads")

    def get_expenses(self):
        return self._fetch("expenses")

    def get_products(self):
        return self._fetch("products")

    def get_projects(self):
        return self._fetch("projects")

    def get_payments(self):
        return self._fetch("payments")

    def get_attendance(self):
        return self._fetch("attendance")

    def get_leaves(self):
        return self._fetch("leaves")

    def get_purchases(self):
        return self._fetch("purchase")


# ============================================================
# AI HELPER - OpenRouter API
# ============================================================
class AIHelper:
    """AI assistant using OpenRouter API."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    def is_configured(self):
        return bool(self.api_key)

    def suggest(self, prompt, context=""):
        """Generate AI response via OpenRouter."""
        if not self.is_configured():
            return {"success": False, "error": "AI not configured (OPENAI_API_KEY missing)"}
        try:
            url = f"{self.base_url}/chat/completions"
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})

            payload = json.dumps({
                "model": self.model,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            }).encode()

            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())

            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            return {"success": True, "response": reply, "model": self.model}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# VAULT MANAGER - File operations
# ============================================================
class VaultManager:
    """Manages the demo vault file system."""

    FOLDERS = ["Inbox", "Needs_Action", "Pending_Approval", "Done", "Approved", "Rejected"]

    def __init__(self):
        self.root = VAULT_PATH

    def get_counts(self):
        counts = {}
        for folder in self.FOLDERS:
            folder_path = self.root / folder
            if folder_path.exists():
                counts[folder.lower()] = len(list(folder_path.rglob("*.md")))
            else:
                counts[folder.lower()] = 0
        return counts

    def list_files(self):
        """List files in all vault subfolders."""
        result = {}
        for folder in self.FOLDERS:
            folder_path = self.root / folder
            files = []
            if folder_path.exists():
                for f in sorted(folder_path.rglob("*.md"), reverse=True):
                    files.append({
                        "filename": f.name,
                        "path": str(f.relative_to(self.root)),
                        "folder": folder,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        "size": f.stat().st_size
                    })
            result[folder.lower()] = files
        return result

    def get_pending(self):
        """Get items in Pending_Approval."""
        pending = []
        pending_path = self.root / "Pending_Approval"
        if pending_path.exists():
            for f in sorted(pending_path.rglob("*.md"), reverse=True):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    content = ""
                pending.append({
                    "filename": f.name,
                    "path": str(f),
                    "relative_path": str(f.relative_to(self.root)),
                    "preview": content[:300],
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        return {"pending": pending, "count": len(pending)}

    def approve_item(self, filename):
        """Move item from Pending_Approval to Approved."""
        return self._move_item(filename, "Pending_Approval", "Approved")

    def reject_item(self, filename):
        """Move item from Pending_Approval to Rejected."""
        return self._move_item(filename, "Pending_Approval", "Rejected")

    def _move_item(self, filename, src_folder, dst_folder):
        src = self.root / src_folder / filename
        if not src.exists():
            # Try recursive search
            found = list((self.root / src_folder).rglob(filename))
            if found:
                src = found[0]
            else:
                return {"success": False, "error": f"File not found: {filename}"}
        dst_dir = self.root / dst_folder
        dst_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst_dir / src.name))
            return {"success": True, "message": f"Moved {filename} to {dst_folder}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================================
# Initialize service managers
# ============================================================
email_manager = EmailManager()
social_manager = SocialManager()
whatsapp_manager = WhatsAppManager()
odoo_manager = OdooManager()
ai_helper = AIHelper()
vault_manager = VaultManager()


# ============================================================
# THREADED HTTP SERVER + REQUEST HANDLER
# ============================================================
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True


class DashboardHandler(BaseHTTPRequestHandler):
    """Full-featured interactive dashboard HTTP handler."""

    # Suppress default logging to avoid console spam
    def log_message(self, format, *args):
        pass

    def end_headers(self):
        """Override to add Connection: close on every response."""
        self.send_header("Connection", "close")
        super().end_headers()

    def send_json(self, data, status=200):
        """Send JSON response with Content-Length."""
        body = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        """Send HTML response with Content-Length."""
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    # ---- ROUTING ----

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/" or path == "/dashboard":
                self.send_html(self._build_html())
            elif path == "/api/status":
                self._handle_status()
            elif path == "/api/emails":
                self._handle_get_emails()
            elif path == "/api/whatsapp":
                self._handle_get_whatsapp()
            elif path == "/api/vault":
                self._handle_get_vault()
            elif path == "/api/pending":
                self._handle_get_pending()
            elif path == "/api/odoo/dashboard" or path == "/api/odoo/summary":
                self._handle_odoo_section("summary")
            elif path.startswith("/api/odoo/"):
                section = path.replace("/api/odoo/", "").strip("/")
                self._handle_odoo_section(section)
            elif path == "/linkedin/callback":
                self._handle_linkedin_callback()
            elif path.startswith("/api/vault/browse"):
                self._handle_vault_browse()
            elif path.startswith("/api/vault/file"):
                self._handle_vault_file()
            elif path.startswith("/api/file/"):
                self._handle_get_file()
            else:
                self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            body = self._read_body()
            if path == "/api/send-email":
                self._handle_send_email(body)
            elif path == "/api/post-twitter":
                self._handle_post_twitter(body)
            elif path == "/api/post-linkedin":
                self._handle_post_linkedin(body)
            elif path == "/api/whatsapp-process":
                self._handle_whatsapp_process(body)
            elif path == "/api/whatsapp-test":
                self._handle_whatsapp_test(body)
            elif path == "/api/ai-suggest":
                self._handle_ai_suggest(body)
            elif path == "/api/generate-post":
                self._handle_generate_post(body)
            elif path == "/api/save-draft":
                self._handle_save_draft(body)
            elif path == "/api/vault/move":
                self._handle_vault_move(body)
            elif path == "/api/approve":
                self._handle_approve(body)
            elif path == "/api/reject":
                self._handle_reject(body)
            else:
                self.send_json({"error": "Not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    # ---- GET HANDLERS ----

    def _handle_status(self):
        """Full system status for all services."""
        odoo_status = odoo_manager.get_status()
        meta_token = os.getenv("META_PAGE_ACCESS_TOKEN", os.getenv("META_ACCESS_TOKEN", ""))
        meta_configured = bool(meta_token and "your_" not in meta_token)

        status = {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "services": {
                "gmail": "connected" if email_manager.is_configured() else "not configured",
                "twitter": "connected" if social_manager.is_configured() else "not configured",
                "linkedin": "connected" if os.getenv("LINKEDIN_ACCESS_TOKEN") else "not configured",
                "whatsapp": "connected",
                "odoo": "connected" if odoo_status.get("connected") else "error",
                "meta": "connected" if meta_configured else "not configured",
                "ai_assistant": "connected" if ai_helper.is_configured() else "not configured",
            },
            "vault_path": str(VAULT_PATH),
            "counts": vault_manager.get_counts()
        }
        self.send_json(status)

    def _handle_get_emails(self):
        """Return only vault-imported emails from Needs_Action/Gmail/, parsed from frontmatter."""
        vault_emails = []
        email_path = VAULT_PATH / "Needs_Action" / "Gmail"
        if email_path.exists():
            for f in sorted(email_path.glob("*.md"), reverse=True)[:20]:
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    meta = self._parse_email_vault_file(content)
                    vault_emails.append({
                        "filename": f.name,
                        "subject": meta.get("subject", f.stem.replace("_", " ")),
                        "from": meta.get("from", meta.get("sender", "")),
                        "date": meta.get("date", meta.get("created", "")),
                        "preview": meta.get("preview", meta.get("subject", f.stem.replace("_", " "))),
                        "priority": meta.get("priority", "normal"),
                        "status": meta.get("status", "needs_action"),
                        "ai_intent": meta.get("ai_intent", ""),
                        "source": "vault",
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
                except Exception:
                    pass

        self.send_json({
            "emails": vault_emails,
            "count": len(vault_emails)
        })

    @staticmethod
    def _parse_email_vault_file(content):
        """Parse YAML frontmatter and markdown table from a vault email file."""
        meta = {}
        lines = content.split("\n")

        # Parse YAML frontmatter
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    break
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip().lower()
                    val = val.strip()
                    if key in ("type", "priority", "status", "created", "source", "ai_intent", "sender", "subject", "date"):
                        meta[key] = val

        # Parse markdown table for From, Subject, Date
        for line in lines:
            if line.startswith("| **From**"):
                parts = line.split("|")
                if len(parts) >= 3:
                    meta["from"] = parts[2].strip()
            elif line.startswith("| **Subject**"):
                parts = line.split("|")
                if len(parts) >= 3:
                    meta["subject"] = parts[2].strip()
            elif line.startswith("| **Date**"):
                parts = line.split("|")
                if len(parts) >= 3:
                    meta["date"] = parts[2].strip()

        # Build preview from content after frontmatter
        preview_lines = []
        in_frontmatter = False
        past_frontmatter = False
        for line in lines:
            if line.strip() == "---" and not past_frontmatter:
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    past_frontmatter = True
                continue
            if not past_frontmatter:
                continue
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("|") \
                    and not stripped.startswith("**From") and not stripped.startswith("**Date") \
                    and not stripped.startswith("**Subject") and not stripped.startswith("- [") \
                    and not stripped.startswith(">"):
                preview_lines.append(stripped)
        if preview_lines:
            meta["preview"] = " ".join(preview_lines)[:200]

        return meta

    def _handle_get_whatsapp(self):
        self.send_json(whatsapp_manager.get_messages())

    def _handle_get_vault(self):
        self.send_json(vault_manager.list_files())

    def _handle_get_pending(self):
        self.send_json(vault_manager.get_pending())

    def _handle_get_file(self):
        filename = urllib.parse.unquote(self.path.replace("/api/file/", ""))
        # Search in multiple locations
        for folder in ["Needs_Action/Gmail", "Needs_Action/WhatsApp", "Needs_Action",
                        "Pending_Approval", "Inbox", "Done"]:
            fp = VAULT_PATH / folder / filename
            if fp.exists():
                self.send_json({
                    "filename": filename,
                    "content": fp.read_text(encoding="utf-8", errors="replace"),
                    "modified": datetime.fromtimestamp(fp.stat().st_mtime).isoformat()
                })
                return
        self.send_json({"error": "File not found"}, 404)

    def _handle_odoo_section(self, section):
        """Handle all Odoo ERP data endpoints."""
        section_map = {
            "summary": odoo_manager.get_dashboard,
            "dashboard": odoo_manager.get_dashboard,
            "invoices": odoo_manager.get_invoices,
            "orders": odoo_manager.get_orders,
            "partners": odoo_manager.get_partners,
            "employees": odoo_manager.get_employees,
            "leads": odoo_manager.get_leads,
            "expenses": odoo_manager.get_expenses,
            "products": odoo_manager.get_products,
            "projects": odoo_manager.get_projects,
            "payments": odoo_manager.get_payments,
            "attendance": odoo_manager.get_attendance,
            "leaves": odoo_manager.get_leaves,
            "purchases": odoo_manager.get_purchases,
        }
        handler = section_map.get(section)
        if handler:
            self.send_json(handler())
        else:
            self.send_json({"error": f"Unknown Odoo section: {section}"}, 404)

    def _handle_linkedin_callback(self):
        """LinkedIn OAuth callback handler."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get("code", [None])[0]
        if code:
            self.send_html(f"""<!DOCTYPE html><html><body style="background:#1a1a2e;color:#fff;
                font-family:sans-serif;text-align:center;padding:60px;">
                <h1>LinkedIn Authorization</h1>
                <p>Authorization code received: <code>{code[:20]}...</code></p>
                <p>You can close this window.</p>
                <script>setTimeout(function(){{ window.close(); }}, 3000);</script>
                </body></html>""")
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_html(f"""<!DOCTYPE html><html><body style="background:#1a1a2e;color:#fff;
                font-family:sans-serif;text-align:center;padding:60px;">
                <h1>LinkedIn Error</h1><p>Error: {error}</p></body></html>""")

    # ---- POST HANDLERS ----

    def _handle_send_email(self, body):
        to = body.get("to", "")
        subject = body.get("subject", "")
        text = body.get("body", "")
        if not to or not subject:
            self.send_json({"success": False, "error": "Missing 'to' or 'subject'"}, 400)
            return
        self.send_json(email_manager.send_email(to, subject, text))

    def _handle_post_twitter(self, body):
        text = body.get("text", "")
        if not text:
            self.send_json({"success": False, "error": "Missing 'text'"}, 400)
            return
        self.send_json(social_manager.post_tweet(text))

    def _handle_post_linkedin(self, body):
        """Post to LinkedIn using access token."""
        text = body.get("text", "")
        if not text:
            self.send_json({"success": False, "error": "Missing 'text'"}, 400)
            return

        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        if not access_token:
            self.send_json({"success": False, "error": "LinkedIn access token not configured"})
            return

        try:
            # Get user profile URN
            profile_url = "https://api.linkedin.com/v2/userinfo"
            req = urllib.request.Request(profile_url)
            req.add_header("Authorization", f"Bearer {access_token}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                profile = json.loads(resp.read().decode())
            person_urn = f"urn:li:person:{profile.get('sub', '')}"

            # Create post
            post_url = "https://api.linkedin.com/v2/ugcPosts"
            payload = json.dumps({
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }).encode()

            req = urllib.request.Request(post_url, data=payload, method="POST")
            req.add_header("Authorization", f"Bearer {access_token}")
            req.add_header("Content-Type", "application/json")
            req.add_header("X-Restli-Protocol-Version", "2.0.0")

            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
            self.send_json({"success": True, "post": result})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)})

    def _handle_whatsapp_process(self, body):
        filename = body.get("filename", "")
        if not filename:
            self.send_json({"success": False, "error": "Missing 'filename'"}, 400)
            return
        self.send_json(whatsapp_manager.process_message(filename))

    def _handle_whatsapp_test(self, body):
        sender = body.get("sender", "Test User")
        text = body.get("text", "Hello, this is a test message")
        self.send_json(whatsapp_manager.create_test_message(sender, text))

    def _handle_ai_suggest(self, body):
        prompt = body.get("prompt", "")
        context = body.get("context", "You are a helpful AI assistant for a business professional.")
        if not prompt:
            self.send_json({"success": False, "error": "Missing 'prompt'"}, 400)
            return
        self.send_json(ai_helper.suggest(prompt, context))

    def _handle_approve(self, body):
        filename = body.get("filename", "")
        if not filename:
            self.send_json({"success": False, "error": "Missing 'filename'"}, 400)
            return
        self.send_json(vault_manager.approve_item(filename))

    def _handle_reject(self, body):
        filename = body.get("filename", "")
        if not filename:
            self.send_json({"success": False, "error": "Missing 'filename'"}, 400)
            return
        self.send_json(vault_manager.reject_item(filename))

    def _handle_generate_post(self, body):
        """Generate AI social media post content."""
        platform = body.get("platform", "twitter")
        topic = body.get("topic", "")

        if platform == "twitter":
            max_chars = "280 characters"
            style = "concise, engaging, with relevant hashtags"
        elif platform == "linkedin":
            max_chars = "1000 characters"
            style = "professional, insightful, thought-leadership tone"
        else:
            max_chars = "500 characters"
            style = "engaging, casual but professional"

        prompt = (
            f"Generate a {platform} post for a business/tech professional.\n"
            f"Topic: {topic if topic else 'AI and automation in business, productivity tips, or tech industry insights'}\n"
            f"Style: {style}\nMax length: {max_chars}\n"
            f"Include relevant hashtags.\nOutput ONLY the post text, nothing else."
        )
        result = ai_helper.suggest(prompt, "You are a social media content expert.")
        if result.get("success"):
            self.send_json({"success": True, "content": result["response"], "platform": platform})
        else:
            self.send_json({"success": False, "error": result.get("error", "AI generation failed")})

    def _handle_save_draft(self, body):
        """Save content as a draft markdown file in Pending_Approval."""
        platform = body.get("platform", "social")
        content = body.get("content", "")
        if not content:
            self.send_json({"success": False, "error": "Missing 'content'"}, 400)
            return

        pending_dir = VAULT_PATH / "Pending_Approval"
        pending_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        filename = f"SOCIAL_{platform}_draft_{now.strftime('%Y%m%d_%H%M%S')}.md"

        draft = f"""---
type: social_post
platform: {platform}
status: pending_approval
generated: {now.isoformat()}
---

# {platform.title()} Post Draft

## Post Content
{content}

## Actions
- Edit the content above if needed
- Move this file to `Approved/` to post
- Move to `Rejected/` to discard

> AI-generated draft at {now.strftime('%Y-%m-%d %H:%M:%S')}
"""
        filepath = pending_dir / filename
        filepath.write_text(draft, encoding="utf-8")
        self.send_json({"success": True, "filename": filename, "path": str(filepath)})

    def _handle_vault_browse(self):
        """List files in a specific vault folder."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        folder = params.get("folder", ["Needs_Action"])[0]

        # Sanitize folder name
        allowed = {"Inbox", "Needs_Action", "Pending_Approval", "Done", "Approved", "Rejected"}
        if folder not in allowed:
            self.send_json({"error": f"Invalid folder: {folder}"}, 400)
            return

        folder_path = VAULT_PATH / folder
        files = []
        if folder_path.exists():
            for f in sorted(folder_path.rglob("*.md"), reverse=True):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    meta = {}
                    lines = content.split("\n")
                    if lines and lines[0].strip() == "---":
                        for line in lines[1:]:
                            if line.strip() == "---":
                                break
                            if ":" in line:
                                k, _, v = line.partition(":")
                                meta[k.strip().lower()] = v.strip()
                    files.append({
                        "filename": f.name,
                        "path": str(f.relative_to(VAULT_PATH)),
                        "subfolder": str(f.parent.relative_to(VAULT_PATH)),
                        "type": meta.get("type", "unknown"),
                        "priority": meta.get("priority", "normal"),
                        "status": meta.get("status", ""),
                        "created": meta.get("created", ""),
                        "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        "size": f.stat().st_size
                    })
                except Exception:
                    pass
        self.send_json({"folder": folder, "files": files, "count": len(files)})

    def _handle_vault_file(self):
        """Get full content of a vault file with parsed frontmatter."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        rel_path = params.get("path", [""])[0]
        if not rel_path:
            self.send_json({"error": "Missing 'path' parameter"}, 400)
            return

        # Prevent path traversal
        safe_path = VAULT_PATH / rel_path
        try:
            safe_path = safe_path.resolve()
            vault_resolved = VAULT_PATH.resolve()
            if not str(safe_path).startswith(str(vault_resolved)):
                self.send_json({"error": "Invalid path"}, 400)
                return
        except Exception:
            self.send_json({"error": "Invalid path"}, 400)
            return

        if not safe_path.exists():
            self.send_json({"error": "File not found"}, 404)
            return

        content = safe_path.read_text(encoding="utf-8", errors="replace")
        meta = {}
        lines = content.split("\n")
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip().lower()] = v.strip()

        self.send_json({
            "filename": safe_path.name,
            "path": rel_path,
            "content": content,
            "meta": meta,
            "modified": datetime.fromtimestamp(safe_path.stat().st_mtime).isoformat()
        })

    def _handle_vault_move(self, body):
        """Move a file between vault folders."""
        filename = body.get("filename", "")
        from_folder = body.get("from_folder", "")
        to_folder = body.get("to_folder", "")
        if not filename or not from_folder or not to_folder:
            self.send_json({"success": False, "error": "Missing filename, from_folder, or to_folder"}, 400)
            return

        allowed = {"Inbox", "Needs_Action", "Pending_Approval", "Done", "Approved", "Rejected"}
        if from_folder not in allowed or to_folder not in allowed:
            self.send_json({"success": False, "error": "Invalid folder name"}, 400)
            return

        self.send_json(vault_manager._move_item(filename, from_folder, to_folder))

    # ============================================================
    # FRONTEND HTML
    # ============================================================
    def _build_html(self):
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal AI Employee - Interactive Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 1.6em;
            color: #fff;
            font-weight: 700;
        }
        .header .subtitle { color: rgba(255,255,255,0.8); font-size: 0.85em; }
        .header .refresh-btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 20px;
            border-radius: 20px;
            color: #fff;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s;
        }
        .header .refresh-btn:hover { background: rgba(255,255,255,0.35); }

        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        /* Service Status Grid */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .status-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
            transition: transform 0.2s;
        }
        .status-card:hover { transform: translateY(-2px); }
        .status-card .svc-name { font-size: 0.8em; color: #999; text-transform: uppercase; margin-bottom: 6px; }
        .status-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
        }
        .status-badge.connected { background: rgba(0,255,136,0.15); color: #00ff88; }
        .status-badge.error { background: rgba(255,71,87,0.15); color: #ff4757; }
        .status-badge.not-configured { background: rgba(255,204,0,0.15); color: #ffcc00; }

        /* Vault Stats Bar */
        .vault-bar {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .vault-stat {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }
        .vault-stat .label { font-size: 0.75em; color: #888; text-transform: uppercase; margin-bottom: 4px; }
        .vault-stat .value { font-size: 2em; font-weight: 700; }
        .vault-stat.inbox .value { color: #00d4ff; }
        .vault-stat.needs-action .value { color: #ffcc00; }
        .vault-stat.pending .value { color: #ff8c00; }
        .vault-stat.done .value { color: #00ff88; }

        /* Tab Navigation */
        .tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            padding-bottom: 12px;
        }
        .tab-btn {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 8px 18px;
            border-radius: 8px 8px 0 0;
            color: #aaa;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        .tab-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .tab-btn.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: #fff;
            border-color: #667eea;
        }

        /* Tab Content */
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Panel Styles */
        .panel {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }
        .panel h3 {
            font-size: 1em;
            margin-bottom: 14px;
            color: #667eea;
            border-bottom: 1px solid rgba(102,126,234,0.2);
            padding-bottom: 8px;
        }

        /* Form elements */
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 0.8em; color: #999; margin-bottom: 4px; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 6px;
            padding: 10px;
            color: #fff;
            font-size: 0.9em;
        }
        .form-group textarea { min-height: 80px; resize: vertical; }
        .btn {
            padding: 8px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85em;
            font-weight: 600;
            transition: opacity 0.3s;
        }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
        .btn-success { background: #00cc66; color: #fff; }
        .btn-danger { background: #ff4757; color: #fff; }
        .btn-info { background: #0088cc; color: #fff; }
        .btn-sm { padding: 5px 12px; font-size: 0.75em; }

        /* Data table */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85em;
        }
        .data-table th {
            background: rgba(102,126,234,0.15);
            color: #667eea;
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        .data-table td {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .data-table tr:hover { background: rgba(255,255,255,0.03); }
        .data-table-wrapper { max-height: 500px; overflow-y: auto; border-radius: 8px; }

        /* Status badges in tables */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75em;
            font-weight: 600;
        }
        .badge-green { background: rgba(0,255,136,0.15); color: #00ff88; }
        .badge-red { background: rgba(255,71,87,0.15); color: #ff4757; }
        .badge-yellow { background: rgba(255,204,0,0.15); color: #ffcc00; }
        .badge-blue { background: rgba(0,136,255,0.15); color: #00aaff; }
        .badge-orange { background: rgba(255,140,0,0.15); color: #ff8c00; }
        .badge-purple { background: rgba(160,100,255,0.15); color: #a064ff; }

        /* Odoo sub-buttons */
        .odoo-nav {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 16px;
        }
        .odoo-nav .obtn {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 6px 14px;
            border-radius: 6px;
            color: #bbb;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.2s;
        }
        .odoo-nav .obtn:hover { background: rgba(102,126,234,0.2); color: #fff; }
        .odoo-nav .obtn.active { background: #667eea; color: #fff; border-color: #667eea; }

        /* Summary cards grid */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 14px;
        }
        .summary-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 18px;
        }
        .summary-card h4 { color: #667eea; margin-bottom: 10px; font-size: 0.95em; }
        .summary-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 0.85em; }
        .summary-row .lbl { color: #888; }
        .summary-row .val { font-weight: 600; }
        .val.green { color: #00ff88; }
        .val.red { color: #ff4757; }
        .val.orange { color: #ff8c00; }

        /* Email list */
        .email-item {
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            cursor: pointer;
            transition: background 0.2s;
        }
        .email-item:hover { background: rgba(102,126,234,0.1); }
        .email-item .subj { color: #00d4ff; font-weight: 600; font-size: 0.9em; }
        .email-item .meta { color: #666; font-size: 0.8em; margin-top: 4px; }

        /* WhatsApp */
        .wa-msg {
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .wa-msg .wa-info { flex: 1; }
        .wa-msg .wa-name { font-weight: 600; font-size: 0.9em; }
        .wa-msg .wa-preview { color: #888; font-size: 0.8em; margin-top: 4px; }
        .wa-msg .priority-high { color: #ff4757; font-size: 0.7em; font-weight: 600; }

        /* AI Response area */
        .ai-response {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 16px;
            white-space: pre-wrap;
            font-size: 0.9em;
            line-height: 1.6;
            min-height: 100px;
            max-height: 400px;
            overflow-y: auto;
        }

        /* Loading spinner */
        .loading { text-align: center; padding: 30px; color: #667eea; }
        .spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid rgba(102,126,234,0.3);
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .timestamp { text-align: center; color: #444; font-size: 0.8em; margin-top: 20px; }

        /* Pending approval items */
        .pending-item {
            padding: 14px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pending-item .pi-info { flex: 1; }
        .pending-item .pi-name { font-weight: 600; font-size: 0.9em; color: #ffcc00; }
        .pending-item .pi-preview { color: #888; font-size: 0.8em; margin-top: 4px; }
        .pending-item .pi-actions { display: flex; gap: 6px; }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Personal AI Employee</h1>
            <div class="subtitle">Autonomous Digital FTE - Interactive Dashboard</div>
        </div>
        <button class="refresh-btn" onclick="refreshAll()">Refresh All</button>
    </div>

    <div class="container">
        <!-- Service Status -->
        <div class="status-grid" id="status-grid"></div>

        <!-- Vault Stats -->
        <div class="vault-bar" id="vault-bar"></div>

        <!-- Tabs -->
        <div class="tabs" id="tabs">
            <button class="tab-btn active" onclick="switchTab('gmail')">Gmail</button>
            <button class="tab-btn" onclick="switchTab('twitter')">Twitter/X</button>
            <button class="tab-btn" onclick="switchTab('linkedin')">LinkedIn</button>
            <button class="tab-btn" onclick="switchTab('whatsapp')">WhatsApp</button>
            <button class="tab-btn" onclick="switchTab('odoo')">Odoo ERP</button>
            <button class="tab-btn" onclick="switchTab('pending')">Pending Approvals</button>
            <button class="tab-btn" onclick="switchTab('vault')">Vault Browser</button>
            <button class="tab-btn" onclick="switchTab('ai')">AI Assistant</button>
        </div>

        <!-- Gmail Tab -->
        <div class="tab-content active" id="tab-gmail">
            <div class="panel">
                <h3>Compose Email</h3>
                <div class="form-group"><label>To</label><input id="email-to" placeholder="recipient@example.com"></div>
                <div class="form-group"><label>Subject</label><input id="email-subject" placeholder="Email subject"></div>
                <div class="form-group"><label>Body</label><textarea id="email-body" placeholder="Write your email..."></textarea></div>
                <button class="btn btn-primary" onclick="sendEmail()">Send Email</button>
                <span id="email-status" style="margin-left:12px;font-size:0.85em;"></span>
            </div>
            <div class="panel">
                <h3>Recent Emails</h3>
                <div id="email-list"><div class="loading"><span class="spinner"></span>Loading emails...</div></div>
            </div>
        </div>

        <!-- Twitter Tab -->
        <div class="tab-content" id="tab-twitter">
            <div class="panel">
                <h3>Post to Twitter/X</h3>
                <div class="form-group"><label>Topic (optional, for AI generation)</label><input id="twitter-topic" placeholder="e.g. AI productivity tips, tech trends..."></div>
                <div class="form-group"><label>Tweet Text</label><textarea id="tweet-text" placeholder="What is happening? Type manually or click AI Generate..." maxlength="280"></textarea></div>
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <div style="display:flex;gap:8px;">
                        <button class="btn btn-primary" onclick="generatePost('twitter')" id="btn-gen-twitter">AI Generate Tweet</button>
                        <button class="btn btn-info" onclick="postTweet()">Post Tweet</button>
                        <button class="btn btn-success" onclick="saveDraft('twitter')">Save Draft</button>
                    </div>
                    <span id="tweet-chars" style="color:#666;font-size:0.8em;">0/280</span>
                </div>
                <div id="tweet-status" style="margin-top:12px;font-size:0.85em;"></div>
            </div>
        </div>

        <!-- LinkedIn Tab -->
        <div class="tab-content" id="tab-linkedin">
            <div class="panel">
                <h3>Post to LinkedIn</h3>
                <div class="form-group"><label>Topic (optional, for AI generation)</label><input id="linkedin-topic" placeholder="e.g. leadership insights, industry trends..."></div>
                <div class="form-group"><label>Post Text</label><textarea id="linkedin-text" placeholder="Share a professional update or click AI Generate..." rows="4"></textarea></div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                    <button class="btn btn-primary" onclick="generatePost('linkedin')" id="btn-gen-linkedin">AI Generate Post</button>
                    <button class="btn btn-info" onclick="postLinkedIn()">Post to LinkedIn</button>
                    <button class="btn btn-success" onclick="saveDraft('linkedin')">Save Draft</button>
                </div>
                <div id="linkedin-status" style="margin-top:12px;font-size:0.85em;"></div>
            </div>
        </div>

        <!-- WhatsApp Tab -->
        <div class="tab-content" id="tab-whatsapp">
            <div class="panel">
                <h3>WhatsApp Messages (from Vault)</h3>
                <button class="btn btn-sm btn-info" onclick="loadWhatsApp()" style="margin-bottom:12px;">Refresh</button>
                <button class="btn btn-sm btn-success" onclick="sendTestWhatsApp()" style="margin-bottom:12px;">Send Test Message</button>
                <div id="whatsapp-list"><div class="loading"><span class="spinner"></span>Loading messages...</div></div>
            </div>
        </div>

        <!-- Odoo ERP Tab -->
        <div class="tab-content" id="tab-odoo">
            <div class="odoo-nav" id="odoo-nav">
                <button class="obtn active" onclick="loadOdooSection('summary')">Summary</button>
                <button class="obtn" onclick="loadOdooSection('invoices')">Invoices</button>
                <button class="obtn" onclick="loadOdooSection('orders')">Orders</button>
                <button class="obtn" onclick="loadOdooSection('partners')">Partners</button>
                <button class="obtn" onclick="loadOdooSection('employees')">Employees</button>
                <button class="obtn" onclick="loadOdooSection('leads')">CRM Leads</button>
                <button class="obtn" onclick="loadOdooSection('expenses')">Expenses</button>
                <button class="obtn" onclick="loadOdooSection('products')">Products</button>
                <button class="obtn" onclick="loadOdooSection('projects')">Projects</button>
                <button class="obtn" onclick="loadOdooSection('payments')">Payments</button>
                <button class="obtn" onclick="loadOdooSection('attendance')">Attendance</button>
                <button class="obtn" onclick="loadOdooSection('leaves')">Leaves</button>
                <button class="obtn" onclick="loadOdooSection('purchases')">Purchases</button>
            </div>
            <div class="panel" id="odoo-content">
                <div class="loading"><span class="spinner"></span>Loading Odoo data...</div>
            </div>
        </div>

        <!-- Pending Approvals Tab -->
        <div class="tab-content" id="tab-pending">
            <div class="panel">
                <h3>Pending Approvals</h3>
                <div id="pending-list"><div class="loading"><span class="spinner"></span>Loading...</div></div>
            </div>
        </div>

        <!-- Vault Browser Tab -->
        <div class="tab-content" id="tab-vault">
            <div class="panel">
                <h3>Vault Browser</h3>
                <div class="odoo-nav" id="vault-nav">
                    <button class="obtn active" onclick="loadVaultFolder('Inbox')">Inbox</button>
                    <button class="obtn" onclick="loadVaultFolder('Needs_Action')">Needs Action</button>
                    <button class="obtn" onclick="loadVaultFolder('Pending_Approval')">Pending Approval</button>
                    <button class="obtn" onclick="loadVaultFolder('Approved')">Approved</button>
                    <button class="obtn" onclick="loadVaultFolder('Rejected')">Rejected</button>
                    <button class="obtn" onclick="loadVaultFolder('Done')">Done</button>
                </div>
                <div id="vault-file-list"><div style="padding:16px;color:#666;">Select a folder above to browse files.</div></div>
            </div>
            <div class="panel" id="vault-preview-panel" style="display:none;">
                <h3 id="vault-preview-title">File Preview</h3>
                <div style="margin-bottom:12px;" id="vault-preview-meta"></div>
                <div class="ai-response" id="vault-preview-content" style="white-space:pre-wrap;"></div>
                <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;" id="vault-preview-actions"></div>
            </div>
        </div>

        <!-- AI Assistant Tab -->
        <div class="tab-content" id="tab-ai">
            <div class="panel">
                <h3>AI Assistant</h3>
                <div class="form-group"><label>Context (System Prompt)</label><input id="ai-context" value="You are a helpful AI assistant for a business professional managing email, social media, and ERP systems."></div>
                <div class="form-group"><label>Your Question / Prompt</label><textarea id="ai-prompt" placeholder="Ask me anything..." rows="3"></textarea></div>
                <button class="btn btn-primary" onclick="askAI()">Ask AI</button>
                <span id="ai-status" style="margin-left:12px;font-size:0.85em;"></span>
            </div>
            <div class="panel">
                <h3>AI Response</h3>
                <div class="ai-response" id="ai-response">Response will appear here...</div>
            </div>
        </div>

        <p class="timestamp" id="timestamp"></p>
    </div>

<script>
// ---- Tab switching ----
function switchTab(name) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    const tab = document.getElementById('tab-' + name);
    if (tab) tab.classList.add('active');
    // Highlight button
    const tabMap = {gmail:'Gmail',twitter:'Twitter/X',linkedin:'LinkedIn',whatsapp:'WhatsApp',odoo:'Odoo ERP',pending:'Pending Approvals',vault:'Vault Browser',ai:'AI Assistant'};
    document.querySelectorAll('.tab-btn').forEach(el => {
        if (el.textContent === tabMap[name]) el.classList.add('active');
    });
    // Load data for tab
    if (name === 'whatsapp') loadWhatsApp();
    if (name === 'odoo') loadOdooSection('summary');
    if (name === 'pending') loadPending();
    if (name === 'vault') loadVaultFolder('Inbox');
}

// ---- Status + Vault ----
async function loadStatus() {
    try {
        const r = await fetch('/api/status');
        const data = await r.json();
        // Services
        const grid = document.getElementById('status-grid');
        grid.innerHTML = '';
        for (const [name, state] of Object.entries(data.services)) {
            const cls = state === 'connected' ? 'connected' : (state === 'error' ? 'error' : 'not-configured');
            grid.innerHTML += '<div class="status-card"><div class="svc-name">' + name.replace('_',' ') + '</div><span class="status-badge ' + cls + '">' + state + '</span></div>';
        }
        // Vault
        const vbar = document.getElementById('vault-bar');
        const c = data.counts;
        vbar.innerHTML = '<div class="vault-stat inbox"><div class="label">Inbox</div><div class="value">' + (c.inbox||0) + '</div></div>'
            + '<div class="vault-stat needs-action"><div class="label">Needs Action</div><div class="value">' + (c.needs_action||0) + '</div></div>'
            + '<div class="vault-stat pending"><div class="label">Pending</div><div class="value">' + (c.pending_approval||0) + '</div></div>'
            + '<div class="vault-stat done"><div class="label">Done</div><div class="value">' + (c.done||0) + '</div></div>';
        document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleString();
    } catch(e) { console.error('Status error:', e); }
}

// ---- Emails ----
async function loadEmails() {
    try {
        const r = await fetch('/api/emails');
        const data = await r.json();
        const el = document.getElementById('email-list');
        if (!data.emails || data.emails.length === 0) {
            el.innerHTML = '<div style="padding:16px;color:#666;">No emails found' + (data.imap_error ? ' (IMAP: ' + data.imap_error + ')' : '') + '</div>';
            return;
        }
        el.innerHTML = data.emails.map(function(e) {
            return '<div class="email-item"><div class="subj">' + esc(e.subject || e.filename || '') + '</div><div class="meta">' + esc(e.from || e.source || '') + ' - ' + esc(e.date || e.modified || '') + '</div><div style="color:#888;font-size:0.8em;margin-top:4px;">' + esc((e.preview||'').substring(0,120)) + '</div></div>';
        }).join('');
    } catch(e) { document.getElementById('email-list').innerHTML = '<div style="padding:16px;color:#ff4757;">Error loading emails</div>'; }
}

async function sendEmail() {
    var to = document.getElementById('email-to').value;
    var subject = document.getElementById('email-subject').value;
    var body = document.getElementById('email-body').value;
    var st = document.getElementById('email-status');
    if (!to || !subject) { st.innerHTML = '<span style="color:#ff4757;">Please fill in To and Subject</span>'; return; }
    st.innerHTML = '<span class="spinner"></span>Sending...';
    try {
        var r = await fetch('/api/send-email', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({to:to,subject:subject,body:body})});
        var data = await r.json();
        st.innerHTML = data.success ? '<span style="color:#00ff88;">Sent!</span>' : '<span style="color:#ff4757;">' + esc(data.error) + '</span>';
        if (data.success) { document.getElementById('email-to').value=''; document.getElementById('email-subject').value=''; document.getElementById('email-body').value=''; }
    } catch(e) { st.innerHTML = '<span style="color:#ff4757;">Error: ' + e.message + '</span>'; }
}

// ---- Twitter ----
document.addEventListener('DOMContentLoaded', function() {
    var tt = document.getElementById('tweet-text');
    if (tt) tt.addEventListener('input', function() {
        document.getElementById('tweet-chars').textContent = this.value.length + '/280';
    });
});

async function postTweet() {
    var text = document.getElementById('tweet-text').value;
    var st = document.getElementById('tweet-status');
    if (!text) { st.innerHTML = '<span style="color:#ff4757;">Please enter tweet text</span>'; return; }
    st.innerHTML = '<span class="spinner"></span>Posting...';
    try {
        var r = await fetch('/api/post-twitter', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:text})});
        var data = await r.json();
        st.innerHTML = data.success ? '<span style="color:#00ff88;">Tweet posted!</span>' : '<span style="color:#ff4757;">' + esc(data.error) + '</span>';
        if (data.success) document.getElementById('tweet-text').value = '';
    } catch(e) { st.innerHTML = '<span style="color:#ff4757;">Error: ' + e.message + '</span>'; }
}

// ---- LinkedIn ----
async function postLinkedIn() {
    var text = document.getElementById('linkedin-text').value;
    var st = document.getElementById('linkedin-status');
    if (!text) { st.innerHTML = '<span style="color:#ff4757;">Please enter post text</span>'; return; }
    st.innerHTML = '<span class="spinner"></span>Posting...';
    try {
        var r = await fetch('/api/post-linkedin', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:text})});
        var data = await r.json();
        st.innerHTML = data.success ? '<span style="color:#00ff88;">Posted to LinkedIn!</span>' : '<span style="color:#ff4757;">' + esc(data.error) + '</span>';
        if (data.success) document.getElementById('linkedin-text').value = '';
    } catch(e) { st.innerHTML = '<span style="color:#ff4757;">Error: ' + e.message + '</span>'; }
}

// ---- WhatsApp ----
async function loadWhatsApp() {
    var el = document.getElementById('whatsapp-list');
    el.innerHTML = '<div class="loading"><span class="spinner"></span>Loading...</div>';
    try {
        var r = await fetch('/api/whatsapp');
        var data = await r.json();
        if (!data.messages || data.messages.length === 0) {
            el.innerHTML = '<div style="padding:16px;color:#666;">No WhatsApp messages in vault</div>';
            return;
        }
        el.innerHTML = data.messages.map(function(m) {
            return '<div class="wa-msg"><div class="wa-info"><div class="wa-name">' + esc(m.filename) + (m.priority==='high'?' <span class="priority-high">[HIGH PRIORITY]</span>':'') + '</div><div class="wa-preview">' + esc((m.content||'').substring(0,150)) + '</div></div><button class="btn btn-sm btn-success" onclick="processWhatsApp(\\'' + esc(m.filename).replace(/'/g,"\\\\'") + '\\')">Process</button></div>';
        }).join('');
    } catch(e) { el.innerHTML = '<div style="padding:16px;color:#ff4757;">Error loading WhatsApp</div>'; }
}

async function processWhatsApp(filename) {
    try {
        var r = await fetch('/api/whatsapp-process', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename:filename})});
        var data = await r.json();
        alert(data.success ? 'Processed: ' + filename : 'Error: ' + data.error);
        loadWhatsApp();
    } catch(e) { alert('Error: ' + e.message); }
}

async function sendTestWhatsApp() {
    try {
        var r = await fetch('/api/whatsapp-test', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({sender:'Dashboard Test', text:'This is a test WhatsApp message from the dashboard. Please help ASAP!'})});
        var data = await r.json();
        alert(data.success ? 'Test message created: ' + data.filename : 'Error: ' + data.error);
        loadWhatsApp();
    } catch(e) { alert('Error: ' + e.message); }
}

// ---- Odoo ERP ----
var currentOdooSection = 'summary';

function loadOdooSection(section) {
    currentOdooSection = section;
    // Update nav buttons
    document.querySelectorAll('.odoo-nav .obtn').forEach(function(b) { b.classList.remove('active'); });
    var sectionLabels = {summary:'Summary',invoices:'Invoices',orders:'Orders',partners:'Partners',employees:'Employees',leads:'CRM Leads',expenses:'Expenses',products:'Products',projects:'Projects',payments:'Payments',attendance:'Attendance',leaves:'Leaves',purchases:'Purchases'};
    document.querySelectorAll('.odoo-nav .obtn').forEach(function(b) {
        if (b.textContent === sectionLabels[section]) b.classList.add('active');
    });

    var el = document.getElementById('odoo-content');
    el.innerHTML = '<div class="loading"><span class="spinner"></span>Loading ' + section + '...</div>';

    var url = (section === 'summary') ? '/api/odoo/dashboard' : '/api/odoo/' + section;
    fetch(url).then(function(r) { return r.json(); }).then(function(data) {
        if (data.error) {
            el.innerHTML = '<div style="color:#ff4757;padding:16px;">Error: ' + esc(data.error) + '</div>';
            return;
        }
        if (section === 'summary' || section === 'dashboard') {
            renderOdooSummary(data);
        } else {
            renderOdooTable(section, data);
        }
    }).catch(function(e) {
        el.innerHTML = '<div style="color:#ff4757;padding:16px;">Failed to load: ' + e.message + '</div>';
    });
}

function renderOdooSummary(data) {
    var el = document.getElementById('odoo-content');
    var html = '<h3>Odoo ERP Summary - ' + esc(data.company || 'Company') + '</h3><div class="summary-grid">';

    if (data.revenue) {
        html += '<div class="summary-card"><h4>Revenue</h4>'
            + sr('Total Invoiced', '$' + fmt(data.revenue.total_invoiced))
            + sr('Total Paid', '$' + fmt(data.revenue.total_paid), 'green')
            + sr('Amount Due', '$' + fmt(data.revenue.total_due), 'orange')
            + sr('Overdue', data.revenue.overdue, 'red')
            + '</div>';
    }
    if (data.sales) {
        html += '<div class="summary-card"><h4>Sales</h4>'
            + sr('Total Orders', data.sales.total_orders)
            + sr('Confirmed', data.sales.confirmed, 'green')
            + sr('Draft', data.sales.draft, 'orange')
            + sr('Total Value', '$' + fmt(data.sales.total_value))
            + '</div>';
    }
    if (data.crm) {
        html += '<div class="summary-card"><h4>CRM Pipeline</h4>'
            + sr('Total Leads', data.crm.total_leads)
            + sr('Won', data.crm.won, 'green')
            + sr('Pipeline Value', '$' + fmt(data.crm.pipeline_value))
            + sr('Avg Probability', data.crm.avg_probability + '%')
            + '</div>';
    }
    if (data.hr) {
        html += '<div class="summary-card"><h4>HR / Team</h4>'
            + sr('Employees', data.hr.total_employees)
            + sr('Active', data.hr.active, 'green')
            + sr('Checked In', data.hr.checked_in_today)
            + sr('Pending Leaves', data.hr.pending_leaves, 'orange')
            + '</div>';
    }
    if (data.payments) {
        html += '<div class="summary-card"><h4>Payments</h4>'
            + sr('Received', '$' + fmt(data.payments.received), 'green')
            + sr('Sent', '$' + fmt(data.payments.sent), 'red')
            + sr('Pending', '$' + fmt(data.payments.pending), 'orange')
            + '</div>';
    }
    if (data.projects) {
        html += '<div class="summary-card"><h4>Projects</h4>'
            + sr('Total', data.projects.total)
            + sr('In Progress', data.projects.in_progress, 'green')
            + sr('Avg Progress', data.projects.avg_progress + '%')
            + '</div>';
    }
    if (data.expenses) {
        html += '<div class="summary-card"><h4>Expenses</h4>'
            + sr('Vendor Bills', '$' + fmt(data.expenses.total_bills))
            + sr('Unpaid Bills', '$' + fmt(data.expenses.unpaid_bills), 'red')
            + sr('Employee Expenses', '$' + fmt(data.expenses.employee_expenses))
            + sr('Pending Approval', data.expenses.pending_approval, 'orange')
            + '</div>';
    }
    if (data.partners) {
        html += '<div class="summary-card"><h4>Partners</h4>'
            + sr('Total', data.partners.total)
            + sr('Customers', data.partners.customers, 'green')
            + sr('Vendors', data.partners.vendors)
            + '</div>';
    }

    html += '</div>';
    el.innerHTML = html;
}

function renderOdooTable(section, data) {
    var el = document.getElementById('odoo-content');
    var rows = data.data || data;
    if (!Array.isArray(rows) || rows.length === 0) {
        el.innerHTML = '<div style="padding:16px;color:#666;">No data available for ' + section + '</div>';
        return;
    }

    var colDefs = getOdooColumns(section, rows);
    var html = '<h3>' + section.charAt(0).toUpperCase() + section.slice(1) + ' (' + rows.length + ' records)</h3>';
    html += '<div class="data-table-wrapper"><table class="data-table"><thead><tr>';
    colDefs.forEach(function(c) { html += '<th>' + c.label + '</th>'; });
    html += '</tr></thead><tbody>';

    rows.forEach(function(row) {
        html += '<tr>';
        colDefs.forEach(function(c) {
            var val = row[c.key] !== undefined && row[c.key] !== null ? row[c.key] : '-';
            if (c.format === 'money') val = '$' + fmt(val);
            if (c.format === 'badge') val = statusBadge(val);
            if (c.format === 'priority') val = priorityBadge(val);
            if (c.format === 'percent') val = val + '%';
            if (c.format === 'hours' && val !== '-') val = Number(val).toFixed(1) + 'h';
            html += '<td>' + val + '</td>';
        });
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    el.innerHTML = html;
}

function getOdooColumns(section, rows) {
    var defs = {
        invoices: [
            {key:'name',label:'Invoice #'},{key:'partner',label:'Partner'},{key:'amount_total',label:'Total',format:'money'},
            {key:'amount_due',label:'Due',format:'money'},{key:'state',label:'State',format:'badge'},
            {key:'payment_state',label:'Payment',format:'badge'},{key:'invoice_date',label:'Date'},{key:'currency',label:'Curr'}
        ],
        orders: [
            {key:'name',label:'Order'},{key:'partner',label:'Partner'},{key:'amount_total',label:'Total',format:'money'},
            {key:'state',label:'State',format:'badge'},{key:'date_order',label:'Date'},{key:'invoice_status',label:'Invoice Status',format:'badge'}
        ],
        partners: [
            {key:'name',label:'Name'},{key:'email',label:'Email'},{key:'phone',label:'Phone'},
            {key:'city',label:'City'},{key:'country',label:'Country'},{key:'type',label:'Type',format:'badge'},
            {key:'total_invoiced',label:'Invoiced',format:'money'}
        ],
        employees: [
            {key:'name',label:'Name'},{key:'job_title',label:'Job Title'},{key:'department',label:'Department'},
            {key:'email',label:'Email'},{key:'work_location',label:'Location'},{key:'status',label:'Status',format:'badge'}
        ],
        leads: [
            {key:'name',label:'Opportunity'},{key:'partner',label:'Partner'},{key:'stage',label:'Stage',format:'badge'},
            {key:'expected_revenue',label:'Revenue',format:'money'},{key:'probability',label:'Prob',format:'percent'},
            {key:'salesperson',label:'Salesperson'},{key:'priority',label:'Priority',format:'priority'}
        ],
        expenses: [
            {key:'name',label:'Expense'},{key:'employee',label:'Employee'},{key:'amount',label:'Amount',format:'money'},
            {key:'state',label:'State',format:'badge'},{key:'date',label:'Date'},{key:'category',label:'Category'}
        ],
        products: [
            {key:'name',label:'Product'},{key:'list_price',label:'Price',format:'money'},{key:'standard_price',label:'Cost',format:'money'},
            {key:'qty_available',label:'Stock'},{key:'category',label:'Category'},{key:'type',label:'Type',format:'badge'}
        ],
        projects: [
            {key:'name',label:'Project'},{key:'manager',label:'Manager'},{key:'status',label:'Status',format:'badge'},
            {key:'task_count',label:'Tasks'},{key:'completed_tasks',label:'Done'},{key:'progress',label:'Progress',format:'percent'},
            {key:'deadline',label:'Deadline'}
        ],
        payments: [
            {key:'name',label:'Payment #'},{key:'partner',label:'Partner'},{key:'amount',label:'Amount',format:'money'},
            {key:'state',label:'State',format:'badge'},{key:'date',label:'Date'},{key:'payment_type',label:'Type',format:'badge'},
            {key:'method',label:'Method'}
        ],
        attendance: [
            {key:'employee',label:'Employee'},{key:'check_in',label:'Check In'},{key:'check_out',label:'Check Out'},
            {key:'worked_hours',label:'Hours',format:'hours'}
        ],
        leaves: [
            {key:'employee',label:'Employee'},{key:'type',label:'Leave Type'},{key:'date_from',label:'From'},
            {key:'date_to',label:'To'},{key:'days',label:'Days'},{key:'state',label:'State',format:'badge'},
            {key:'reason',label:'Reason'}
        ],
        purchases: [
            {key:'name',label:'PO #'},{key:'partner',label:'Vendor'},{key:'amount_total',label:'Total',format:'money'},
            {key:'state',label:'State',format:'badge'},{key:'date_order',label:'Date'},{key:'date_planned',label:'Planned'}
        ]
    };
    if (defs[section]) return defs[section];
    // Fallback: auto-detect from first row
    if (rows && rows.length > 0) {
        return Object.keys(rows[0]).map(function(k) { return {key:k, label:k}; });
    }
    return [];
}

function statusBadge(val) {
    var v = String(val).toLowerCase();
    var map = {
        'posted':'green','paid':'green','done':'green','sale':'green','active':'green',
        'connected':'green','purchase':'green','validate':'green','approved':'green','won':'green',
        'in_progress':'blue','inbound':'green','outbound':'red','confirm':'yellow','submitted':'yellow',
        'partial':'orange','not_paid':'red','overdue':'red','error':'red','draft':'yellow',
        'to invoice':'orange','invoiced':'green','new':'blue','qualified':'blue','proposition':'purple',
        'customer':'green','vendor':'blue','service':'blue','product':'orange',
        'planned':'yellow','no':'yellow'
    };
    var cls = map[v] || 'blue';
    return '<span class="badge badge-' + cls + '">' + esc(val) + '</span>';
}

function priorityBadge(val) {
    var map = {'0':'Low','1':'Normal','2':'High','3':'Urgent'};
    var cls_map = {'0':'blue','1':'green','2':'orange','3':'red'};
    var label = map[String(val)] || val;
    var cls = cls_map[String(val)] || 'blue';
    return '<span class="badge badge-' + cls + '">' + label + '</span>';
}

// ---- Pending Approvals ----
async function loadPending() {
    var el = document.getElementById('pending-list');
    el.innerHTML = '<div class="loading"><span class="spinner"></span>Loading...</div>';
    try {
        var r = await fetch('/api/pending');
        var data = await r.json();
        if (!data.pending || data.pending.length === 0) {
            el.innerHTML = '<div style="padding:16px;color:#666;">No pending approvals</div>';
            return;
        }
        el.innerHTML = data.pending.map(function(p) {
            return '<div class="pending-item"><div class="pi-info"><div class="pi-name">' + esc(p.filename) + '</div><div class="pi-preview">' + esc((p.preview||'').substring(0,150)) + '</div></div><div class="pi-actions"><button class="btn btn-sm btn-success" onclick="approveItem(\\'' + esc(p.filename).replace(/'/g,"\\\\'") + '\\')">Approve</button><button class="btn btn-sm btn-danger" onclick="rejectItem(\\'' + esc(p.filename).replace(/'/g,"\\\\'") + '\\')">Reject</button></div></div>';
        }).join('');
    } catch(e) { el.innerHTML = '<div style="padding:16px;color:#ff4757;">Error loading pending items</div>'; }
}

async function approveItem(filename) {
    try {
        var r = await fetch('/api/approve', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename:filename})});
        var data = await r.json();
        alert(data.success ? 'Approved: ' + filename : 'Error: ' + data.error);
        loadPending(); loadStatus();
    } catch(e) { alert('Error: ' + e.message); }
}

async function rejectItem(filename) {
    try {
        var r = await fetch('/api/reject', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename:filename})});
        var data = await r.json();
        alert(data.success ? 'Rejected: ' + filename : 'Error: ' + data.error);
        loadPending(); loadStatus();
    } catch(e) { alert('Error: ' + e.message); }
}

// ---- AI Assistant ----
async function askAI() {
    var prompt = document.getElementById('ai-prompt').value;
    var context = document.getElementById('ai-context').value;
    var st = document.getElementById('ai-status');
    var resp = document.getElementById('ai-response');
    if (!prompt) { st.innerHTML = '<span style="color:#ff4757;">Please enter a prompt</span>'; return; }
    st.innerHTML = '<span class="spinner"></span>Thinking...';
    resp.textContent = 'Generating response...';
    try {
        var r = await fetch('/api/ai-suggest', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({prompt:prompt, context:context})});
        var data = await r.json();
        if (data.success) {
            resp.textContent = data.response;
            st.innerHTML = '<span style="color:#00ff88;">Done (' + esc(data.model||'') + ')</span>';
        } else {
            resp.textContent = 'Error: ' + data.error;
            st.innerHTML = '<span style="color:#ff4757;">Failed</span>';
        }
    } catch(e) { resp.textContent = 'Error: ' + e.message; st.innerHTML = '<span style="color:#ff4757;">Failed</span>'; }
}

// ---- AI Generate Post ----
async function generatePost(platform) {
    var textareaId = platform === 'twitter' ? 'tweet-text' : 'linkedin-text';
    var statusId = platform === 'twitter' ? 'tweet-status' : 'linkedin-status';
    var topicId = platform === 'twitter' ? 'twitter-topic' : 'linkedin-topic';
    var btnId = 'btn-gen-' + platform;
    var st = document.getElementById(statusId);
    var btn = document.getElementById(btnId);
    var topic = document.getElementById(topicId) ? document.getElementById(topicId).value : '';

    btn.disabled = true;
    btn.textContent = 'Generating...';
    st.innerHTML = '<span class="spinner"></span>AI is generating your ' + platform + ' post...';

    try {
        var r = await fetch('/api/generate-post', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({platform: platform, topic: topic})});
        var data = await r.json();
        if (data.success) {
            document.getElementById(textareaId).value = data.content;
            st.innerHTML = '<span style="color:#00ff88;">AI post generated! Review and edit before posting.</span>';
            if (platform === 'twitter') {
                document.getElementById('tweet-chars').textContent = data.content.length + '/280';
            }
        } else {
            st.innerHTML = '<span style="color:#ff4757;">Error: ' + esc(data.error) + '</span>';
        }
    } catch(e) {
        st.innerHTML = '<span style="color:#ff4757;">Error: ' + e.message + '</span>';
    }
    btn.disabled = false;
    btn.textContent = platform === 'twitter' ? 'AI Generate Tweet' : 'AI Generate Post';
}

// ---- Save Draft ----
async function saveDraft(platform) {
    var textareaId = platform === 'twitter' ? 'tweet-text' : 'linkedin-text';
    var statusId = platform === 'twitter' ? 'tweet-status' : 'linkedin-status';
    var content = document.getElementById(textareaId).value;
    var st = document.getElementById(statusId);

    if (!content) {
        st.innerHTML = '<span style="color:#ff4757;">Nothing to save — write or generate content first.</span>';
        return;
    }
    st.innerHTML = '<span class="spinner"></span>Saving draft...';
    try {
        var r = await fetch('/api/save-draft', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({platform: platform, content: content})});
        var data = await r.json();
        if (data.success) {
            st.innerHTML = '<span style="color:#00ff88;">Draft saved: ' + esc(data.filename) + ' — check Pending Approvals tab.</span>';
            loadStatus();
        } else {
            st.innerHTML = '<span style="color:#ff4757;">Error: ' + esc(data.error) + '</span>';
        }
    } catch(e) {
        st.innerHTML = '<span style="color:#ff4757;">Error: ' + e.message + '</span>';
    }
}

// ---- Vault Browser ----
var currentVaultFolder = 'Inbox';

async function loadVaultFolder(folder) {
    currentVaultFolder = folder;
    // Update nav buttons
    document.querySelectorAll('#vault-nav .obtn').forEach(function(b) { b.classList.remove('active'); });
    var folderLabels = {'Inbox':'Inbox','Needs_Action':'Needs Action','Pending_Approval':'Pending Approval','Approved':'Approved','Rejected':'Rejected','Done':'Done'};
    document.querySelectorAll('#vault-nav .obtn').forEach(function(b) {
        if (b.textContent === folderLabels[folder]) b.classList.add('active');
    });

    var el = document.getElementById('vault-file-list');
    el.innerHTML = '<div class="loading"><span class="spinner"></span>Loading ' + folder + '...</div>';
    document.getElementById('vault-preview-panel').style.display = 'none';

    try {
        var r = await fetch('/api/vault/browse?folder=' + encodeURIComponent(folder));
        var data = await r.json();
        if (!data.files || data.files.length === 0) {
            el.innerHTML = '<div style="padding:16px;color:#666;">No files in ' + folder + '</div>';
            return;
        }
        var html = '<div class="data-table-wrapper"><table class="data-table"><thead><tr><th>File</th><th>Type</th><th>Priority</th><th>Modified</th><th>Actions</th></tr></thead><tbody>';
        data.files.forEach(function(f) {
            html += '<tr>'
                + '<td><a href="#" style="color:#00d4ff;text-decoration:none;" onclick="viewVaultFile(\\'' + esc(f.path).replace(/'/g,"\\\\'") + '\\');return false;">' + esc(f.filename) + '</a></td>'
                + '<td>' + statusBadge(f.type || 'file') + '</td>'
                + '<td>' + (f.priority === 'high' ? '<span class="badge badge-red">high</span>' : '<span class="badge badge-blue">' + esc(f.priority) + '</span>') + '</td>'
                + '<td style="font-size:0.8em;color:#888;">' + esc((f.modified||'').substring(0,16)) + '</td>'
                + '<td><button class="btn btn-sm btn-info" onclick="viewVaultFile(\\'' + esc(f.path).replace(/'/g,"\\\\'") + '\\')">View</button></td>'
                + '</tr>';
        });
        html += '</tbody></table></div>';
        el.innerHTML = html;
    } catch(e) {
        el.innerHTML = '<div style="padding:16px;color:#ff4757;">Error: ' + e.message + '</div>';
    }
}

async function viewVaultFile(path) {
    var panel = document.getElementById('vault-preview-panel');
    var titleEl = document.getElementById('vault-preview-title');
    var metaEl = document.getElementById('vault-preview-meta');
    var contentEl = document.getElementById('vault-preview-content');
    var actionsEl = document.getElementById('vault-preview-actions');

    panel.style.display = 'block';
    contentEl.textContent = 'Loading...';
    titleEl.textContent = 'Loading...';
    metaEl.innerHTML = '';
    actionsEl.innerHTML = '';

    try {
        var r = await fetch('/api/vault/file?path=' + encodeURIComponent(path));
        var data = await r.json();
        if (data.error) {
            contentEl.textContent = 'Error: ' + data.error;
            return;
        }
        titleEl.textContent = data.filename;
        var meta = data.meta || {};
        var metaHtml = '';
        if (meta.type) metaHtml += '<span class="badge badge-blue" style="margin-right:6px;">' + esc(meta.type) + '</span>';
        if (meta.priority) metaHtml += '<span class="badge ' + (meta.priority==='high'?'badge-red':'badge-green') + '" style="margin-right:6px;">' + esc(meta.priority) + '</span>';
        if (meta.status) metaHtml += '<span class="badge badge-yellow" style="margin-right:6px;">' + esc(meta.status) + '</span>';
        if (data.modified) metaHtml += '<span style="color:#666;font-size:0.8em;">Modified: ' + esc(data.modified) + '</span>';
        metaEl.innerHTML = metaHtml;
        contentEl.textContent = data.content;

        // Determine move actions based on current folder
        var filename = data.filename;
        var folders = ['Inbox','Needs_Action','Pending_Approval','Approved','Rejected','Done'];
        var btnHtml = '';
        folders.forEach(function(f) {
            if (f !== currentVaultFolder) {
                var cls = (f === 'Approved') ? 'btn-success' : (f === 'Rejected' ? 'btn-danger' : 'btn-info');
                btnHtml += '<button class="btn btn-sm ' + cls + '" onclick="moveVaultFile(\\'' + esc(filename).replace(/'/g,"\\\\'") + '\\', \\'' + currentVaultFolder + '\\', \\'' + f + '\\')">Move to ' + f.replace('_',' ') + '</button>';
            }
        });
        actionsEl.innerHTML = btnHtml;
    } catch(e) {
        contentEl.textContent = 'Error: ' + e.message;
    }
}

async function moveVaultFile(filename, fromFolder, toFolder) {
    try {
        var r = await fetch('/api/vault/move', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({filename: filename, from_folder: fromFolder, to_folder: toFolder})});
        var data = await r.json();
        if (data.success) {
            alert('Moved ' + filename + ' to ' + toFolder);
            loadVaultFolder(currentVaultFolder);
            document.getElementById('vault-preview-panel').style.display = 'none';
            loadStatus();
        } else {
            alert('Error: ' + data.error);
        }
    } catch(e) { alert('Error: ' + e.message); }
}

// ---- Helpers ----
function esc(s) { var d=document.createElement('div'); d.textContent=String(s||''); return d.innerHTML; }
function fmt(n) { return Number(n||0).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}); }
function sr(label, val, cls) { return '<div class="summary-row"><span class="lbl">' + label + '</span><span class="val' + (cls?' '+cls:'') + '">' + val + '</span></div>'; }

// ---- Init ----
function refreshAll() {
    loadStatus();
    loadEmails();
}

// Load on page ready
loadStatus();
loadEmails();

// Auto-refresh status every 30 seconds
setInterval(loadStatus, 30000);
</script>
</body>
</html>'''


# ============================================================
# SERVER ENTRY POINT
# ============================================================
def run_dashboard(port=9001):
    """Run the interactive dashboard server."""
    print("=" * 60)
    print("  PERSONAL AI EMPLOYEE - INTERACTIVE DASHBOARD")
    print("=" * 60)
    print(f"\n  Open in browser: http://localhost:{port}")
    print(f"  Or: http://127.0.0.1:{port}")
    print(f"\n  Services configured:")
    print(f"    Gmail:     {'Yes' if email_manager.is_configured() else 'No'}")
    print(f"    Twitter:   {'Yes' if social_manager.is_configured() else 'No'}")
    print(f"    LinkedIn:  {'Yes' if os.getenv('LINKEDIN_ACCESS_TOKEN') else 'No'}")
    print(f"    Odoo ERP:  {'Yes' if odoo_manager.is_configured() else 'No'}")
    print(f"    AI Helper: {'Yes' if ai_helper.is_configured() else 'No'}")
    print(f"    Vault:     {VAULT_PATH}")
    print(f"\n  Press Ctrl+C to stop\n")
    print("=" * 60)

    server = ThreadedHTTPServer(("0.0.0.0", port), DashboardHandler)
    server.protocol_version = "HTTP/1.1"
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down interactive dashboard...")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    run_dashboard(port)
