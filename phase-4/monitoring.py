"""
Monitoring and Alerting System for Personal AI Employee
=======================================================

Production monitoring, metrics collection, and alerting infrastructure.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client.exposition import generate_latest
import redis
from sqlalchemy import create_engine, text
import requests

from phase_4.config import REDIS_CONFIG, DATABASE_CONFIG


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Alert:
    id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]


@dataclass
class MetricDefinition:
    name: str
    type: MetricType
    description: str
    labels: List[str]


class MetricsCollector:
    """Collects and exports application metrics."""

    def __init__(self):
        self.metrics = {}
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize Prometheus metrics."""
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )

        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'Request duration',
            ['method', 'endpoint']
        )

        # Business metrics
        self.events_processed = Counter(
            'events_processed_total',
            'Total events processed',
            ['source', 'type']
        )

        self.responses_generated = Counter(
            'responses_generated_total',
            'Total responses generated',
            ['source', 'type']
        )

        # System metrics
        self.active_watchers = Gauge(
            'active_watchers',
            'Number of active watchers'
        )

        self.mcp_servers_up = Gauge(
            'mcp_servers_up',
            'Number of MCP servers currently up',
            ['service']
        )

        # Database metrics
        self.db_queries = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'table']
        )

        self.db_errors = Counter(
            'db_errors_total',
            'Database errors',
            ['operation', 'table']
        )

        # Redis metrics
        self.redis_operations = Counter(
            'redis_operations_total',
            'Redis operations',
            ['operation', 'key']
        )

        self.redis_errors = Counter(
            'redis_errors_total',
            'Redis errors',
            ['operation', 'key']
        )

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        self.request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_event_processed(self, source: str, event_type: str):
        """Record event processing metrics."""
        self.events_processed.labels(source=source, type=event_type).inc()

    def record_response_generated(self, source: str, response_type: str):
        """Record response generation metrics."""
        self.responses_generated.labels(source=source, type=response_type).inc()

    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format."""
        return generate_latest()


class AlertManager:
    """Manages alert generation, routing, and notification."""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.severity_thresholds = {
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.ERROR: 3,
            AlertSeverity.CRITICAL: 4
        }
        self.alert_handlers = []

    def add_alert_handler(self, handler_func):
        """Add a function to handle alerts."""
        self.alert_handlers.append(handler_func)

    def trigger_alert(self, severity: AlertSeverity, title: str, description: str, source: str, metadata: Dict[str, Any] = None):
        """Trigger an alert."""
        alert_id = f"alert_{datetime.now().timestamp()}_{hash(title)}"
        metadata = metadata or {}

        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.now(),
            source=source,
            metadata=metadata
        )

        self.alerts.append(alert)
        logger.warn("Alert triggered", alert_id=alert.id, severity=severity.value, title=title, source=source)

        # Call all registered handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler failed", handler=str(handler), error=str(e))

    def get_recent_alerts(self, hours: int = 1) -> List[Alert]:
        """Get alerts from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp >= cutoff_time]

    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alert counts by severity."""
        summary = {severity.value: 0 for severity in AlertSeverity}
        for alert in self.alerts:
            summary[alert.severity.value] += 1
        return summary


class EmailNotifier:
    """Handles email notifications for alerts."""

    def __init__(self):
        import os
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("NOTIFICATION_EMAIL_FROM", "alerts@ai-employee.local")
        self.to_emails = os.getenv("NOTIFICATION_EMAIL_TO", "").split(",")

    def send_alert_email(self, alert: Alert):
        """Send an alert via email."""
        if not self.to_emails or not self.smtp_user:
            logger.warn("Email notification skipped - no recipients or SMTP configured")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            body = f"""
Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Source: {alert.source}
Time: {alert.timestamp.isoformat()}
Description: {alert.description}

Metadata: {json.dumps(alert.metadata, indent=2, default=str)}

