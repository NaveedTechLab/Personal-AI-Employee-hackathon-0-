#!/usr/bin/env python3
"""
Pytest suite for the Platinum Tier End-to-End Demo.

Validates every stage of the Platinum gate:
  Email -> Cloud draft -> Approval -> Local execute -> Log -> /Done

Run with:
    pytest test_platinum_demo.py -v
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from platinum_demo_e2e import (
    CloudAgent,
    LocalAgent,
    PlatinumDemo,
    SimulatedEmail,
    VAULT_ROOT,
    ALL_DIRS,
    DASHBOARD,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
TEST_VAULT = Path("./test_demo_vault")


def _make_dirs(root: Path) -> None:
    for d in [
        "Inbox", "Needs_Action", "Plans", "Pending_Approval",
        "Approved", "In_Progress", "Done", "Logs", "Updates", "Signals",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path: Path, monkeypatch):
    """Give every test its own clean vault directory.

    We patch the module-level VAULT_ROOT so that the agents
    pick up the temporary path automatically when constructed
    with default arguments.
    """
    vault = tmp_path / "demo_vault"
    _make_dirs(vault)

    import platinum_demo_e2e as mod
    monkeypatch.setattr(mod, "VAULT_ROOT", vault)
    monkeypatch.setattr(mod, "INBOX", vault / "Inbox")
    monkeypatch.setattr(mod, "NEEDS_ACTION", vault / "Needs_Action")
    monkeypatch.setattr(mod, "PLANS", vault / "Plans")
    monkeypatch.setattr(mod, "PENDING_APPROVAL", vault / "Pending_Approval")
    monkeypatch.setattr(mod, "APPROVED", vault / "Approved")
    monkeypatch.setattr(mod, "IN_PROGRESS", vault / "In_Progress")
    monkeypatch.setattr(mod, "DONE", vault / "Done")
    monkeypatch.setattr(mod, "LOGS", vault / "Logs")
    monkeypatch.setattr(mod, "UPDATES", vault / "Updates")
    monkeypatch.setattr(mod, "SIGNALS", vault / "Signals")
    monkeypatch.setattr(mod, "DASHBOARD", vault / "Dashboard.md")
    monkeypatch.setattr(mod, "ALL_DIRS", [
        vault / "Inbox", vault / "Needs_Action", vault / "Plans",
        vault / "Pending_Approval", vault / "Approved", vault / "In_Progress",
        vault / "Done", vault / "Logs", vault / "Updates", vault / "Signals",
    ])

    yield vault


@pytest.fixture
def sample_email() -> SimulatedEmail:
    return SimulatedEmail(
        sender="sarah.chen@acmecorp.com",
        subject="Invoice #2026-0042 overdue - please advise",
        body=(
            "Hi,\n\nI wanted to follow up on Invoice #2026-0042 which was "
            "due on 2026-01-15. Could you confirm the payment status?\n\n"
            "Kind regards,\nSarah Chen"
        ),
    )


# ---------------------------------------------------------------------------
# 1. Vault setup
# ---------------------------------------------------------------------------
class TestVaultSetup:

    def test_vault_setup(self, isolated_vault: Path):
        """Verify that PlatinumDemo.setup_vault creates all directories."""
        # Remove them first to prove setup creates them
        shutil.rmtree(isolated_vault)
        demo = PlatinumDemo(isolated_vault)
        demo.setup_vault()

        expected = [
            "Inbox", "Needs_Action", "Plans", "Pending_Approval",
            "Approved", "In_Progress", "Done", "Logs", "Updates", "Signals",
        ]
        for d in expected:
            assert (isolated_vault / d).is_dir(), f"Missing directory: {d}"

    def test_vault_setup_idempotent(self, isolated_vault: Path):
        """setup_vault can be called twice without error."""
        demo = PlatinumDemo(isolated_vault)
        demo.setup_vault()
        demo.setup_vault()  # second call should not raise
        assert (isolated_vault / "Inbox").is_dir()


# ---------------------------------------------------------------------------
# 2. Cloud email detection
# ---------------------------------------------------------------------------
class TestCloudEmailDetection:

    def test_cloud_email_detection(self, isolated_vault: Path,
                                    sample_email: SimulatedEmail):
        """detect_email creates a file in /Inbox/."""
        cloud = CloudAgent(isolated_vault)
        inbox_file = cloud.detect_email(sample_email)

        assert inbox_file.exists()
        assert inbox_file.parent == isolated_vault / "Inbox"

        text = inbox_file.read_text(encoding="utf-8")
        assert sample_email.sender in text
        assert sample_email.subject in text
        assert "claimed_by: cloud" in text

    def test_email_file_contains_body(self, isolated_vault: Path,
                                       sample_email: SimulatedEmail):
        """The inbox file should contain the email body."""
        cloud = CloudAgent(isolated_vault)
        inbox_file = cloud.detect_email(sample_email)
        text = inbox_file.read_text(encoding="utf-8")
        assert "Invoice #2026-0042" in text


# ---------------------------------------------------------------------------
# 3. Cloud draft creation
# ---------------------------------------------------------------------------
class TestCloudDraftCreation:

    def test_cloud_draft_creation(self, isolated_vault: Path,
                                   sample_email: SimulatedEmail):
        """draft_reply creates a file in /Plans/."""
        cloud = CloudAgent(isolated_vault)
        draft = cloud.draft_reply(sample_email)

        assert draft.exists()
        assert draft.parent == isolated_vault / "Plans"

        text = draft.read_text(encoding="utf-8")
        assert "Re:" in text
        assert sample_email.sender in text
        assert "created_by: cloud" in text
        assert "status: draft" in text

    def test_draft_references_original(self, isolated_vault: Path,
                                        sample_email: SimulatedEmail):
        """Draft should reference the original message id."""
        cloud = CloudAgent(isolated_vault)
        draft = cloud.draft_reply(sample_email)
        text = draft.read_text(encoding="utf-8")
        assert sample_email.message_id in text


# ---------------------------------------------------------------------------
# 4. Approval file creation
# ---------------------------------------------------------------------------
class TestApprovalFileCreation:

    def test_approval_file_creation(self, isolated_vault: Path,
                                     sample_email: SimulatedEmail):
        """create_approval_request writes to /Pending_Approval/."""
        cloud = CloudAgent(isolated_vault)
        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)

        assert approval.exists()
        assert approval.parent == isolated_vault / "Pending_Approval"

        text = approval.read_text(encoding="utf-8")
        assert "requires_approval: true" in text
        assert "status: pending_approval" in text
        assert "send_email" in text

    def test_approval_contains_json_payload(self, isolated_vault: Path,
                                             sample_email: SimulatedEmail):
        """Approval file includes a parseable JSON action payload."""
        cloud = CloudAgent(isolated_vault)
        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)

        text = approval.read_text(encoding="utf-8")
        json_block = text.split("```json")[1].split("```")[0].strip()
        payload = json.loads(json_block)

        assert payload["action"] == "send_email"
        assert payload["to"] == sample_email.sender


# ---------------------------------------------------------------------------
# 5. Approval workflow (claim-by-move)
# ---------------------------------------------------------------------------
class TestApprovalWorkflow:

    def test_approval_workflow(self, isolated_vault: Path,
                                sample_email: SimulatedEmail):
        """approve_action moves file from Pending_Approval to Approved."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)

        approved = local.approve_action(approval)

        assert approved.exists()
        assert approved.parent == isolated_vault / "Approved"
        assert not approval.exists(), "Original file should no longer exist"

        text = approved.read_text(encoding="utf-8")
        assert "status: approved" in text

    def test_pending_empty_after_approval(self, isolated_vault: Path,
                                           sample_email: SimulatedEmail):
        """After approval, /Pending_Approval/ has no remaining files."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        local.approve_action(approval)

        remaining = list((isolated_vault / "Pending_Approval").glob("*.md"))
        assert len(remaining) == 0


# ---------------------------------------------------------------------------
# 6. Local execution (MCP send)
# ---------------------------------------------------------------------------
class TestLocalExecution:

    def test_local_execution(self, isolated_vault: Path,
                              sample_email: SimulatedEmail):
        """execute_send returns a success result and marks the file."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        approved = local.approve_action(approval)

        result = local.execute_send(approved)

        assert result["status"] == "success"
        assert result["dry_run"] is True
        assert result["action"] == "send_email"
        assert result["to"] == sample_email.sender

    def test_execution_updates_status(self, isolated_vault: Path,
                                       sample_email: SimulatedEmail):
        """After execution the file status should be 'executed'."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        approved = local.approve_action(approval)
        local.execute_send(approved)

        text = approved.read_text(encoding="utf-8")
        assert "status: executed" in text


# ---------------------------------------------------------------------------
# 7. Audit logging
# ---------------------------------------------------------------------------
class TestAuditLogging:

    def test_audit_logging(self, isolated_vault: Path,
                            sample_email: SimulatedEmail):
        """log_action creates an audit file in /Logs/."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        approved = local.approve_action(approval)
        result = local.execute_send(approved)
        log_file = local.log_action(result)

        assert log_file.exists()
        assert log_file.parent == isolated_vault / "Logs"

        text = log_file.read_text(encoding="utf-8")
        assert "send_email" in text
        assert sample_email.sender in text
        assert "audit_log" in text

    def test_audit_log_contains_full_payload(self, isolated_vault: Path,
                                              sample_email: SimulatedEmail):
        """The audit log should embed the full JSON payload."""
        local = LocalAgent(isolated_vault)
        result = {
            "status": "success",
            "dry_run": True,
            "action": "send_email",
            "to": sample_email.sender,
            "subject": f"Re: {sample_email.subject}",
            "message_id": sample_email.message_id,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "executed_by": "local",
            "mcp_server": "gmail-mcp (simulated)",
        }
        log_file = local.log_action(result)
        text = log_file.read_text(encoding="utf-8")
        assert "```json" in text
        # Extract and parse JSON block
        json_block = text.split("```json")[1].split("```")[0].strip()
        parsed = json.loads(json_block)
        assert parsed["action"] == "send_email"


