#!/usr/bin/env python3
"""
Live Filesystem Watcher - Monitors Inbox folder for dropped files.
Creates action files in Needs_Action when new files arrive.
"""

import os
import re
import time
import signal
import sys
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION = VAULT_DIR / "Needs_Action"
LOGS_DIR = VAULT_DIR / "Logs"
POLL_INTERVAL = 10  # seconds

processed_files = set()
running = True


def signal_handler(sig, frame):
    global running
    print("\n[File Watcher] Shutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_file_info(filepath):
    stat = filepath.stat()
    mime_type = mimetypes.guess_type(str(filepath))[0] or "application/octet-stream"
    size = stat.st_size
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"
    return mime_type, size_str


def create_action_file(filepath):
    mime_type, size_str = get_file_info(filepath)
    safe_name = re.sub(r"[^a-zA-Z0-9_.]", "_", filepath.name)[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FILE_{timestamp}_{safe_name}.md"

    # Determine category
    ext = filepath.suffix.lower()
    if ext in [".pdf", ".doc", ".docx", ".txt"]:
        category = "document"
    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        category = "image"
    elif ext in [".csv", ".xlsx", ".xls"]:
        category = "spreadsheet"
    elif ext in [".mp4", ".mov", ".avi"]:
        category = "video"
    else:
        category = "file"

    content = f"""---
type: file_action
source: filesystem
category: {category}
mime_type: {mime_type}
status: needs_action
created: {datetime.now().isoformat()}
---

# File Dropped: {filepath.name}

| Field | Value |
|-------|-------|
| **Filename** | {filepath.name} |
| **Type** | {mime_type} |
| **Size** | {size_str} |
| **Category** | {category} |
| **Location** | {filepath} |
| **Dropped** | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |

## Action Required
- [ ] Review file contents
- [ ] Process / categorize
- [ ] Move to [[Done]] when complete

> Detected by File Watcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    action_path = NEEDS_ACTION / filename
    action_path.write_text(content, encoding="utf-8")
    return action_path


def log_activity(action, details=""):
    log_file = LOGS_DIR / f"file_watcher_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")


def main():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Initial scan - mark existing files as seen
    for f in INBOX_DIR.iterdir():
        if f.is_file():
            processed_files.add(str(f))

    print("=" * 60)
    print("  Filesystem Watcher - LIVE MODE")
    print(f"  Watching: {INBOX_DIR}")
    print(f"  Poll Interval: {POLL_INTERVAL}s")
    print(f"  Existing files: {len(processed_files)} (skipped)")
    print("=" * 60)
    print()

    cycle = 0
    while running:
        cycle += 1
        new_count = 0

        try:
            for f in INBOX_DIR.iterdir():
                if f.is_file() and str(f) not in processed_files:
                    action_path = create_action_file(f)
                    processed_files.add(str(f))
                    new_count += 1
                    print(f"  📁 New file: {f.name} => {action_path.name}")
                    log_activity("NEW_FILE", f"{f.name}")
        except Exception as e:
            log_activity("ERROR", str(e))

        if new_count > 0 and cycle > 1:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] {new_count} new file(s) detected")

        for _ in range(POLL_INTERVAL):
            if not running:
                break
            time.sleep(1)

    print("[File Watcher] Stopped.")


if __name__ == "__main__":
    main()
