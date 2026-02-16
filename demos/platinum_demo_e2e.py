#!/usr/bin/env python3
"""
Platinum Tier End-to-End Demo
=============================
Demonstrates the minimum passing gate for Platinum tier:

1. Email arrives while Local agent is offline
2. Cloud agent detects email, drafts reply, writes approval file
3. When Local agent returns, user approves
4. Local agent executes send via MCP
5. Action is logged
6. Task file moves to /Done

This script simulates both Cloud and Local agents to demonstrate
the full workflow without requiring actual cloud deployment.
"""

import asyncio
import json
import shutil
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# Vault paths
# ---------------------------------------------------------------------------
VAULT_ROOT = Path("./demo_vault")
INBOX = VAULT_ROOT / "Inbox"
NEEDS_ACTION = VAULT_ROOT / "Needs_Action"
PLANS = VAULT_ROOT / "Plans"
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
APPROVED = VAULT_ROOT / "Approved"
IN_PROGRESS = VAULT_ROOT / "In_Progress"
DONE = VAULT_ROOT / "Done"
LOGS = VAULT_ROOT / "Logs"
UPDATES = VAULT_ROOT / "Updates"
SIGNALS = VAULT_ROOT / "Signals"
DASHBOARD = VAULT_ROOT / "Dashboard.md"

ALL_DIRS = [INBOX, NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED,
            IN_PROGRESS, DONE, LOGS, UPDATES, SIGNALS]

# ---------------------------------------------------------------------------
# ANSI colours for terminal output
# ---------------------------------------------------------------------------
class _C:
    HEADER  = "\033[95m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"


def _ts() -> str:
    """Return a human-readable timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _banner(text: str, colour: str = _C.HEADER) -> None:
    width = 64
    print(f"\n{colour}{_C.BOLD}{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}{_C.RESET}\n")


def _step(number: int, title: str) -> None:
    print(f"{_C.CYAN}{_C.BOLD}--- Step {number}: {title} [{_ts()}] ---{_C.RESET}")


def _ok(msg: str) -> None:
    print(f"  {_C.GREEN}[OK]{_C.RESET} {msg}")


def _info(msg: str) -> None:
    print(f"  {_C.BLUE}[INFO]{_C.RESET} {msg}")


def _warn(msg: str) -> None:
    print(f"  {_C.YELLOW}[WARN]{_C.RESET} {msg}")


def _fail(msg: str) -> None:
    print(f"  {_C.RED}[FAIL]{_C.RESET} {msg}")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
class AgentRole(Enum):
    CLOUD = "cloud"
    LOCAL = "local"


@dataclass
class SimulatedEmail:
    sender: str
    subject: str
    body: str
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: str = ""

    def __post_init__(self):
        if not self.message_id:
            raw = f"{self.sender}:{self.subject}:{self.received_at.isoformat()}"
            self.message_id = hashlib.sha256(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Cloud Agent -- runs in the cloud, never writes Dashboard.md
# ---------------------------------------------------------------------------
class CloudAgent:
    """Simulates the always-on cloud component.

    Responsibilities:
      - Watch for incoming email (simulated)
      - Draft a reply and store it in /Plans/
      - Create an approval request in /Pending_Approval/
      - Write update signals to /Updates/ (never Dashboard.md directly)
    """

    role = AgentRole.CLOUD

    def __init__(self, vault: Path = VAULT_ROOT):
        self.vault = vault

    # -- email detection ------------------------------------------------
    def detect_email(self, email: SimulatedEmail) -> Path:
        """Simulate gmail-watcher detecting an incoming email.

        Creates an action file in /Inbox/ representing the raw event.
        Returns the path of the created file.
        """
        safe_subject = "".join(c if c.isalnum() or c in (" ", "-") else "_"
                               for c in email.subject).strip().replace(" ", "_")
        ts = email.received_at.strftime("%Y%m%d_%H%M%S")
        filename = f"email_{ts}_{safe_subject[:40]}.md"
        filepath = self.vault / "Inbox" / filename

        content = f"""---