# ---------------------------------------------------------------------------
# 8. Move to /Done/
# ---------------------------------------------------------------------------
class TestMoveToDone:

    def test_move_to_done(self, isolated_vault: Path,
                           sample_email: SimulatedEmail):
        """move_to_done relocates artefacts to /Done/."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        inbox_file = cloud.detect_email(sample_email)
        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        signal = cloud.write_update_signal(sample_email, draft, approval)
        approved = local.approve_action(approval)
        local.execute_send(approved)

        files_to_move = [inbox_file, draft, approved, signal]
        done_files = local.move_to_done(files_to_move)

        assert len(done_files) == len(files_to_move)
        for f in done_files:
            assert f.parent == isolated_vault / "Done"
            assert f.exists()

    def test_source_dirs_empty_after_done(self, isolated_vault: Path,
                                           sample_email: SimulatedEmail):
        """After moving, Inbox/Plans/Approved/Updates should be empty."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        inbox = cloud.detect_email(sample_email)
        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)
        signal = cloud.write_update_signal(sample_email, draft, approval)
        approved = local.approve_action(approval)
        local.execute_send(approved)

        local.move_to_done([inbox, draft, approved, signal])

        for subdir in ["Inbox", "Plans", "Approved", "Updates"]:
            remaining = list((isolated_vault / subdir).glob("*.md"))
            assert len(remaining) == 0, f"{subdir} still has files: {remaining}"


