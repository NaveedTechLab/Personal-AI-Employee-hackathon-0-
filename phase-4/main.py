#!/usr/bin/env python3
"""
Personal AI Employee - Platinum Tier Main Entry Point
======================================================

24/7 Cloud Deployment with:
- Health check endpoints
- Graceful shutdown handling
- Process supervision
- Multi-service orchestration
- Metrics collection
"""

import os
import sys
import signal
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "phase-3"))

# Import aiohttp for web server
try:
    from aiohttp import web
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("Warning: aiohttp not installed. Install with: pip install aiohttp")

# Import project components
try:
    from phase3.config import (
        VAULT_DIR, LOGS_DIR, AUDITS_DIR,
        MCP_SERVERS, AUDIT_LOGGING, SAFETY_OVERSIGHT
    )
except ImportError:
    # Fallback defaults
    VAULT_DIR = PROJECT_ROOT / "vault"
    LOGS_DIR = PROJECT_ROOT / "logs"
    AUDITS_DIR = PROJECT_ROOT / "audits"
    MCP_SERVERS = {}
    AUDIT_LOGGING = {"enabled": True}
    SAFETY_OVERSIGHT = {"human_in_the_loop_required": True}

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "platinum.log") if LOGS_DIR.exists() else logging.StreamHandler()
    ]
)
logger = logging.getLogger("PlatinumTier")


class ServiceStatus:
    """Track status of all services."""

    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()
        self.is_healthy = True
        self.is_shutting_down = False

    def register(self, name: str):
        """Register a service."""
        self.services[name] = {
            "status": "starting",
            "started_at": None,
            "last_heartbeat": None,
            "error": None
        }

    def set_running(self, name: str):
        """Mark service as running."""
        if name in self.services:
            self.services[name]["status"] = "running"
            self.services[name]["started_at"] = datetime.now().isoformat()
            self.services[name]["last_heartbeat"] = datetime.now().isoformat()

    def set_error(self, name: str, error: str):
        """Mark service as errored."""
        if name in self.services:
            self.services[name]["status"] = "error"
            self.services[name]["error"] = error
            self.is_healthy = False

    def heartbeat(self, name: str):
        """Update heartbeat for a service."""
        if name in self.services:
            self.services[name]["last_heartbeat"] = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Get status as dictionary."""
        return {
            "healthy": self.is_healthy and not self.is_shutting_down,
            "shutting_down": self.is_shutting_down,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "start_time": self.start_time.isoformat(),
            "services": self.services
        }


class MetricsCollector:
    """Collect and expose Prometheus metrics."""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}

    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        self.gauges[name] = value

    def observe(self, name: str, value: float):
        """Add observation to histogram."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
        # Keep only last 1000 observations
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]

    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        for name, values in self.histograms.items():
            if values:
                lines.append(f"# TYPE {name} histogram")
                lines.append(f"{name}_count {len(values)}")
                lines.append(f"{name}_sum {sum(values)}")

        return "\n".join(lines)


