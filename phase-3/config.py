"""
Configuration file for Phase 3 - Autonomous Employee (Gold Tier)
Contains configuration settings for cross-domain reasoning, MCP servers,
audit logging, and scheduled tasks.
"""

import os
from pathlib import Path
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# ============================================
# BASE PATHS
# ============================================
BASE_DIR = Path(__file__).parent.parent
PHASE_3_DIR = Path(__file__).parent
VAULT_DIR = PHASE_3_DIR / "vault"
LOGS_DIR = PHASE_3_DIR / "logs"
AUDITS_DIR = PHASE_3_DIR / "audits"
BRIEFINGS_DIR = PHASE_3_DIR / "briefings"
EMAIL_DRAFTS_DIR = PHASE_3_DIR / "email_drafts"

# Vault subdirectories
INBOX_DIR = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR = VAULT_DIR / "Needs_Action"
DONE_DIR = VAULT_DIR / "Done"
PENDING_APPROVAL_DIR = VAULT_DIR / "Pending_Approval"
APPROVED_DIR = VAULT_DIR / "Approved"
REJECTED_DIR = VAULT_DIR / "Rejected"
PLANS_DIR = VAULT_DIR / "Plans"

# Cross-domain data paths
COMMUNICATIONS_DIR = VAULT_DIR / "Communications"
TASKS_DIR = VAULT_DIR / "Tasks"
BUSINESS_DIR = VAULT_DIR / "Business"
FINANCE_DIR = VAULT_DIR / "Finance"

# Create directories if they don't exist
def ensure_directories():
    """Create all required directories."""
    directories = [
        VAULT_DIR, LOGS_DIR, AUDITS_DIR, BRIEFINGS_DIR, EMAIL_DRAFTS_DIR,
        INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR, PENDING_APPROVAL_DIR,
        APPROVED_DIR, REJECTED_DIR, PLANS_DIR,
        COMMUNICATIONS_DIR, TASKS_DIR, BUSINESS_DIR, FINANCE_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

ensure_directories()

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email_address': os.getenv('GMAIL_ADDRESS', 'your_email@gmail.com'),
    'app_password': os.getenv('GMAIL_APP_PASSWORD', 'your_app_password_here'),
    'use_tls': True
}

# MCP Server Configuration
MCP_SERVERS = {
    'communication': {
        'url': os.getenv('COMMUNICATION_MCP_URL', 'http://localhost:8000'),
        'timeout': int(os.getenv('COMMUNICATION_MCP_TIMEOUT', '30')),
        'enabled': True
    },
    'browser': {
        'url': os.getenv('BROWSER_MCP_URL', 'http://localhost:8001'),
        'timeout': int(os.getenv('BROWSER_MCP_TIMEOUT', '60')),
        'enabled': True
    },
    'scheduling': {
        'url': os.getenv('SCHEDULING_MCP_URL', 'http://localhost:8002'),
        'timeout': int(os.getenv('SCHEDULING_MCP_TIMEOUT', '30')),
        'enabled': True
    }
}

# Cross-Domain Reasoning Configuration
CROSS_DOMAIN_PERMISSIONS = {
    'allow_personal_to_business_correlation': True,
    'allow_business_to_personal_correlation': False,
    'require_approval_for_financial_actions': True,
    'require_approval_for_communication_actions': False
}

# Audit Logging Configuration
AUDIT_LOGGING = {
    'enabled': True,
    'log_directory': './phase-3/logs',
    'retention_days': 90,
    'immutable_after_write': True
}

# Weekly Audit Schedule Configuration
WEEKLY_AUDIT_SCHEDULE = {
    'enabled': True,
    'day_of_week': 'monday',  # Run weekly audit on Mondays
    'time': '09:00',  # 9:00 AM
    'timezone': 'UTC'
}

# CEO Briefing Schedule Configuration
CEO_BRIEFING_SCHEDULE = {
    'enabled': True,
    'day_of_week': 'monday',  # Generate briefing on Monday mornings
    'time': '08:00',  # 8:00 AM
    'timezone': 'UTC'
}

# Error Handling Configuration
ERROR_HANDLING = {
    'retry_attempts': {
        'transient': 3,
        'authentication': 1,
        'logic': 0,  # No retries for logic errors
        'data': 2,
        'system': 2
    },
    'retry_delay': timedelta(seconds=5),
    'halt_on_critical_errors': True
}

# Safety and Oversight Configuration
SAFETY_OVERSIGHT = {
    'human_in_the_loop_required': True,
    'financial_action_approval_required': True,
    'permission_boundary_enforcement': True
}