# ---------------------------------------------------------------------------
# 9. Dashboard update
# ---------------------------------------------------------------------------
class TestDashboardUpdate:

    def test_dashboard_update(self, isolated_vault: Path):
        """update_dashboard creates and appends to Dashboard.md."""
        local = LocalAgent(isolated_vault)
        dashboard = isolated_vault / "Dashboard.md"

        local.update_dashboard("Test action completed")

        assert dashboard.exists()
        text = dashboard.read_text(encoding="utf-8")
        assert "Test action completed" in text
        assert "completed" in text
        assert "writer: local" in text

    def test_dashboard_appends(self, isolated_vault: Path):
        """Multiple calls append rows, not overwrite."""
        local = LocalAgent(isolated_vault)
        dashboard = isolated_vault / "Dashboard.md"

        local.update_dashboard("First action")
        local.update_dashboard("Second action")

        text = dashboard.read_text(encoding="utf-8")
        assert "First action" in text
        assert "Second action" in text


# ---------------------------------------------------------------------------
# 10. Full end-to-end flow
# ---------------------------------------------------------------------------
class TestFullE2EFlow:

    def test_full_e2e_flow(self, isolated_vault: Path):
        """Run the complete PlatinumDemo and assert it passes."""
        demo = PlatinumDemo(isolated_vault)
        result = demo.run_demo()
        assert result is True, "Platinum gate should PASS"

    def test_e2e_artefact_tracking(self, isolated_vault: Path):
        """After the full flow, all tracked artefacts should be set."""
        demo = PlatinumDemo(isolated_vault)
        demo.run_demo()

        assert demo.log_file is not None and demo.log_file.exists()
        assert len(demo.done_files) > 0
        assert demo.execution_result.get("status") == "success"