This is an automated alert from Personal AI Employee monitoring system.
            """

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("Alert email sent", alert_id=alert.id, recipients=len(self.to_emails))
        except Exception as e:
            logger.error("Failed to send alert email", error=str(e))


class SlackNotifier:
    """Handles Slack notifications for alerts."""

    def __init__(self):
        import os
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

    def send_alert_slack(self, alert: Alert):
        """Send an alert to Slack."""
        if not self.webhook_url:
            logger.warn("Slack notification skipped - no webhook URL configured")
            return

        try:
            color_map = {
                AlertSeverity.INFO: "#36a64f",  # Green
                AlertSeverity.WARNING: "#ffcc00",  # Yellow
                AlertSeverity.ERROR: "#e74c3c",  # Red
                AlertSeverity.CRITICAL: "#8b0000"  # Dark Red
            }

            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, "#36a64f"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Source",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.isoformat(),
                            "short": True
                        }
                    ],
                    "footer": "Personal AI Employee Monitoring",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info("Alert sent to Slack", alert_id=alert.id)
            else:
                logger.error("Failed to send Slack alert", status_code=response.status_code, response=response.text)
        except Exception as e:
            logger.error("Failed to send Slack alert", error=str(e))


class SystemMonitor:
    """Main system monitoring class."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.email_notifier = EmailNotifier()
        self.slack_notifier = SlackNotifier()

        # Register alert handlers
        self.alert_manager.add_alert_handler(self.email_notifier.send_alert_email)
        self.alert_manager.add_alert_handler(self.slack_notifier.send_alert_slack)

        # Database and Redis connections
        self.db_engine = create_engine(DATABASE_CONFIG["url"])
        self.redis_client = redis.Redis.from_url(REDIS_CONFIG["url"], decode_responses=True)

    def check_system_health(self):
        """Perform comprehensive system health check."""
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        # CPU alert
        if cpu_percent > 90:
            self.alert_manager.trigger_alert(
                AlertSeverity.WARNING,
                "High CPU Usage",
                f"CPU usage is {cpu_percent}% which is above threshold",
                "system_monitor",
                {"cpu_percent": cpu_percent}
            )
        elif cpu_percent > 95:
            self.alert_manager.trigger_alert(
                AlertSeverity.CRITICAL,
                "Critical CPU Usage",
                f"CPU usage is critically high at {cpu_percent}%",
                "system_monitor",
                {"cpu_percent": cpu_percent}
            )

        # Memory alert
        if memory_percent > 85:
            self.alert_manager.trigger_alert(
                AlertSeverity.WARNING,
                "High Memory Usage",
                f"Memory usage is {memory_percent}% which is above threshold",
                "system_monitor",
                {"memory_percent": memory_percent}
            )
        elif memory_percent > 95:
            self.alert_manager.trigger_alert(
                AlertSeverity.CRITICAL,
                "Critical Memory Usage",
                f"Memory usage is critically high at {memory_percent}%",
                "system_monitor",
                {"memory_percent": memory_percent}
            )

        # Disk alert
        if disk_percent > 80:
            self.alert_manager.trigger_alert(
                AlertSeverity.WARNING,
                "High Disk Usage",
                f"Disk usage is {disk_percent}% which is above threshold",
                "system_monitor",
                {"disk_percent": disk_percent}
            )
        elif disk_percent > 90:
            self.alert_manager.trigger_alert(
                AlertSeverity.CRITICAL,
                "Critical Disk Usage",
                f"Disk usage is critically high at {disk_percent}%",
                "system_monitor",
                {"disk_percent": disk_percent}
            )

    def check_database_health(self):
        """Check database health."""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))

            # Check connection pool metrics
            pool_size = self.db_engine.pool.size()
            pool_overflow = self.db_engine.pool.overflow()

            if pool_overflow > 5:  # More than 5 connections over pool size
                self.alert_manager.trigger_alert(
                    AlertSeverity.WARNING,
                    "Database Pool Overflow",
                    f"Database pool has {pool_overflow} overflow connections",
                    "database_monitor",
                    {"pool_size": pool_size, "overflow": pool_overflow}
                )
        except Exception as e:
            self.alert_manager.trigger_alert(
                AlertSeverity.CRITICAL,
                "Database Connection Failed",
                f"Unable to connect to database: {str(e)}",
                "database_monitor",
                {"error": str(e)}
            )

    def check_redis_health(self):
        """Check Redis health."""
        try:
            # Ping Redis
            ping_result = self.redis_client.ping()

            # Check Redis info
            info = self.redis_client.info()
            connected_clients = info.get('connected_clients', 0)
            used_memory = info.get('used_memory_human', 'unknown')

            if connected_clients > 100:  # High number of connections
                self.alert_manager.trigger_alert(
                    AlertSeverity.WARNING,
                    "High Redis Connections",
                    f"Redis has {connected_clients} connected clients",
                    "redis_monitor",
                    {"connected_clients": connected_clients}
                )

        except Exception as e:
            self.alert_manager.trigger_alert(
                AlertSeverity.CRITICAL,
                "Redis Connection Failed",
                f"Unable to connect to Redis: {str(e)}",
                "redis_monitor",
                {"error": str(e)}
            )

    def collect_business_metrics(self):
        """Collect business-level metrics."""
        # Example: Count events processed in last hour
        try:
            # This would typically query your event logs/database
            # For now, we'll simulate with system metrics
            pass
        except Exception as e:
            logger.error("Failed to collect business metrics", error=str(e))

    async def run_monitoring_cycle(self):
        """Run a complete monitoring cycle."""
        logger.info("Starting monitoring cycle")

        # Run all checks
        self.check_system_health()
        self.check_database_health()
        self.check_redis_health()
        self.collect_business_metrics()

        logger.info("Monitoring cycle completed")

    def get_alert_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard-ready alert data."""
        recent_alerts = self.alert_manager.get_recent_alerts(hours=24)
        alert_summary = self.alert_manager.get_alert_summary()

        return {
            "timestamp": datetime.now().isoformat(),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "source": alert.source,
                    "timestamp": alert.timestamp.isoformat(),
                    "description": alert.description
                }
                for alert in recent_alerts[-10:]  # Last 10 alerts
            ],
            "alert_summary": alert_summary,
            "total_alerts": len(recent_alerts)
        }


# Global monitor instance
monitor = SystemMonitor()


async def start_monitoring_loop(interval_seconds: int = 60):
    """Start the continuous monitoring loop."""
    logger.info("Starting monitoring loop", interval_seconds=interval_seconds)

    while True:
        try:
            await monitor.run_monitoring_cycle()
            await asyncio.sleep(interval_seconds)
        except Exception as e:
            logger.error("Monitoring loop error", error=str(e))
            await asyncio.sleep(10)  # Brief pause before retrying


# Convenience functions for other parts of the application
def record_event_processed(source: str, event_type: str):
    """Convenience function to record event processing."""
    monitor.metrics_collector.record_event_processed(source, event_type)


def record_response_generated(source: str, response_type: str):
    """Convenience function to record response generation."""
    monitor.metrics_collector.record_response_generated(source, response_type)


def trigger_custom_alert(severity: AlertSeverity, title: str, description: str, source: str, metadata: Dict[str, Any] = None):
    """Convenience function to trigger custom alerts."""
    monitor.alert_manager.trigger_alert(severity, title, description, source, metadata)


def get_current_metrics():
    """Get current metrics export."""
    return monitor.metrics_collector.get_metrics()


def get_alert_dashboard_data():
    """Get current alert dashboard data."""
    return monitor.get_alert_dashboard_data()