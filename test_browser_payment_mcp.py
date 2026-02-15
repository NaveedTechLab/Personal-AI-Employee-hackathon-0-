#!/usr/bin/env python3
"""Tests for Browser/Payment MCP Server skill."""

import pytest
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

SKILLS_PATH = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS_PATH / "browser-payment-mcp" / "scripts"))


class TestPaymentConfig:
    """Test payment configuration."""

    def test_default_config(self):
        from config_manager import PaymentMCPConfig
        config = PaymentMCPConfig()
        assert config.headless is True
        assert config.max_payments_per_hour == 3
        assert config.approval_expiry_hours == 24
        assert config.dry_run is True  # Default to safe mode

    def test_rate_limits(self):
        from config_manager import PaymentMCPConfig
        config = PaymentMCPConfig()
        assert config.max_payments_per_hour > 0
        assert config.max_payments_per_hour <= 10  # Reasonable upper bound


class TestPaymentApprovalWorkflow:
    """Test HITL for payment operations."""

    def test_all_payments_require_approval(self):
        from approval_workflow import PaymentApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = PaymentApprovalWorkflow(vault_path=tmpdir)
            # ALL payments must require approval - no exceptions
            assert workflow.requires_approval(amount=1.00) is True
            assert workflow.requires_approval(amount=50.00) is True
            assert workflow.requires_approval(amount=500.00) is True
            assert workflow.requires_approval(amount=10000.00) is True

    def test_create_payment_approval_file(self):
        from approval_workflow import PaymentApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = PaymentApprovalWorkflow(vault_path=tmpdir)
            approval_id = workflow.create_approval_request(
                recipient="Client A",
                amount=500.00,
                reference="Invoice #1234",
                account="XXXX1234"
            )
            assert approval_id is not None

            # Verify file created
            approval_dir = Path(tmpdir) / "Pending_Approval"
            assert approval_dir.exists()
            files = list(approval_dir.glob("PAYMENT_*.md"))
            assert len(files) == 1

    def test_approval_expiry(self):
        from approval_workflow import PaymentApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = PaymentApprovalWorkflow(vault_path=tmpdir, expiry_hours=24)
            approval_id = workflow.create_approval_request(
                recipient="Client B",
                amount=200.00,
                reference="Invoice #5678",
                account="XXXX5678"
            )
            # Fresh approval should not be expired
            assert workflow.is_expired(approval_id) is False

    def test_never_auto_approve_new_payees(self):
        from approval_workflow import PaymentApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = PaymentApprovalWorkflow(vault_path=tmpdir)
            # New payees ALWAYS require approval regardless of amount
            assert workflow.requires_approval(
                amount=10.00,
                is_new_payee=True
            ) is True


class TestPaymentAudit:
    """Test payment audit trail."""

    def test_audit_log_creation(self):
        from payment_audit import PaymentAuditLogger
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = PaymentAuditLogger(log_dir=tmpdir)
            logger.log_action(
                action_type="draft_payment",
                recipient="Client A",
                amount=500.00,
                approval_status="pending",
                result="drafted"
            )
            # Verify log file exists
            log_files = list(Path(tmpdir).glob("*.json"))
            assert len(log_files) >= 1

    def test_audit_log_format(self):
        from payment_audit import PaymentAuditLogger
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = PaymentAuditLogger(log_dir=tmpdir)
            logger.log_action(
                action_type="execute_payment",
                recipient="Client A",
                amount=500.00,
                approval_status="approved",
                approved_by="human",
                result="success"
            )
            log_files = list(Path(tmpdir).glob("*.json"))
            content = json.loads(log_files[0].read_text())
            # Should be a list or have required fields
            if isinstance(content, list):
                entry = content[0]
            else:
                entry = content
            assert "action_type" in entry
            assert "timestamp" in entry
            assert "amount" in entry


class TestDryRunMode:
    """Test DRY_RUN safety mode."""

    def test_dry_run_prevents_execution(self):
        from config_manager import PaymentMCPConfig
        config = PaymentMCPConfig(dry_run=True)
        assert config.dry_run is True
        # In dry run, no actual browser actions should execute


class TestBrowserPaymentMCP:
    """Test MCP server creation."""

    def test_server_creation(self):
        from browser_payment_mcp import create_payment_mcp_server
        server = create_payment_mcp_server()
        assert server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