class PersonalAIEmployeeService:
    """Main service orchestrator for Platinum tier."""

    def __init__(self, dev_mode: bool = False):
        self.dev_mode = dev_mode
        self.status = ServiceStatus()
        self.metrics = MetricsCollector()
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.tasks: list = []

        # Register core services
        self.status.register("api_server")
        self.status.register("watcher_gmail")
        self.status.register("watcher_whatsapp")
        self.status.register("watcher_filesystem")
        self.status.register("mcp_communication")
        self.status.register("mcp_browser")
        self.status.register("mcp_scheduling")
        self.status.register("orchestrator")

        logger.info(f"Personal AI Employee Service initialized (dev_mode={dev_mode})")

    async def setup_routes(self, app: web.Application):
        """Setup HTTP routes."""
        app.router.add_get("/", self.handle_root)
        app.router.add_get("/health", self.handle_health)
        app.router.add_get("/health/live", self.handle_liveness)
        app.router.add_get("/health/ready", self.handle_readiness)
        app.router.add_get("/metrics", self.handle_metrics)
        app.router.add_get("/status", self.handle_status)
        app.router.add_post("/api/process", self.handle_process)
        app.router.add_get("/api/approvals", self.handle_get_approvals)
        app.router.add_post("/api/approvals/{id}/approve", self.handle_approve)
        app.router.add_post("/api/approvals/{id}/reject", self.handle_reject)

    async def handle_root(self, request: web.Request) -> web.Response:
        """Root endpoint."""
        return web.json_response({
            "name": "Personal AI Employee",
            "tier": "Platinum",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "metrics": "/metrics",
                "status": "/status",
                "api": "/api"
            }
        })

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        status_data = self.status.to_dict()
        http_status = 200 if status_data["healthy"] else 503
        return web.json_response(status_data, status=http_status)

    async def handle_liveness(self, request: web.Request) -> web.Response:
        """Kubernetes liveness probe."""
        if self.status.is_shutting_down:
            return web.json_response({"alive": False}, status=503)
        return web.json_response({"alive": True})

    async def handle_readiness(self, request: web.Request) -> web.Response:
        """Kubernetes readiness probe."""
        if not self.status.is_healthy or self.status.is_shutting_down:
            return web.json_response({"ready": False}, status=503)
        return web.json_response({"ready": True})

    async def handle_metrics(self, request: web.Request) -> web.Response:
        """Prometheus metrics endpoint."""
        # Update current metrics
        self.metrics.set_gauge("ai_employee_uptime_seconds",
                               (datetime.now() - self.status.start_time).total_seconds())
        self.metrics.set_gauge("ai_employee_services_total", len(self.status.services))
        self.metrics.set_gauge("ai_employee_services_healthy",
                               sum(1 for s in self.status.services.values() if s["status"] == "running"))

        return web.Response(
            text=self.metrics.to_prometheus_format(),
            content_type="text/plain"
        )

    async def handle_status(self, request: web.Request) -> web.Response:
        """Detailed status endpoint."""
        return web.json_response({
            **self.status.to_dict(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": sys.version,
            "dev_mode": self.dev_mode
        })

    async def handle_process(self, request: web.Request) -> web.Response:
        """Process an incoming event manually."""
        try:
            data = await request.json()
            self.metrics.increment("ai_employee_events_received")

            # Simulate processing
            logger.info(f"Processing event: {data.get('type', 'unknown')}")

            return web.json_response({
                "status": "processed",
                "event_id": data.get("id", "unknown"),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self.metrics.increment("ai_employee_events_failed")
            return web.json_response({"error": str(e)}, status=400)

    async def handle_get_approvals(self, request: web.Request) -> web.Response:
        """Get pending approvals."""
        pending_dir = VAULT_DIR / "Pending_Approval" if VAULT_DIR.exists() else Path("./vault/Pending_Approval")
        approvals = []

        if pending_dir.exists():
            for f in pending_dir.glob("*.md"):
                approvals.append({
                    "id": f.stem,
                    "file": f.name,
                    "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })

        return web.json_response({"approvals": approvals})

    async def handle_approve(self, request: web.Request) -> web.Response:
        """Approve an action."""
        approval_id = request.match_info["id"]
        self.metrics.increment("ai_employee_approvals_approved")
        logger.info(f"Approved: {approval_id}")
        return web.json_response({"status": "approved", "id": approval_id})

    async def handle_reject(self, request: web.Request) -> web.Response:
        """Reject an action."""
        approval_id = request.match_info["id"]
        self.metrics.increment("ai_employee_approvals_rejected")
        logger.info(f"Rejected: {approval_id}")
        return web.json_response({"status": "rejected", "id": approval_id})

    async def start_watcher_simulation(self, name: str):
        """Simulate a watcher service."""
        self.status.set_running(name)
        logger.info(f"Started watcher: {name}")

        while not self.status.is_shutting_down:
            self.status.heartbeat(name)
            self.metrics.increment(f"ai_employee_{name}_heartbeats")
            await asyncio.sleep(30)

    async def start_mcp_simulation(self, name: str, port: int):
        """Simulate an MCP server."""
        self.status.set_running(name)
        logger.info(f"Started MCP server: {name} on port {port}")

        while not self.status.is_shutting_down:
            self.status.heartbeat(name)
            await asyncio.sleep(30)

    async def start_orchestrator(self):
        """Start the main orchestrator."""
        self.status.set_running("orchestrator")
        logger.info("Orchestrator started")

        while not self.status.is_shutting_down:
            self.status.heartbeat("orchestrator")

            # Check for approved actions
            approved_dir = VAULT_DIR / "Approved" if VAULT_DIR.exists() else Path("./vault/Approved")
            if approved_dir.exists():
                for f in approved_dir.glob("*.md"):
                    logger.info(f"Processing approved action: {f.name}")
                    self.metrics.increment("ai_employee_actions_executed")
                    # Move to done (in real implementation)

            await asyncio.sleep(10)

    async def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the service."""
        if not AIOHTTP_AVAILABLE:
            logger.error("aiohttp not available, cannot start web server")
            return

        # Create web application
        self.app = web.Application()
        await self.setup_routes(self.app)

        # Start web server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, host, port)
        await site.start()

        self.status.set_running("api_server")
        logger.info(f"API server started on http://{host}:{port}")

        # Start background services
        self.tasks = [
            asyncio.create_task(self.start_watcher_simulation("watcher_gmail")),
            asyncio.create_task(self.start_watcher_simulation("watcher_whatsapp")),
            asyncio.create_task(self.start_watcher_simulation("watcher_filesystem")),
            asyncio.create_task(self.start_mcp_simulation("mcp_communication", 8000)),
            asyncio.create_task(self.start_mcp_simulation("mcp_browser", 8001)),
            asyncio.create_task(self.start_mcp_simulation("mcp_scheduling", 8002)),
            asyncio.create_task(self.start_orchestrator()),
        ]

        logger.info("All services started successfully")
        self.metrics.increment("ai_employee_starts")

        # Wait for shutdown signal
        try:
            while not self.status.is_shutting_down:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        self.status.is_shutting_down = True

        # Cancel all background tasks
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Stop web server
        if self.runner:
            await self.runner.cleanup()

        logger.info("Shutdown complete")
        self.metrics.increment("ai_employee_shutdowns")


async def main(dev_mode: bool = False):
    """Main entry point."""
    service = PersonalAIEmployeeService(dev_mode=dev_mode)

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(service.shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    print("\n" + "="*60)
    print("  PERSONAL AI EMPLOYEE - PLATINUM TIER")
    print("  24/7 Cloud Deployment Service")
    print("="*60)
    print(f"\n  Mode: {'Development' if dev_mode else 'Production'}")
    print(f"  API: http://0.0.0.0:8080")
    print(f"  Health: http://0.0.0.0:8080/health")
    print(f"  Metrics: http://0.0.0.0:8080/metrics")
    print("\n  Press Ctrl+C to stop")
    print("="*60 + "\n")

    try:
        await service.start()
    except KeyboardInterrupt:
        await service.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Personal AI Employee - Platinum Tier")
    parser.add_argument("--dev", action="store_true", help="Run in development mode")
    parser.add_argument("--port", type=int, default=8080, help="API port (default: 8080)")
    args = parser.parse_args()

    asyncio.run(main(dev_mode=args.dev))
