#!/usr/bin/env python3
"""Tests for A2A Agent-to-Agent Messaging skill."""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

SKILLS_PATH = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS_PATH / "a2a-messaging" / "scripts"))


class TestA2AMessageTypes:
    """Test message type definitions."""

    def test_agent_roles(self):
        from a2a_messaging import AgentRole
        assert AgentRole.CLOUD.value == "cloud"
        assert AgentRole.LOCAL.value == "local"

    def test_message_types(self):
        from a2a_messaging import MessageType
        assert MessageType.TASK_DELEGATION.value == "task_delegation"
        assert MessageType.APPROVAL_REQUEST.value == "approval_request"
        assert MessageType.APPROVAL_RESPONSE.value == "approval_response"
        assert MessageType.STATUS_UPDATE.value == "status_update"
        assert MessageType.RESULT_DELIVERY.value == "result_delivery"
        assert MessageType.HEARTBEAT.value == "heartbeat"

    def test_message_priority(self):
        from a2a_messaging import MessagePriority
        assert MessagePriority.LOW.value == "low"
        assert MessagePriority.CRITICAL.value == "critical"


class TestA2AMessage:
    """Test A2AMessage dataclass."""

    def test_create_message(self):
        from a2a_messaging import A2AMessage, AgentRole, MessageType, MessagePriority
        msg = A2AMessage(
            message_id="msg-001",
            sender=AgentRole.CLOUD,
            recipient=AgentRole.LOCAL,
            message_type=MessageType.TASK_DELEGATION,
            priority=MessagePriority.NORMAL,
            payload={"task": "Draft email reply"},
            timestamp=datetime.now()
        )
        assert msg.sender == AgentRole.CLOUD
        assert msg.recipient == AgentRole.LOCAL
        assert msg.requires_approval is False

    def test_approval_request_message(self):
        from a2a_messaging import A2AMessage, AgentRole, MessageType, MessagePriority
        msg = A2AMessage(
            message_id="msg-002",
            sender=AgentRole.CLOUD,
            recipient=AgentRole.LOCAL,
            message_type=MessageType.APPROVAL_REQUEST,
            priority=MessagePriority.HIGH,
            payload={"action": "send_email", "to": "client@example.com"},
            timestamp=datetime.now(),
            requires_approval=True
        )
        assert msg.requires_approval is True
        assert msg.message_type == MessageType.APPROVAL_REQUEST

    def test_message_ttl(self):
        from a2a_messaging import A2AMessage, AgentRole, MessageType, MessagePriority
        msg = A2AMessage(
            message_id="msg-003",
            sender=AgentRole.LOCAL,
            recipient=AgentRole.CLOUD,
            message_type=MessageType.HEARTBEAT,
            priority=MessagePriority.LOW,
            payload={},
            timestamp=datetime.now(),
            ttl_seconds=60
        )
        assert msg.ttl_seconds == 60


class TestMessageRouter:
    """Test message routing."""

    def test_file_based_routing(self):
        from message_router import FileMessageRouter
        with tempfile.TemporaryDirectory() as tmpdir:
            router = FileMessageRouter(vault_path=tmpdir)
            assert router is not None

    def test_route_to_needs_action(self):
        from message_router import FileMessageRouter
        from a2a_messaging import A2AMessage, AgentRole, MessageType, MessagePriority
        with tempfile.TemporaryDirectory() as tmpdir:
            router = FileMessageRouter(vault_path=tmpdir)
            msg = A2AMessage(
                message_id="msg-004",
                sender=AgentRole.CLOUD,
                recipient=AgentRole.LOCAL,
                message_type=MessageType.TASK_DELEGATION,
                priority=MessagePriority.NORMAL,
                payload={"task": "Review draft"},
                timestamp=datetime.now()
            )
            result = router.route_message(msg)
            assert result is True


class TestVaultSync:
    """Test vault synchronization."""

    def test_security_filter(self):
        from vault_sync import VaultSyncManager
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = VaultSyncManager(vault_path=tmpdir)
            # Should filter out sensitive files
            assert sync.should_sync(".env") is False
            assert sync.should_sync("token.json") is False
            assert sync.should_sync("Dashboard.md") is True
            assert sync.should_sync("Needs_Action/task.md") is True

    def test_no_secrets_in_sync(self):
        from vault_sync import VaultSyncManager
        with tempfile.TemporaryDirectory() as tmpdir:
            sync = VaultSyncManager(vault_path=tmpdir)
            sensitive_patterns = [".env", "credentials.json", "token.json",
                                  "whatsapp_session", "banking_creds"]
            for pattern in sensitive_patterns:
                assert sync.should_sync(pattern) is False


class TestClaimByMoveRule:
    """Test claim-by-move agent ownership."""

    def test_claim_task(self):
        from a2a_messaging import AgentRole
        from message_router import FileMessageRouter
        with tempfile.TemporaryDirectory() as tmpdir:
            router = FileMessageRouter(vault_path=tmpdir)
            # Create a task file in Needs_Action
            needs_action = Path(tmpdir) / "Needs_Action"
            needs_action.mkdir(parents=True, exist_ok=True)
            task_file = needs_action / "task_001.md"
            task_file.write_text("# Task\nDraft email reply")

            # Cloud agent claims it
            result = router.claim_task(task_file, AgentRole.CLOUD)
            assert result is True

            # Verify moved to In_Progress/cloud/
            in_progress = Path(tmpdir) / "In_Progress" / "cloud"
            assert (in_progress / "task_001.md").exists()
            assert not task_file.exists()


class TestSingleWriterRule:
    """Test single-writer rule for Dashboard.md."""

    def test_only_local_writes_dashboard(self):
        from a2a_messaging import AgentRole
        from message_router import FileMessageRouter
        with tempfile.TemporaryDirectory() as tmpdir:
            router = FileMessageRouter(vault_path=tmpdir)
            # Local should be allowed
            assert router.can_write_dashboard(AgentRole.LOCAL) is True
            # Cloud should not
            assert router.can_write_dashboard(AgentRole.CLOUD) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
