"""
Process Supervisor Integration for Personal AI Employee
=====================================================

Manages all long-running processes, auto-restarts failed processes,
and provides health monitoring for the complete system.
"""

import asyncio
import logging
import subprocess
import signal
import psutil
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import os
import sys
from pathlib import Path

import structlog
import redis
from sqlalchemy import create_engine

from phase_4.config import REDIS_CONFIG, DATABASE_CONFIG, MCP_PORTS, WATCHER_CONFIG
from phase_4.health_checks import HealthChecker
from phase_4.monitoring import monitor, start_monitoring_loop


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


class ProcessState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FATAL = "fatal"
    BACKOFF = "backoff"


@dataclass
class ProcessConfig:
    name: str
    command: str
    directory: str
    autostart: bool = True
    autorestart: bool = True
    start_retries: int = 3
    start_timeout: int = 30
    stop_timeout: int = 10
    stdout_logfile: Optional[str] = None
    stderr_logfile: Optional[str] = None
    env_vars: Dict[str, str] = None


@dataclass
class ProcessInfo:
    name: str
    pid: Optional[int]
    state: ProcessState
    start_time: Optional[datetime]
    stop_time: Optional[datetime]
    exit_code: Optional[int]
    restart_count: int
    process_obj: Optional[psutil.Process] = None