source: gmail
sender: "{email.sender}"
subject: "{email.subject}"
received_at: "{email.received_at.isoformat()}"
message_id: "{email.message_id}"
status: new
claimed_by: cloud
---

# Incoming Email

**From:** {email.sender}
**Subject:** {email.subject}
**Received:** {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

## Body

{email.body}
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    # -- draft reply ----------------------------------------------------
    def draft_reply(self, email: SimulatedEmail) -> Path:
        """Create a draft reply in /Plans/.

        In production this would call Claude to generate the draft.
        Here we produce a deterministic professional reply.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"draft_reply_{email.message_id}_{ts}.md"
        filepath = self.vault / "Plans" / filename

        draft_body = (
            f"Dear {email.sender.split('@')[0].replace('.', ' ').title()},\n\n"
            f"Thank you for reaching out regarding \"{email.subject}\".\n\n"
            f"I have reviewed your request and prepared the relevant information. "
            f"Please find the details below:\n\n"
            f"- Your request has been logged and assigned a tracking ID: {email.message_id}\n"
            f"- Expected turnaround: 24 business hours\n"
            f"- If you need immediate assistance, please call our support line.\n\n"
            f"Best regards,\n"
            f"Personal AI Employee\n"
        )

        content = f"""---
type: draft_reply
in_reply_to: "{email.message_id}"
sender: "{email.sender}"
subject: "Re: {email.subject}"
created_at: "{datetime.now(timezone.utc).isoformat()}"
created_by: cloud
status: draft
---

# Draft Reply

**To:** {email.sender}
**Subject:** Re: {email.subject}

## Draft Body

{draft_body}

## Context

Original email received at {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}.
Draft auto-generated by Cloud agent.  Requires local approval before sending.
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    # -- approval request -----------------------------------------------
    def create_approval_request(self, email: SimulatedEmail,
                                draft_path: Path) -> Path:
        """Write an approval file to /Pending_Approval/.

        Encodes the action to execute (send email via MCP) and the draft
        reference so the Local agent knows what to approve.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"approve_send_{email.message_id}_{ts}.md"
        filepath = self.vault / "Pending_Approval" / filename

        action_payload = json.dumps({
            "action": "send_email",
            "to": email.sender,
            "subject": f"Re: {email.subject}",
            "draft_file": str(draft_path.relative_to(self.vault)),
            "original_message_id": email.message_id,
        }, indent=2)

        content = f"""---
type: approval_request
action: send_email
message_id: "{email.message_id}"
to: "{email.sender}"
draft_file: "{draft_path.name}"
created_at: "{datetime.now(timezone.utc).isoformat()}"
created_by: cloud
status: pending_approval
requires_approval: true
---

# Approval Request -- Send Email Reply

**Action:** Send drafted email reply to {email.sender}
**Subject:** Re: {email.subject}
**Draft:** [{draft_path.name}](Plans/{draft_path.name})

## Action Payload

```json
{action_payload}
```

## Instructions

Move this file to `/Approved/` to authorise the Local agent to send.
Move this file to `/Rejected/` to discard.

---
*This action requires human approval before execution.*
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    # -- update signal ---------------------------------------------------
    def write_update_signal(self, email: SimulatedEmail,
                            draft_path: Path,
                            approval_path: Path) -> Path:
        """Write a signal file to /Updates/ for the Local agent to merge
        into Dashboard.md (single-writer rule: only Local writes Dashboard).
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"signal_{email.message_id}_{ts}.md"
        filepath = self.vault / "Updates" / filename

        content = f"""---
type: update_signal
message_id: "{email.message_id}"
created_at: "{datetime.now(timezone.utc).isoformat()}"
created_by: cloud
---

# Update Signal

- New email from **{email.sender}**: "{email.subject}"
- Draft reply created: `{draft_path.name}`
- Approval pending: `{approval_path.name}`
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath


# ---------------------------------------------------------------------------
# Local Agent -- runs on the user's machine, owns Dashboard.md
# ---------------------------------------------------------------------------
class LocalAgent:
    """Simulates the local component that resumes when the user is back.

    Responsibilities:
      - Scan /Pending_Approval/ for work
      - Move file to /Approved/ (claim-by-move)
      - Execute the send action via MCP (simulated / dry-run)
      - Write audit log to /Logs/
      - Move all artefacts to /Done/
      - Update Dashboard.md (single-writer)
    """

    role = AgentRole.LOCAL

    def __init__(self, vault: Path = VAULT_ROOT):
        self.vault = vault

    # -- scan for approvals ---------------------------------------------
    def check_for_approvals(self) -> List[Path]:
        """Return list of files in /Pending_Approval/."""
        pa = self.vault / "Pending_Approval"
        return sorted(pa.glob("*.md"))

    # -- approve (claim-by-move) ----------------------------------------
    def approve_action(self, approval_file: Path) -> Path:
        """Move file from /Pending_Approval/ to /Approved/.

        This atomic move is the *claim-by-move* rule: the first agent to
        successfully move the file owns the action.
        """
        dest = self.vault / "Approved" / approval_file.name
        shutil.move(str(approval_file), str(dest))

        # Patch status in frontmatter
        text = dest.read_text(encoding="utf-8")
        text = text.replace("status: pending_approval", "status: approved")
        dest.write_text(text, encoding="utf-8")
        return dest

    # -- execute send via MCP (dry-run) ---------------------------------
    def execute_send(self, approved_file: Path) -> Dict[str, Any]:
        """Simulate executing the send-email action via MCP.

        In production this would call the gmail MCP server.
        Returns a result dict describing what happened.
        """
        text = approved_file.read_text(encoding="utf-8")

        # Extract action payload from the markdown code block
        payload: Dict[str, Any] = {}
        if "```json" in text:
            json_block = text.split("```json")[1].split("```")[0].strip()
            payload = json.loads(json_block)

        result = {
            "status": "success",
            "dry_run": True,
            "action": payload.get("action", "send_email"),
            "to": payload.get("to", "unknown"),
            "subject": payload.get("subject", "unknown"),
            "message_id": payload.get("original_message_id", "unknown"),
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "executed_by": "local",
            "mcp_server": "gmail-mcp (simulated)",
        }

        # Mark file as executed
        text = text.replace("status: approved", "status: executed")
        approved_file.write_text(text, encoding="utf-8")

        return result

    # -- audit log -------------------------------------------------------
    def log_action(self, action_details: Dict[str, Any]) -> Path:
        """Write an immutable audit log entry to /Logs/."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        mid = action_details.get("message_id", "unknown")
        filename = f"audit_{mid}_{ts}.md"
        filepath = self.vault / "Logs" / filename

        content = f"""---
type: audit_log
action: "{action_details.get('action', 'unknown')}"
message_id: "{mid}"
executed_at: "{action_details.get('executed_at', '')}"
executed_by: "{action_details.get('executed_by', 'local')}"
dry_run: {str(action_details.get('dry_run', True)).lower()}
status: "{action_details.get('status', 'unknown')}"
---

# Audit Log Entry

| Field | Value |
|-------|-------|
| Action | {action_details.get('action', 'unknown')} |
| To | {action_details.get('to', 'unknown')} |
| Subject | {action_details.get('subject', 'unknown')} |
| MCP Server | {action_details.get('mcp_server', 'unknown')} |
| Status | {action_details.get('status', 'unknown')} |
| Dry Run | {action_details.get('dry_run', True)} |
| Executed At | {action_details.get('executed_at', '')} |
| Executed By | {action_details.get('executed_by', 'local')} |

## Full Payload

```json
{json.dumps(action_details, indent=2)}
```
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    # -- move to done ----------------------------------------------------
    def move_to_done(self, files: List[Path]) -> List[Path]:
        """Move all related artefact files to /Done/.

        Returns the new paths.
        """
        done_dir = self.vault / "Done"
        moved: List[Path] = []
        for f in files:
            if f.exists():
                dest = done_dir / f.name
                shutil.move(str(f), str(dest))
                moved.append(dest)
        return moved

    # -- update dashboard (single-writer) --------------------------------
    def update_dashboard(self, action_summary: str) -> Path:
        """Append an entry to Dashboard.md.

        Only the Local agent ever writes to Dashboard.md
        (single-writer rule).
        """
        dashboard = self.vault / "Dashboard.md"

        if not dashboard.exists():
            header = (
                "---\n"
                "title: Personal AI Employee Dashboard\n"
                f"updated_at: \"{datetime.now(timezone.utc).isoformat()}\"\n"
                "writer: local\n"
                "---\n\n"
                "# Personal AI Employee -- Dashboard\n\n"
                "| Timestamp | Summary | Status |\n"
                "|-----------|---------|--------|\n"
            )
            dashboard.write_text(header, encoding="utf-8")

        existing = dashboard.read_text(encoding="utf-8")

        # Update the updated_at timestamp
        import re
        existing = re.sub(
            r'updated_at: ".*?"',
            f'updated_at: "{datetime.now(timezone.utc).isoformat()}"',
            existing
        )

        row = (
            f"| {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"| {action_summary} | completed |\n"
        )
        existing += row
        dashboard.write_text(existing, encoding="utf-8")
        return dashboard


# ---------------------------------------------------------------------------
# Platinum Demo Orchestrator
# ---------------------------------------------------------------------------
class PlatinumDemo:
    """Orchestrates the full Platinum-tier E2E demo."""

    def __init__(self, vault_root: Path = VAULT_ROOT):
        self.vault_root = vault_root
        self.cloud = CloudAgent(vault_root)
        self.local = LocalAgent(vault_root)

        # Artefact tracking
        self.inbox_file: Optional[Path] = None
        self.draft_file: Optional[Path] = None
        self.approval_file: Optional[Path] = None
        self.approved_file: Optional[Path] = None
        self.signal_file: Optional[Path] = None
        self.log_file: Optional[Path] = None
        self.done_files: List[Path] = []
        self.execution_result: Dict[str, Any] = {}

    # -- setup -----------------------------------------------------------
    def setup_vault(self) -> None:
        """Create (or reset) the vault directory structure."""
        for d in ALL_DIRS:
            d.mkdir(parents=True, exist_ok=True)
        _ok(f"Vault directories ready at {self.vault_root.resolve()}")

    # -- cleanup stale files (optional) ----------------------------------
    def cleanup_vault(self) -> None:
        """Remove previous demo artefacts so the run is clean."""
        for d in ALL_DIRS:
            for f in d.glob("*.md"):
                f.unlink()
        if DASHBOARD.exists():
            DASHBOARD.unlink()
        _ok("Previous demo artefacts cleaned")

    # -- main demo -------------------------------------------------------
    def run_demo(self) -> bool:
        """Execute the full Platinum workflow. Returns True if gate passes."""

        _banner("PLATINUM TIER  --  END-TO-END DEMO")

        # -------- Setup -------------------------------------------------
        _step(0, "Setup vault structure")
        self.setup_vault()
        self.cleanup_vault()

        # -------- Simulate email arrival while Local is offline ---------
        _step(1, "Email arrives while Local agent is OFFLINE")
        email = SimulatedEmail(
            sender="sarah.chen@acmecorp.com",
            subject="Invoice #2026-0042 overdue - please advise",
            body=(
                "Hi,\n\n"
                "I hope this finds you well.  I wanted to follow up on "
                "Invoice #2026-0042 which was due on 2026-01-15.  Our "
                "records show it remains unpaid.\n\n"
                "Could you please confirm the payment status or let me "
                "know if there are any issues?  I have attached the "
                "original invoice for reference.\n\n"
                "Kind regards,\n"
                "Sarah Chen\n"
                "Accounts Receivable, Acme Corp"
            ),
        )
        _info(f"Email from: {email.sender}")
        _info(f"Subject:    {email.subject}")
        _info(f"Received:   {email.received_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        _warn("Local agent is OFFLINE -- Cloud agent handles triage")

        # -------- Cloud detects email -----------------------------------
        _step(2, "Cloud agent detects email via gmail-watcher")
        self.inbox_file = self.cloud.detect_email(email)
        _ok(f"Inbox file created: {self.inbox_file.name}")

        # -------- Cloud drafts reply ------------------------------------
        _step(3, "Cloud agent drafts reply (writes to /Plans/)")
        self.draft_file = self.cloud.draft_reply(email)
        _ok(f"Draft created: {self.draft_file.name}")

        # -------- Cloud creates approval request ------------------------
        _step(4, "Cloud agent creates approval request in /Pending_Approval/")
        self.approval_file = self.cloud.create_approval_request(
            email, self.draft_file
        )
        _ok(f"Approval file: {self.approval_file.name}")

        # -------- Cloud writes update signal ----------------------------
        _step(5, "Cloud writes update signal to /Updates/")
        self.signal_file = self.cloud.write_update_signal(
            email, self.draft_file, self.approval_file
        )
        _ok(f"Signal file: {self.signal_file.name}")

        # -------- Simulated delay while user is away --------------------
        _step(6, "User is away ... Local agent is offline")
        _info("(simulating passage of time)")
        time.sleep(0.5)

        # -------- Local comes back online -------------------------------
        _step(7, "Local agent comes back online -- scans for approvals")
        pending = self.local.check_for_approvals()
        _info(f"Found {len(pending)} pending approval(s)")
        if not pending:
            _fail("No pending approvals found -- aborting")
            return False
        for p in pending:
            _info(f"  -> {p.name}")

        # -------- User approves (claim-by-move) -------------------------
        _step(8, "User approves action (claim-by-move rule)")
        self.approved_file = self.local.approve_action(pending[0])
        _ok(f"Moved to /Approved/: {self.approved_file.name}")
        _info("Claim-by-move: file atomically moved; no other agent can claim it")

        # -------- Local executes send via MCP ---------------------------
        _step(9, "Local agent executes send via MCP (dry-run)")
        self.execution_result = self.local.execute_send(self.approved_file)
        _ok(f"MCP send executed (dry_run={self.execution_result['dry_run']})")
        _info(f"  To:      {self.execution_result['to']}")
        _info(f"  Subject: {self.execution_result['subject']}")
        _info(f"  Server:  {self.execution_result['mcp_server']}")

        # -------- Audit log ---------------------------------------------
        _step(10, "Local agent writes audit log to /Logs/")
        self.log_file = self.local.log_action(self.execution_result)
        _ok(f"Audit log: {self.log_file.name}")

        # -------- Move to /Done/ ----------------------------------------
        _step(11, "Move all artefacts to /Done/")
        files_to_move = [
            f for f in [
                self.inbox_file, self.draft_file,
                self.approved_file, self.signal_file,
            ] if f is not None and f.exists()
        ]
        self.done_files = self.local.move_to_done(files_to_move)
        for d in self.done_files:
            _ok(f"  -> /Done/{d.name}")

        # -------- Update Dashboard (single-writer) ----------------------
        _step(12, "Local agent updates Dashboard.md (single-writer rule)")
        summary = (
            f"Replied to {email.sender} re: \"{email.subject}\" "
            f"[msg:{email.message_id}]"
        )
        self.local.update_dashboard(summary)
        _ok("Dashboard.md updated by Local agent (sole writer)")

        # -------- Verification ------------------------------------------
        return self.verify_completion()

    # -- verify ----------------------------------------------------------
    def verify_completion(self) -> bool:
        """Run all gate checks and print PASS/FAIL."""
        _banner("VERIFICATION", _C.YELLOW)
        checks_passed = 0
        checks_total = 0

        def _check(condition: bool, label: str) -> bool:
            nonlocal checks_passed, checks_total
            checks_total += 1
            if condition:
                checks_passed += 1
                _ok(label)
            else:
                _fail(label)
            return condition

        # 1 - Inbox file created (may have been moved to Done)
        inbox_in_done = any("email_" in f.name for f in (self.vault_root / "Done").glob("*.md"))
        _check(inbox_in_done, "Inbox email file exists in /Done/")

        # 2 - Draft exists in /Done/
        draft_in_done = any("draft_reply_" in f.name for f in (self.vault_root / "Done").glob("*.md"))
        _check(draft_in_done, "Draft reply file exists in /Done/")

        # 3 - Approval file was moved out of /Pending_Approval/
        pending_empty = len(list((self.vault_root / "Pending_Approval").glob("*.md"))) == 0
        _check(pending_empty, "/Pending_Approval/ is empty (file was claimed)")

        # 4 - Approved file moved to /Done/
        approved_in_done = any("approve_send_" in f.name for f in (self.vault_root / "Done").glob("*.md"))
        _check(approved_in_done, "Approved action file exists in /Done/")

        # 5 - Audit log exists
        log_exists = len(list((self.vault_root / "Logs").glob("audit_*.md"))) > 0
        _check(log_exists, "Audit log entry exists in /Logs/")

        # 6 - Log contains correct action
        if self.log_file and self.log_file.exists():
            log_text = self.log_file.read_text(encoding="utf-8")
            _check("send_email" in log_text, "Audit log records send_email action")
            _check("dry_run" in log_text.lower(), "Audit log records dry_run flag")
        else:
            _check(False, "Audit log records send_email action")
            _check(False, "Audit log records dry_run flag")

        # 7 - Dashboard updated
        _check(DASHBOARD.exists(), "Dashboard.md exists")
        if DASHBOARD.exists():
            dash_text = DASHBOARD.read_text(encoding="utf-8")
            _check("writer: local" in dash_text, "Dashboard.md declares writer: local")
            _check("completed" in dash_text, "Dashboard.md contains completion entry")
        else:
            _check(False, "Dashboard.md declares writer: local")
            _check(False, "Dashboard.md contains completion entry")

        # 8 - No secrets in vault markdown files
        secrets_found = False
        for md in self.vault_root.rglob("*.md"):
            text = md.read_text(encoding="utf-8")
            for keyword in ["api_key", "password", "secret_key", "token=",
                            "Bearer ", "ANTHROPIC_API_KEY"]:
                if keyword.lower() in text.lower():
                    _fail(f"Potential secret found in {md.name}: {keyword}")
                    secrets_found = True
                    break
        _check(not secrets_found, "No credentials/secrets found in vault files")

        # 9 - Single-writer rule: Cloud never wrote Dashboard
        # (We verify by checking that Dashboard writer is 'local')
        if DASHBOARD.exists():
            dash_text = DASHBOARD.read_text(encoding="utf-8")
            _check("writer: local" in dash_text and "writer: cloud" not in dash_text,
                   "Single-writer rule: only Local wrote Dashboard.md")
        else:
            _check(False, "Single-writer rule: only Local wrote Dashboard.md")

        # -------- Final verdict ------------------------------------------
        _banner("RESULTS", _C.GREEN if checks_passed == checks_total else _C.RED)
        print(f"  Checks passed: {checks_passed}/{checks_total}")

        if checks_passed == checks_total:
            print(f"\n  {_C.GREEN}{_C.BOLD}*** PLATINUM GATE: PASS ***{_C.RESET}\n")
            return True
        else:
            print(f"\n  {_C.RED}{_C.BOLD}*** PLATINUM GATE: FAIL ***{_C.RESET}\n")
            return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    demo = PlatinumDemo()
    passed = demo.run_demo()
    raise SystemExit(0 if passed else 1)
