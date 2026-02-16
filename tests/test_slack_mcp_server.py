#!/usr/bin/env python3
"""Tests for Slack MCP Server skill."""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
import tempfile

SKILLS_PATH = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS_PATH / "slack-mcp-server" / "scripts"))


class TestSlackConfig:
    """Test Slack configuration."""

    def test_default_config(self):
        from config_manager import SlackMCPConfig
        config = SlackMCPConfig()
        assert config.default_channel == "#general"
        assert config.max_message_length > 0

    def test_rate_limits(self):
        from config_manager import SlackMCPConfig
        config = SlackMCPConfig()
        assert config.rate_limit_messages_per_minute > 0


class TestSlackApprovalWorkflow:
    """Test HITL approval for Slack operations."""

    def test_external_channel_requires_approval(self):
        from approval_workflow import SlackApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = SlackApprovalWorkflow(vault_path=tmpdir)
            assert workflow.requires_approval(
                action="send_message",
                channel="#external-clients",
                is_external=True
            ) is True

    def test_internal_message_no_approval(self):
        from approval_workflow import SlackApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = SlackApprovalWorkflow(vault_path=tmpdir)
            assert workflow.requires_approval(
                action="read_channel",
                channel="#general",
                is_external=False
            ) is False

    def test_file_upload_requires_approval(self):
        from approval_workflow import SlackApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = SlackApprovalWorkflow(vault_path=tmpdir)
            assert workflow.requires_approval(
                action="upload_file",
                channel="#general",
                is_external=False
            ) is True

    def test_create_approval_file(self):
        from approval_workflow import SlackApprovalWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = SlackApprovalWorkflow(vault_path=tmpdir)
            result = workflow.create_approval_request(
                action="send_message",
                details={
                    "channel": "#external",
                    "text": "Hello from AI Employee",
                    "reason": "Client outreach"
                }
            )
            assert result is not None
            approval_dir = Path(tmpdir) / "Pending_Approval"
            assert approval_dir.exists()


class TestSlackMCPServer:
    """Test MCP server creation."""

    def test_server_creation(self):
        from slack_mcp_server import create_slack_mcp_server
        server = create_slack_mcp_server()
        assert server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