# ---------------------------------------------------------------------------
# 11. Claim-by-move rule
# ---------------------------------------------------------------------------
class TestClaimByMoveRule:

    def test_claim_by_move_rule(self, isolated_vault: Path,
                                 sample_email: SimulatedEmail):
        """After one agent claims via move, the source file is gone."""
        cloud = CloudAgent(isolated_vault)
        local = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)

        original_path = approval
        assert original_path.exists()

        approved = local.approve_action(approval)

        # Original gone, new location exists
        assert not original_path.exists(), "Source file must not exist after claim"
        assert approved.exists(), "Claimed file must exist in /Approved/"

    def test_double_claim_fails(self, isolated_vault: Path,
                                 sample_email: SimulatedEmail):
        """A second agent cannot claim the same file."""
        cloud = CloudAgent(isolated_vault)
        local1 = LocalAgent(isolated_vault)
        local2 = LocalAgent(isolated_vault)

        draft = cloud.draft_reply(sample_email)
        approval = cloud.create_approval_request(sample_email, draft)

        local1.approve_action(approval)

        # Second attempt should fail because the file no longer exists
        with pytest.raises((FileNotFoundError, OSError)):
            local2.approve_action(approval)


# ---------------------------------------------------------------------------
# 12. Single-writer rule
# ---------------------------------------------------------------------------
class TestSingleWriterRule:

    def test_single_writer_rule(self, isolated_vault: Path):
        """Only the Local agent should ever write Dashboard.md."""
        local = LocalAgent(isolated_vault)
        local.update_dashboard("Local writes this")

        dashboard = isolated_vault / "Dashboard.md"
        text = dashboard.read_text(encoding="utf-8")
        assert "writer: local" in text
        assert "writer: cloud" not in text

    def test_cloud_never_writes_dashboard(self, isolated_vault: Path,
                                           sample_email: SimulatedEmail):
        """CloudAgent has no method to write Dashboard.md.

        We verify the Cloud class does not have an update_dashboard method
        and that after cloud operations, Dashboard.md does not exist.
        """
        cloud = CloudAgent(isolated_vault)
        assert not hasattr(cloud, "update_dashboard"), \
            "CloudAgent must not have update_dashboard method"

        cloud.detect_email(sample_email)
        draft = cloud.draft_reply(sample_email)
        cloud.create_approval_request(sample_email, draft)

        dashboard = isolated_vault / "Dashboard.md"
        assert not dashboard.exists(), \
            "Dashboard.md should not exist after cloud-only operations"


# ---------------------------------------------------------------------------
# 13. Security -- no secrets in vault
# ---------------------------------------------------------------------------
class TestSecurityNoSecretsInVault:

    FORBIDDEN_KEYWORDS = [
        "api_key", "password", "secret_key", "access_token",
        "Bearer ", "ANTHROPIC_API_KEY", "private_key",
        "client_secret", "oauth_token",
    ]

    def test_security_no_secrets_in_vault(self, isolated_vault: Path):
        """No vault markdown file should contain credential-like strings."""
        demo = PlatinumDemo(isolated_vault)
        demo.run_demo()

        violations = []
        for md_file in isolated_vault.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            for kw in self.FORBIDDEN_KEYWORDS:
                if kw.lower() in text.lower():
                    violations.append((md_file.name, kw))

        assert len(violations) == 0, (
            f"Secrets found in vault files: {violations}"
        )

    def test_no_env_values_in_files(self, isolated_vault: Path):
        """Vault files must not contain raw .env variable values."""
        demo = PlatinumDemo(isolated_vault)
        demo.run_demo()

        for md_file in isolated_vault.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            # Common env patterns
            assert "sk-" not in text, f"Possible API key in {md_file.name}"
            assert "ghp_" not in text, f"Possible GitHub token in {md_file.name}"
            assert "xoxb-" not in text, f"Possible Slack token in {md_file.name}"
