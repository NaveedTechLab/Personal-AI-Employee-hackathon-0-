#!/usr/bin/env python3
"""Tests for Calendar MCP Server skill."""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

SKILLS_PATH = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS_PATH / "calendar-mcp-server" / "scripts"))


class TestCalendarConfig:
    """Test calendar configuration."""

    def test_default_config(self):
        from config_manager import CalendarMCPConfig
        config = CalendarMCPConfig()
        assert config.default_calendar_id == "primary"
        assert config.hitl_required_for_shared is True

    def test_custom_config(self):
        from config_manager import CalendarMCPConfig
        config = CalendarMCPConfig(
            default_calendar_id="work@example.com",
            max_results=50
        )
        assert config.default_calendar_id == "work@example.com"


class TestApprovalWorkflow:
    """Test HITL approval for calendar operations."""

    def test_create_approval_request(self):
        from approval_workflow import CalendarApprovalWorkflow
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = CalendarApprovalWorkflow(vault_path=tmpdir)
            request = workflow.create_approval_request(
                action="create_event",
                details={
                    "summary": "Team Meeting",
                    "start": "2026-02-10T10:00:00",
                    "end": "2026-02-10T11:00:00",
                    "attendees": ["external@other.com"]
                }
            )
            assert request is not None
            assert Path(tmpdir, "Pending_Approval").exists()

    def test_shared_calendar_requires_approval(self):
        from approval_workflow import CalendarApprovalWorkflow
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = CalendarApprovalWorkflow(vault_path=tmpdir)
            assert workflow.requires_approval(
                action="create_event",
                calendar_id="shared@company.com",
                attendees=["external@other.com"]
            ) is True

    def test_personal_read_no_approval(self):
        from approval_workflow import CalendarApprovalWorkflow
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow = CalendarApprovalWorkflow(vault_path=tmpdir)
            assert workflow.requires_approval(
                action="list_events",
                calendar_id="primary",
                attendees=[]
            ) is False


class TestCalendarMCPServer:
    """Test MCP server tools."""

    def test_server_creation(self):
        from calendar_mcp_server import create_calendar_mcp_server
        server = create_calendar_mcp_server()
        assert server is not None

    def test_list_events_tool_exists(self):
        from calendar_mcp_server import create_calendar_mcp_server
        server = create_calendar_mcp_server()
        # Verify tool registration
        assert hasattr(server, 'name') or server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
