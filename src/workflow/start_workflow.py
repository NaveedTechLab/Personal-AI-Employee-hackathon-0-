#!/usr/bin/env python3
"""
AI Employee - Master Workflow Launcher
Starts all watchers and the orchestrator in parallel.

Usage:
    python start_workflow.py              # Start all (Gmail + File + WhatsApp)
    python start_workflow.py --no-whatsapp  # Without WhatsApp (no browser needed)
    python start_workflow.py --gmail-only   # Only Gmail watcher
"""

import subprocess
import sys
import signal
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
PROJECT_DIR = Path(__file__).parent.parent.parent  # repo root

# Detect OS and set correct Python path
if os.name == "nt":  # Windows
    VENV_PYTHON = str(PROJECT_DIR / "venv-win" / "Scripts" / "python.exe")
    if not Path(VENV_PYTHON).exists():
        VENV_PYTHON = sys.executable  # fallback to current python
else:  # Linux/Mac
    VENV_PYTHON = str(PROJECT_DIR / "venv" / "bin" / "python")
    if not Path(VENV_PYTHON).exists():
        VENV_PYTHON = sys.executable

processes = []
running = True


def signal_handler(sig, frame):
    global running
    running = False
    print("\n\n" + "=" * 60)
    print("  Shutting down all watchers...")
    print("=" * 60)
    for name, proc in processes:
        try:
            proc.terminate()
            print(f"  Stopped: {name}")
        except Exception:
            pass
    # Wait for graceful shutdown
    time.sleep(2)
    for name, proc in processes:
        try:
            proc.kill()
        except Exception:
            pass
    print("  All watchers stopped.")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def start_process(name, script, extra_args=None):
    cmd = [VENV_PYTHON, str(PROJECT_DIR / script)]
    if extra_args:
        cmd.extend(extra_args)
    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )
    processes.append((name, proc))
    print(f"  Started: {name} (PID: {proc.pid})")
    return proc


def update_dashboard_status(component, status):
    dashboard = VAULT_DIR / "Dashboard.md"
    if dashboard.exists():
        import re
        content = dashboard.read_text(encoding="utf-8")
        icon = "🟢" if status == "Running" else "🔴"
        # Update the system health table
        pattern = rf"\| {component}\s*\|.*\|.*\|"
        replacement = f"| {component} | {icon} {status} | {datetime.now().strftime('%H:%M:%S')} |"
        content = re.sub(pattern, replacement, content)
        # Update last check time
        content = re.sub(
            r"\*\*Last Check:\*\* `[^`]*`",
            f"**Last Check:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}`",
            content
        )
        dashboard.write_text(content, encoding="utf-8")


def print_output(name, proc):
    """Read and print one line from process if available."""
    try:
        line = proc.stdout.readline()
        if line:
            print(f"  [{name}] {line.strip()}")
            return True
    except Exception:
        pass
    return False


def main():
    no_whatsapp = "--no-whatsapp" in sys.argv
    gmail_only = "--gmail-only" in sys.argv

    print()
    print("=" * 60)
    print("  AI Employee - Full Workflow Launcher")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Vault: {VAULT_DIR}")
    print(f"  Python: {VENV_PYTHON}")
    print("=" * 60)
    print()

    # Ensure vault dirs exist
    for d in ["Inbox", "Needs_Action/Gmail", "Needs_Action/WhatsApp",
              "Needs_Action/Finance", "Plans", "Pending_Approval", "Approved",
              "Rejected", "Done", "Logs", "Briefings", "Accounting",
              "In_Progress/cloud", "In_Progress/local"]:
        (VAULT_DIR / d).mkdir(parents=True, exist_ok=True)

    # Start watchers
    print("Starting watchers...")
    print("-" * 40)

    # 1. Gmail Watcher (always)
    gmail_proc = start_process("Gmail Watcher", "src/watchers/gmail_watcher_live.py")
    update_dashboard_status("Gmail Watcher", "Running")

    if not gmail_only:
        # 2. File Watcher
        file_proc = start_process("File Watcher", "src/watchers/file_watcher_live.py")
        update_dashboard_status("File Watcher", "Running")

        # 3. WhatsApp Watcher (optional - needs browser)
        if not no_whatsapp:
            wa_proc = start_process("WhatsApp Watcher", "src/watchers/whatsapp_watcher_live.py")
            update_dashboard_status("WhatsApp Watcher", "Running")
        else:
            print("  Skipped: WhatsApp Watcher (--no-whatsapp)")

        # 4. Orchestrator (processes Needs_Action → Plans → Pending_Approval)
        orchestrator_proc = start_process("Orchestrator", "src/orchestrator/orchestrator_live.py")
        update_dashboard_status("Orchestrator", "Running")

        # 5. Approval Flow Watcher
        approval_proc = start_process("Approval Watcher", "src/watchers/approval_watcher.py")

        # 6. Scheduler (CEO Briefing, Subscription Audit, Daily Summary)
        scheduler_proc = start_process("Scheduler", "src/orchestrator/scheduler_live.py")

        # 7. MCP Servers (Social Media, Odoo, Email, Calendar, Slack, Payment)
        mcp_proc = start_process("MCP Servers", "src/mcp_servers/start_mcp_servers.py")

    print("-" * 40)
    print(f"\n  {len(processes)} watcher(s) running!")
    print("  Press Ctrl+C to stop all\n")
    print("=" * 60)
    print()

    # Monitor processes and print their output
    while running:
        any_output = False
        for name, proc in processes:
            if proc.poll() is not None:
                print(f"\n  [WARNING] {name} exited with code {proc.returncode}")
                update_dashboard_status(name.replace(" Watcher", ""), "Stopped")
                # Auto-restart
                print(f"  [RESTART] Restarting {name}...")
                script_map = {
                    "Gmail Watcher": "src/watchers/gmail_watcher_live.py",
                    "File Watcher": "src/watchers/file_watcher_live.py",
                    "WhatsApp Watcher": "src/watchers/whatsapp_watcher_live.py",
                    "Orchestrator": "src/orchestrator/orchestrator_live.py",
                    "Approval Watcher": "src/watchers/approval_watcher.py",
                    "Scheduler": "src/orchestrator/scheduler_live.py",
                    "MCP Servers": "src/mcp_servers/start_mcp_servers.py",
                }
                if name in script_map:
                    new_proc = start_process(name, script_map[name])
                    # Replace in processes list
                    for i, (n, p) in enumerate(processes):
                        if n == name and p == proc:
                            processes[i] = (name, new_proc)
                            break
                    update_dashboard_status(name.replace(" Watcher", ""), "Running")
                continue

            if print_output(name, proc):
                any_output = True

        if not any_output:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
