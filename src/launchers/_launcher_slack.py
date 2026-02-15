#!/usr/bin/env python3
"""Auto-generated launcher for Slack MCP"""
import sys
import os
from pathlib import Path

# Add the scripts directory to Python path for local imports
scripts_dir = r"E:\hackathon 0 qwen\Personal-AI-Employee\.claude\skills\slack-mcp-server\scripts"
sys.path.insert(0, scripts_dir)

# Also add project root
sys.path.insert(0, r"E:\hackathon 0 qwen\Personal-AI-Employee")

# Set environment
os.environ.setdefault("MCP_PORT", "8006")
os.environ.setdefault("VAULT_DIR", r"demo_vault")

# Change to scripts directory for relative file access
os.chdir(scripts_dir)

# Import and run

# Direct execution - imports work from sys.path
exec(open(os.path.join(scripts_dir, "slack_mcp_server.py"), encoding="utf-8").read())
