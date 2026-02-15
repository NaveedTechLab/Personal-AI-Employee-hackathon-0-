"""
Health Check Endpoints for Personal AI Employee
===============================================

Provides health check endpoints for Kubernetes liveness/readiness probes
and monitoring systems.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psutil
import redis
from sqlalchemy import create_engine, text

from phase_3.config import DATABASE_CONFIG
from phase_4.config import REDIS_CONFIG

logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    uptime: float
    checks: Dict[str, Any]


class HealthChecker:
    def __init__(self):
        self.start_time = datetime.now()
        self.database_url = DATABASE_CONFIG["url"]
        self.redis_url = REDIS_CONFIG["url"]

        # Initialize connections
        self.redis_client = None
        self.db_engine = None

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            if not self.db_engine:
                self.db_engine = create_engine(self.database_url)

            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return {"status": "healthy", "response_time": "fast"}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis.from_url(
                    self.redis_url,
                    decode_responses=True
                )

            ping_result = self.redis_client.ping()
            return {"status": "healthy", "response_time": "fast"}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent

            status = "healthy"
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                status = "warning"
            elif cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = "unhealthy"

            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent
            }
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def check_mcp_servers(self) -> Dict[str, Any]:
        """Check MCP server availability."""
        import socket
        from phase_4.config import MCP_PORTS

        results = {}
        for service, port in MCP_PORTS.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # 5 second timeout
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    results[service] = {"status": "healthy", "port": port}
                else:
                    results[service] = {"status": "unhealthy", "port": port, "error": "connection refused"}
                sock.close()
            except Exception as e:
                results[service] = {"status": "unhealthy", "port": port, "error": str(e)}

        return results

    def get_health_status(self) -> HealthStatus:
        """Get overall health status."""
        uptime = (datetime.now() - self.start_time).total_seconds()

        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "system_resources": self.check_system_resources(),
            "mcp_servers": self.check_mcp_servers(),
        }

        # Overall status is unhealthy if any check is unhealthy
        overall_status = "healthy"
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict) and "status" in check_result:
                if check_result["status"] == "unhealthy":
                    overall_status = "unhealthy"
                    break
            elif isinstance(check_result, dict):
                # For MCP servers, check each service
                for service, service_result in check_result.items():
                    if service_result.get("status") == "unhealthy":
                        overall_status = "unhealthy"
                        break

        return HealthStatus(
            status=overall_status,
            timestamp=datetime.now(),
            uptime=uptime,
            checks=checks
        )


# Global health checker instance
health_checker = HealthChecker()


def register_health_routes(app: FastAPI):
    """Register health check routes with the FastAPI app."""

    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """Basic health check endpoint."""
        return health_checker.get_health_status()

    @app.get("/ready")
    async def readiness_check():
        """Readiness probe - indicates if the service is ready to serve traffic."""
        status = health_checker.get_health_status()
        if status.status in ["healthy", "warning"]:
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")

    @app.get("/live")
    async def liveness_check():
        """Liveness probe - indicates if the service is alive."""
        # Simple liveness check - just ensure the service is responding
        return {"status": "alive", "timestamp": datetime.now()}

    @app.get("/metrics")
    async def metrics():
        """Metrics endpoint for Prometheus."""
        import prometheus_client
        from prometheus_client import Counter, Histogram, Gauge

        # Example metrics
        requests_total = Counter('http_requests_total', 'Total HTTP requests')
        request_duration = Histogram('http_request_duration_seconds', 'Request duration')
        active_connections = Gauge('active_connections', 'Active connections')

        requests_total.inc()

        # Return metrics in Prometheus format
        return Response(prometheus_client.generate_latest(), media_type="text/plain")