class ProcessSupervisor:
    """Manages all processes for the Personal AI Employee system."""

    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self.process_configs: Dict[str, ProcessConfig] = {}
        self.health_checker = HealthChecker()
        self.running = False

        # Initialize all process configurations
        self._setup_process_configs()

        # Redis and database for persistence
        self.redis_client = redis.Redis.from_url(REDIS_CONFIG["url"], decode_responses=True)
        self.db_engine = create_engine(DATABASE_CONFIG["url"])

    def _setup_process_configs(self):
        """Setup configurations for all system processes."""
        project_root = Path(__file__).parent.parent

        # MCP Server processes
        for service, port in MCP_PORTS.items():
            self.process_configs[f"mcp-{service}"] = ProcessConfig(
                name=f"mcp-{service}",
                command=f"python -m phase_3.mcp_servers.{service}_mcp",
                directory=str(project_root),
                autostart=True,
                autorestart=True,
                start_timeout=60,
                stdout_logfile=f"logs/mcp_{service}.log",
                stderr_logfile=f"logs/mcp_{service}_error.log"
            )

        # Watcher processes
        if WATCHER_CONFIG["gmail"]["enabled"]:
            self.process_configs["watcher-gmail"] = ProcessConfig(
                name="watcher-gmail",
                command="python -m .claude.skills.gmail-watcher.main",
                directory=str(project_root),
                autostart=True,
                autorestart=True,
                start_timeout=30,
                stdout_logfile="logs/watcher_gmail.log",
                stderr_logfile="logs/watcher_gmail_error.log"
            )

        if WATCHER_CONFIG["whatsapp"]["enabled"]:
            self.process_configs["watcher-whatsapp"] = ProcessConfig(
                name="watcher-whatsapp",
                command="python -m claude_whatsapp_integration",
                directory=str(project_root),
                autostart=True,
                autorestart=True,
                start_timeout=60,
                stdout_logfile="logs/watcher_whatsapp.log",
                stderr_logfile="logs/watcher_whatsapp_error.log"
            )

        # Filesystem watcher
        if WATCHER_CONFIG["filesystem"]["enabled"]:
            self.process_configs["watcher-filesystem"] = ProcessConfig(
                name="watcher-filesystem",
                command="python -m .claude.skills.filesystem-watcher.main",
                directory=str(project_root),
                autostart=True,
                autorestart=True,
                start_timeout=30,
                stdout_logfile="logs/watcher_filesystem.log",
                stderr_logfile="logs/watcher_filesystem_error.log"
            )

        # Monitoring process
        self.process_configs["monitoring"] = ProcessConfig(
            name="monitoring",
            command="python -c 'import asyncio; from phase_4.monitoring import start_monitoring_loop; asyncio.run(start_monitoring_loop())'",
            directory=str(project_root),
            autostart=True,
            autorestart=True,
            start_timeout=10,
            stdout_logfile="logs/monitoring.log",
            stderr_logfile="logs/monitoring_error.log"
        )

        # Orchestrator process
        self.process_configs["orchestrator"] = ProcessConfig(
            name="orchestrator",
            command="python -m .claude.skills.orchestrator-engine.main",
            directory=str(project_root),
            autostart=True,
            autorestart=True,
            start_timeout=30,
            stdout_logfile="logs/orchestrator.log",
            stderr_logfile="logs/orchestrator_error.log"
        )

    async def start_process(self, process_name: str) -> bool:
        """Start a process by name."""
        if process_name not in self.process_configs:
            logger.error("Process config not found", process_name=process_name)
            return False

        config = self.process_configs[process_name]

        if process_name in self.processes and self.processes[process_name].state in [ProcessState.RUNNING, ProcessState.STARTING]:
            logger.info("Process already running", process_name=process_name)
            return True

        try:
            logger.info("Starting process", process_name=process_name, command=config.command)

            # Create log directories
            if config.stdout_logfile:
                Path(config.stdout_logfile).parent.mkdir(parents=True, exist_ok=True)
            if config.stderr_logfile:
                Path(config.stderr_logfile).parent.mkdir(parents=True, exist_ok=True)

            # Start the process
            env = os.environ.copy()
            if config.env_vars:
                env.update(config.env_vars)

            proc = subprocess.Popen(
                config.command.split(),
                cwd=config.directory,
                stdout=open(config.stdout_logfile, 'a') if config.stdout_logfile else subprocess.PIPE,
                stderr=open(config.stderr_logfile, 'a') if config.stderr_logfile else subprocess.PIPE,
                env=env
            )

            # Create process info
            process_info = ProcessInfo(
                name=process_name,
                pid=proc.pid,
                state=ProcessState.STARTING,
                start_time=datetime.now(),
                stop_time=None,
                exit_code=None,
                restart_count=0
            )

            # Wait for process to start (simple health check)
            start_wait = 0
            while start_wait < config.start_timeout:
                if proc.poll() is not None:
                    # Process died immediately
                    process_info.state = ProcessState.FATAL
                    process_info.exit_code = proc.returncode
                    self.processes[process_name] = process_info
                    logger.error("Process failed to start", process_name=process_name, exit_code=proc.returncode)
                    return False

                # Try to get the process object to confirm it's running
                try:
                    process_obj = psutil.Process(proc.pid)
                    if process_obj.is_running():
                        process_info.state = ProcessState.RUNNING
                        process_info.process_obj = process_obj
                        self.processes[process_name] = process_info
                        logger.info("Process started successfully", process_name=process_name, pid=proc.pid)
                        return True
                except psutil.NoSuchProcess:
                    pass

                await asyncio.sleep(1)
                start_wait += 1

            # Timeout reached
            if process_info.state == ProcessState.STARTING:
                # Force kill the process
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=config.stop_timeout)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                except:
                    pass

                process_info.state = ProcessState.FATAL
                self.processes[process_name] = process_info
                logger.error("Process start timeout", process_name=process_name, timeout=config.start_timeout)
                return False

        except Exception as e:
            logger.error("Failed to start process", process_name=process_name, error=str(e))
            process_info = ProcessInfo(
                name=process_name,
                pid=None,
                state=ProcessState.FATAL,
                start_time=datetime.now(),
                stop_time=datetime.now(),
                exit_code=None,
                restart_count=0
            )
            self.processes[process_name] = process_info
            return False

        return False

    async def stop_process(self, process_name: str) -> bool:
        """Stop a process by name."""
        if process_name not in self.processes:
            logger.warn("Process not found", process_name=process_name)
            return False

        process_info = self.processes[process_name]

        if process_info.state in [ProcessState.STOPPED, ProcessState.STOPPING]:
            logger.info("Process already stopped", process_name=process_name)
            return True

        try:
            logger.info("Stopping process", process_name=process_name, pid=process_info.pid)

            process_info.state = ProcessState.STOPPING

            if process_info.process_obj:
                # Try graceful shutdown first
                process_info.process_obj.terminate()

                try:
                    process_info.process_obj.wait(timeout=process_info.config.stop_timeout)
                    process_info.state = ProcessState.STOPPED
                    process_info.stop_time = datetime.now()
                    logger.info("Process stopped gracefully", process_name=process_name)
                except psutil.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    process_info.process_obj.kill()
                    process_info.state = ProcessState.STOPPED
                    process_info.stop_time = datetime.now()
                    logger.warn("Process killed after timeout", process_name=process_name)
            else:
                # Try to find and kill the process by PID
                try:
                    proc = psutil.Process(process_info.pid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=process_info.config.stop_timeout)
                    except psutil.TimeoutExpired:
                        proc.kill()

                    process_info.state = ProcessState.STOPPED
                    process_info.stop_time = datetime.now()
                    logger.info("Process stopped", process_name=process_name)
                except psutil.NoSuchProcess:
                    process_info.state = ProcessState.STOPPED
                    process_info.stop_time = datetime.now()
                    logger.info("Process already dead", process_name=process_name)

        except Exception as e:
            logger.error("Failed to stop process", process_name=process_name, error=str(e))
            process_info.state = ProcessState.FATAL
            return False

        return True

    async def restart_process(self, process_name: str) -> bool:
        """Restart a process by name."""
        await self.stop_process(process_name)
        # Wait a bit before restarting
        await asyncio.sleep(2)
        return await self.start_process(process_name)

    async def start_all_processes(self):
        """Start all configured processes."""
        logger.info("Starting all processes")

        for process_name in self.process_configs:
            if self.process_configs[process_name].autostart:
                await self.start_process(process_name)
                # Small delay between starting processes
                await asyncio.sleep(1)

    async def stop_all_processes(self):
        """Stop all running processes."""
        logger.info("Stopping all processes")

        # Stop in reverse order (opposite of start order)
        process_names = list(reversed(list(self.processes.keys())))

        for process_name in process_names:
            await self.stop_process(process_name)
            await asyncio.sleep(1)

    async def monitor_processes(self):
        """Monitor all processes and handle failures/restarts."""
        while self.running:
            for process_name, process_info in list(self.processes.items()):
                config = self.process_configs.get(process_name)

                if not config:
                    continue

                # Check if process is still running
                if process_info.state == ProcessState.RUNNING:
                    if process_info.process_obj:
                        try:
                            if not process_info.process_obj.is_running():
                                # Process died unexpectedly
                                process_info.state = ProcessState.FATAL
                                process_info.exit_code = process_info.process_obj.returncode if hasattr(process_info.process_obj, 'returncode') else -1

                                logger.error("Process died unexpectedly", process_name=process_name, pid=process_info.pid)

                                # Handle restart logic
                                if config.autorestart and process_info.restart_count < config.start_retries:
                                    process_info.restart_count += 1
                                    logger.info("Restarting process", process_name=process_name, restart_count=process_info.restart_count)

                                    # Trigger alert for process failure
                                    from phase_4.monitoring import trigger_custom_alert, AlertSeverity
                                    trigger_custom_alert(
                                        AlertSeverity.WARNING,
                                        f"Process Restarted: {process_name}",
                                        f"Process {process_name} died and is being restarted (attempt {process_info.restart_count})",
                                        "process_supervisor",
                                        {"process_name": process_name, "restart_count": process_info.restart_count}
                                    )

                                    await self.restart_process(process_name)
                                else:
                                    logger.error("Process failed too many times, not restarting", process_name=process_name)
                                    # Alert for persistent failure
                                    from phase_4.monitoring import trigger_custom_alert, AlertSeverity
                                    trigger_custom_alert(
                                        AlertSeverity.CRITICAL,
                                        f"Process Failed: {process_name}",
                                        f"Process {process_name} failed too many times and will not be restarted",
                                        "process_supervisor",
                                        {"process_name": process_name, "final_restart_count": process_info.restart_count}
                                    )
                        except psutil.NoSuchProcess:
                            # Process disappeared
                            process_info.state = ProcessState.FATAL
                            logger.error("Process disappeared", process_name=process_name)
                    else:
                        # Process object not available, check by PID
                        try:
                            proc = psutil.Process(process_info.pid)
                            if not proc.is_running():
                                process_info.state = ProcessState.FATAL
                                logger.error("Process died (by PID)", process_name=process_name, pid=process_info.pid)
                        except psutil.NoSuchProcess:
                            process_info.state = ProcessState.FATAL
                            logger.error("Process disappeared (PID not found)", process_name=process_name, pid=process_info.pid)

            # Health check the entire system
            try:
                health_status = self.health_checker.get_health_status()
                if health_status.status == "unhealthy":
                    from phase_4.monitoring import trigger_custom_alert, AlertSeverity
                    trigger_custom_alert(
                        AlertSeverity.CRITICAL,
                        "System Health Critical",
                        f"Overall system health is {health_status.status}",
                        "health_monitor",
                        {"overall_status": health_status.status}
                    )
            except Exception as e:
                logger.error("Health check failed", error=str(e))

            await asyncio.sleep(5)  # Check every 5 seconds

    async def run(self):
        """Run the supervisor main loop."""
        logger.info("Starting process supervisor")

        self.running = True

        # Start all configured processes
        await self.start_all_processes()

        # Start monitoring loop in background
        monitoring_task = asyncio.create_task(start_monitoring_loop())
        process_monitor_task = asyncio.create_task(self.monitor_processes())

        try:
            # Wait for both tasks
            await asyncio.gather(monitoring_task, process_monitor_task)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.running = False
            await self.stop_all_processes()
            logger.info("Process supervisor stopped")

    def get_process_status(self) -> Dict[str, Dict]:
        """Get status of all processes."""
        status = {}
        for name, info in self.processes.items():
            status[name] = {
                "name": info.name,
                "pid": info.pid,
                "state": info.state.value,
                "start_time": info.start_time.isoformat() if info.start_time else None,
                "restart_count": info.restart_count,
                "exit_code": info.exit_code
            }
        return status

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        import psutil

        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "running_processes": len([p for p in self.processes.values() if p.state == ProcessState.RUNNING]),
            "total_processes": len(self.processes),
            "processes": self.get_process_status()
        }


# Global supervisor instance
supervisor = ProcessSupervisor()


def get_supervisor():
    """Get the global supervisor instance."""
    return supervisor


async def main():
    """Main entry point for the process supervisor."""
    logger.info("Personal AI Employee Process Supervisor Starting")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    try:
        await supervisor.run()
    except Exception as e:
        logger.error("Supervisor failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())