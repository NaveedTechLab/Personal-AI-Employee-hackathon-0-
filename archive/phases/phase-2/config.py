"""
Configuration file for Phase 2 - Functional Assistant (Silver Tier)

This file contains all configuration settings for the Personal AI Employee system.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = BASE_DIR / "phase-2" / "vault"
PLANS_DIR = BASE_DIR / "phase-2" / "plans"
CONFIG_DIR = BASE_DIR / "phase-2" / "config"

# Vault subdirectories
INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
DONE_DIR = VAULT_DIR / "Done"
PENDING_APPROVAL_DIR = VAULT_DIR / "Pending_Approval"
APPROVED_DIR = VAULT_DIR / "Approved"
REJECTED_DIR = VAULT_DIR / "Rejected"

# Email watcher configuration
EMAIL_WATCHER_ENABLED = True
EMAIL_POLL_INTERVAL = 60  # seconds
EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Filesystem watcher configuration
FILESYSTEM_WATCHER_ENABLED = True
WATCHED_FOLDER_PATH = os.getenv("WATCHED_FOLDER_PATH", str(BASE_DIR / "watched_folder"))
FILESYSTEM_POLL_INTERVAL = 30  # seconds

# MCP server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
MCP_SERVER_ENABLED = True

# Scheduler configuration
SCHEDULER_ENABLED = True
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "5"))

# Approval workflow configuration
AUTO_APPROVAL_ENABLED = False  # Must be False to maintain HITL
APPROVAL_REQUIRED_FOR_EXTERNAL_ACTIONS = True

# Plan generation configuration
PLAN_OUTPUT_DIR = PLANS_DIR
PLAN_TEMPLATE_PATH = CONFIG_DIR / "plan_template.md"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH = BASE_DIR / "phase-2" / "logs" / "app.log"

# Safety and security settings
ENFORCE_HITL = True  # Human-in-the-loop enforcement
PREVENT_AUTONOMOUS_LOOPS = True  # Prevent background autonomous loops