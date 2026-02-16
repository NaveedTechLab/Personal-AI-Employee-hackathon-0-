#!/usr/bin/env python3
"""
Approval Flow Watcher - Monitors Approved/Rejected folders for HITL decisions.
When a file is moved to Approved/ or Rejected/, executes the corresponding action.
"""

import os
import time
import signal
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
APPROVED_DIR = VAULT_DIR / "Approved"
REJECTED_DIR = VAULT_DIR / "Rejected"
DONE_DIR = VAULT_DIR / "Done"
LOGS_DIR = VAULT_DIR / "Logs"
POLL_INTERVAL = 5

processed_approved = set()
processed_rejected = set()
running = True


def signal_handler(sig, frame):
    global running
    print("\n[Approval Watcher] Shutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def log_activity(action, details=""):
    log_file = LOGS_DIR / f"approval_flow_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")


def process_approved(filepath):
    """Handle approved action files."""
    try:
        content = filepath.read_text(encoding="utf-8")
        filename = filepath.name

        if filename.startswith("EMAIL_"):
            log_activity("APPROVED_EMAIL", f"Email action approved: {filename}")
            print(f"  [APPROVED] Email: {filename}")
            # In production: would trigger email send via MCP

        elif filename.startswith("WA_"):
            log_activity("APPROVED_WHATSAPP", f"WhatsApp reply approved: {filename}")
            print(f"  [APPROVED] WhatsApp: {filename}")

        elif filename.startswith("FILE_"):
            log_activity("APPROVED_FILE", f"File action approved: {filename}")
            print(f"  [APPROVED] File: {filename}")

        elif filename.startswith("PAYMENT_"):
            log_activity("APPROVED_PAYMENT", f"Payment approved: {filename}")
            print(f"  [APPROVED] Payment: {filename}")

        elif filename.startswith("SOCIAL_"):
            log_activity("APPROVED_SOCIAL", f"Social post approved: {filename}")
            print(f"  [APPROVED] Social: {filename}")

        else:
            log_activity("APPROVED_OTHER", f"Action approved: {filename}")
            print(f"  [APPROVED] {filename}")

        # Move to Done
        done_path = DONE_DIR / filepath.name
        if not done_path.exists():
            import shutil
            shutil.move(str(filepath), str(done_path))
            log_activity("MOVED_TO_DONE", f"{filename} -> Done/")
            print(f"  -> Moved to Done/")

    except Exception as e:
        log_activity("ERROR", f"Processing approved {filepath.name}: {e}")


def process_rejected(filepath):
    """Handle rejected action files."""
    try:
        filename = filepath.name
        log_activity("REJECTED", f"Action rejected: {filename}")
        print(f"  [REJECTED] {filename}")

        # Add rejection note
        content = filepath.read_text(encoding="utf-8")
        content += f"\n\n---\n**REJECTED** at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        filepath.write_text(content, encoding="utf-8")

        # Move to Done with rejected prefix
        done_path = DONE_DIR / f"REJECTED_{filepath.name}"
        if not done_path.exists():
            import shutil
            shutil.move(str(filepath), str(done_path))
            log_activity("MOVED_TO_DONE", f"REJECTED_{filename} -> Done/")

    except Exception as e:
        log_activity("ERROR", f"Processing rejected {filepath.name}: {e}")


def main():
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Mark existing files as already processed
    for f in APPROVED_DIR.iterdir():
        if f.is_file():
            processed_approved.add(f.name)
    for f in REJECTED_DIR.iterdir():
        if f.is_file():
            processed_rejected.add(f.name)

    print("=" * 60)
    print("  Approval Flow Watcher - LIVE MODE")
    print(f"  Approved Dir: {APPROVED_DIR}")
    print(f"  Rejected Dir: {REJECTED_DIR}")
    print(f"  Poll Interval: {POLL_INTERVAL}s")
    print("=" * 60)
    print()

    while running:
        # Check Approved folder
        for f in APPROVED_DIR.iterdir():
            if f.is_file() and f.name not in processed_approved:
                process_approved(f)
                processed_approved.add(f.name)

        # Check Rejected folder
        for f in REJECTED_DIR.iterdir():
            if f.is_file() and f.name not in processed_rejected:
                process_rejected(f)
                processed_rejected.add(f.name)

        for _ in range(POLL_INTERVAL):
            if not running:
                break
            time.sleep(1)

    print("[Approval Watcher] Stopped.")


if __name__ == "__main__":
    main()
