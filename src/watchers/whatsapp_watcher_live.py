#!/usr/bin/env python3
"""
Live WhatsApp Watcher - Monitors WhatsApp Web for keyword-triggered messages.
Uses Playwright to automate WhatsApp Web browser session.
"""

import re
import time
import signal
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Config
VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", "./whatsapp_session")
POLL_INTERVAL = 30  # seconds between scans
NEEDS_ACTION = VAULT_DIR / "Needs_Action" / "WhatsApp"
LOGS_DIR = VAULT_DIR / "Logs"

# Keywords from Company Handbook
HIGH_PRIORITY_KEYWORDS = ["payment", "invoice", "urgent", "critical", "overdue"]
NORMAL_PRIORITY_KEYWORDS = ["meeting", "schedule", "update", "project", "deadline"]

SEEN_FILE = VAULT_DIR / ".whatsapp_seen_ids.json"
seen_messages = set()
running = True


def signal_handler(sig, frame):
    global running
    print("\n[WhatsApp Watcher] Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def load_seen():
    global seen_messages
    if SEEN_FILE.exists():
        try:
            seen_messages = set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            seen_messages = set()


def save_seen():
    trimmed = list(seen_messages)[-500:]
    SEEN_FILE.write_text(json.dumps(trimmed))


def get_priority(text):
    text_lower = text.lower()
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in text_lower:
            return "HIGH"
    for kw in NORMAL_PRIORITY_KEYWORDS:
        if kw in text_lower:
            return "normal"
    return "low"


def has_keyword(text):
    text_lower = text.lower()
    all_keywords = HIGH_PRIORITY_KEYWORDS + NORMAL_PRIORITY_KEYWORDS
    return any(kw in text_lower for kw in all_keywords)


def create_vault_file(sender, message, priority, matched_keywords):
    safe_sender = re.sub(r"[^a-zA-Z0-9 ]", "", sender)[:20].strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"WA_{timestamp}_{safe_sender}.md"

    content = f"""---
type: whatsapp_action
source: whatsapp
priority: {priority}
status: needs_action
keywords_matched: {matched_keywords}
created: {datetime.now().isoformat()}
---

# WhatsApp Message

| Field | Value |
|-------|-------|
| **From** | {sender} |
| **Priority** | {priority} |
| **Keywords** | {', '.join(matched_keywords)} |
| **Time** | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |

## Message
{message}

## Action Required
- [ ] Review message
- [ ] Reply if needed
- [ ] Move to [[Done]] when complete

> Detected by WhatsApp Watcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    filepath = NEEDS_ACTION / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def log_activity(action, details=""):
    log_file = LOGS_DIR / f"whatsapp_watcher_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")


def update_dashboard_wa_count(count):
    dashboard = VAULT_DIR / "Dashboard.md"
    if dashboard.exists():
        content = dashboard.read_text(encoding="utf-8")
        icon = "🟡" if count > 0 else "✅"
        new_line = f"- {icon} {count} keyword-triggered messages in [[Needs_Action/WhatsApp]]"
        content = re.sub(
            r"- [🔴✅🟡] \d+ keyword-triggered messages in \[\[Needs_Action/WhatsApp\]\]",
            new_line,
            content
        )
        dashboard.write_text(content, encoding="utf-8")


def run_with_playwright():
    """Run WhatsApp Web monitoring with Playwright."""
    from playwright.sync_api import sync_playwright

    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    load_seen()

    print("=" * 60)
    print("  WhatsApp Watcher - LIVE MODE")
    print(f"  Poll Interval: {POLL_INTERVAL}s")
    print(f"  Session: {SESSION_PATH}")
    print(f"  Keywords: {HIGH_PRIORITY_KEYWORDS + NORMAL_PRIORITY_KEYWORDS}")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch with persistent context (keeps WhatsApp session)
        session_dir = Path(SESSION_PATH)
        session_dir.mkdir(parents=True, exist_ok=True)

        browser_context = p.chromium.launch_persistent_context(
            user_data_dir=str(session_dir),
            headless=False,  # Must be visible for QR scan
            args=["--no-sandbox"],
            viewport={"width": 1280, "height": 800}
        )

        page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
        page.goto("https://web.whatsapp.com")

        print("\n[WhatsApp] Waiting for login...")
        print("[WhatsApp] Scan the QR code if prompted...")

        # Wait for WhatsApp to load (side panel appears)
        try:
            page.wait_for_selector('div[aria-label="Chat list"]', timeout=120000)
            print("[WhatsApp] Logged in successfully!\n")
            log_activity("LOGIN", "WhatsApp Web session active")
        except Exception:
            # Try alternative selector
            try:
                page.wait_for_selector("#pane-side", timeout=120000)
                print("[WhatsApp] Logged in successfully!\n")
                log_activity("LOGIN", "WhatsApp Web session active")
            except Exception as e:
                print(f"[WhatsApp] Login timeout - please scan QR code. Error: {e}")
                log_activity("LOGIN_TIMEOUT", str(e))
                browser_context.close()
                return

        cycle = 0
        while running:
            cycle += 1
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] WhatsApp scan #{cycle}...", end=" ")

            new_count = 0
            try:
                # Find unread chat items
                unread_chats = page.query_selector_all(
                    'span[aria-label*="unread message"], span[data-testid="icon-unread-count"]'
                )

                for badge in unread_chats:
                    try:
                        # Navigate to parent chat row
                        chat_row = badge.evaluate_handle(
                            "el => el.closest('[data-testid=\"cell-frame-container\"]') || el.closest('[role=\"listitem\"]') || el.closest('[class*=\"chat\"]')"
                        )
                        if not chat_row:
                            continue

                        # Get sender name
                        name_el = chat_row.query_selector("span[title]")
                        sender = name_el.get_attribute("title") if name_el else "Unknown"

                        # Get last message preview
                        msg_el = chat_row.query_selector("span[title][class*='matched']") or \
                                 chat_row.query_selector("span.selectable-text") or \
                                 chat_row.query_selector('[data-testid="last-msg-status"]')
                        message = msg_el.inner_text() if msg_el else ""

                        if not message:
                            continue

                        # Create unique ID
                        msg_hash = f"{sender}:{message[:50]}:{datetime.now().strftime('%Y%m%d%H')}"
                        if msg_hash in seen_messages:
                            continue

                        # Check for keywords
                        if has_keyword(message) or has_keyword(sender):
                            priority = get_priority(message + " " + sender)
                            matched = [kw for kw in HIGH_PRIORITY_KEYWORDS + NORMAL_PRIORITY_KEYWORDS
                                       if kw in (message + " " + sender).lower()]

                            create_vault_file(sender, message, priority, matched)
                            seen_messages.add(msg_hash)
                            new_count += 1

                            icon = "🔴" if priority == "HIGH" else "💬"
                            print(f"\n  {icon} [{priority}] {sender}: {message[:50]}")
                            log_activity("NEW_MESSAGE", f"[{priority}] {sender}: {message[:50]}")

                    except Exception:
                        continue

            except Exception as e:
                log_activity("SCAN_ERROR", str(e))

            save_seen()

            # Update dashboard
            wa_files = list(NEEDS_ACTION.glob("WA_*.md"))
            update_dashboard_wa_count(len(wa_files))

            if new_count > 0:
                print(f"=> {new_count} new message(s)")
            else:
                print("=> No new keyword messages")

            for _ in range(POLL_INTERVAL):
                if not running:
                    break
                time.sleep(1)

        browser_context.close()

    save_seen()
    print("[WhatsApp Watcher] Stopped.")


def main():
    try:
        run_with_playwright()
    except ImportError:
        print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"[ERROR] {e}")
        log_activity("FATAL_ERROR", str(e))


if __name__ == "__main__":
    main()
