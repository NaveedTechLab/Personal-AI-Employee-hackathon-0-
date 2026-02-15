"""
Platinum Tier Configuration
===========================

Production-ready configuration for 24/7 cloud deployment.
"""

import os
from pathlib import Path
from typing import Dict, Any

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"
IS_DEVELOPMENT = ENVIRONMENT == "development"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PHASE_4_DIR = Path(__file__).parent
VAULT_DIR = Path(os.getenv("VAULT_DIR", PROJECT_ROOT / "vault"))
LOGS_DIR = Path(os.getenv("LOGS_DIR", PROJECT_ROOT / "logs"))
AUDITS_DIR = Path(os.getenv("AUDITS_DIR", PROJECT_ROOT / "audits"))
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))

# Create directories
for dir_path in [VAULT_DIR, LOGS_DIR, AUDITS_DIR, DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))

# Claude AI Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Gmail Configuration
GMAIL_CONFIG = {
    "address": os.getenv("GMAIL_ADDRESS"),
    "app_password": os.getenv("GMAIL_APP_PASSWORD"),
    "check_interval": int(os.getenv("GMAIL_CHECK_INTERVAL", "60")),
}

# Redis Configuration
REDIS_CONFIG = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
}

# PostgreSQL Configuration
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "sqlite:///./data/aiemployee.db"),
    "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
}

# MCP Server Ports
MCP_PORTS = {
    "communication": int(os.getenv("MCP_COMMUNICATION_PORT", "8000")),
    "browser": int(os.getenv("MCP_BROWSER_PORT", "8001")),
    "scheduling": int(os.getenv("MCP_SCHEDULING_PORT", "8002")),
}

# Watcher Configuration
WATCHER_CONFIG = {
    "gmail": {
        "enabled": bool(GMAIL_CONFIG["address"]),
        "poll_interval": 60,
    },
    "whatsapp": {
        "enabled": True,
        "poll_interval": 5,
        "headless": IS_PRODUCTION,
    },
    "filesystem": {
        "enabled": True,
        "watch_paths": [str(VAULT_DIR / "Inbox")],
        "poll_interval": 2,
    },
}

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    "interval_seconds": 30,
    "timeout_seconds": 10,
    "unhealthy_threshold": 3,
    "healthy_threshold": 1,
}

# Metrics Configuration
METRICS_CONFIG = {
    "enabled": True,
    "port": int(os.getenv("METRICS_PORT", "9090")),
    "path": "/metrics",
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file": str(LOGS_DIR / "platinum.log"),
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# Security Configuration
SECURITY_CONFIG = {
    "require_https": IS_PRODUCTION,
    "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
    "rate_limit_requests": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
    "rate_limit_window": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
}

# Human-in-the-Loop Configuration
HITL_CONFIG = {
    "enabled": True,
    "require_approval_for": [
        "send_email",
        "send_whatsapp",
        "financial_action",
        "external_api_call",
    ],
    "auto_approve_after_seconds": None,  # None = never auto-approve
}

# Retry Configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_delay": 1.0,
    "max_delay": 60.0,
    "exponential_base": 2,
}

# Feature Flags
FEATURES = {
    "cross_domain_reasoning": True,
    "auto_response": False,  # Requires HITL approval
    "ceo_briefings": True,
    "weekly_audits": True,
    "linkedin_integration": bool(os.getenv("LINKEDIN_ENABLED", "")),
}


def get_config() -> Dict[str, Any]:
    """Get full configuration as dictionary."""
    return {
        "environment": ENVIRONMENT,
        "is_production": IS_PRODUCTION,
        "paths": {
            "project_root": str(PROJECT_ROOT),
            "vault": str(VAULT_DIR),
            "logs": str(LOGS_DIR),
            "audits": str(AUDITS_DIR),
            "data": str(DATA_DIR),
        },
        "api": {
            "host": API_HOST,
            "port": API_PORT,
        },
        "mcp_ports": MCP_PORTS,
        "watcher": WATCHER_CONFIG,
        "health_check": HEALTH_CHECK_CONFIG,
        "metrics": METRICS_CONFIG,
        "security": SECURITY_CONFIG,
        "hitl": HITL_CONFIG,
        "features": FEATURES,
    }
