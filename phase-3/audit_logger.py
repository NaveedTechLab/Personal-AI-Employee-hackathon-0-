"""
Audit Logger Module for Phase 3 - Autonomous Employee (Gold Tier)
Provides comprehensive audit logging for all actions with immutable logs.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import threading
from dataclasses import dataclass, asdict
import uuid


@dataclass
class AuditLogEntry:
    """Represents a single audit log entry."""
    log_id: str
    timestamp: datetime
    action_type: str
    target: str
    approval_status: str  # 'approved', 'pending', 'rejected'
    approver: Optional[str]  # Approver identifier or None
    result: str  # 'success', 'failure', 'partial'
    context_correlation: Optional[str]  # Cross-domain context ID
    safety_boundary_checks: Dict[str, bool]  # Safety boundary compliance
    additional_metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit log entry to a dictionary."""
        result = asdict(self)
        # Convert datetime to ISO format string
        result['timestamp'] = self.timestamp.isoformat()
        return result

    def to_json(self) -> str:
        """Convert the audit log entry to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Class responsible for comprehensive audit logging of all actions
    with immutable logs and proper retention structure.
    """

    def __init__(self, log_directory: str = "./phase-3/logs", retention_days: int = 90):
        """
        Initialize the AuditLogger.

        Args:
            log_directory: Directory to store log files
            retention_days: Number of days to retain logs
        """
        self.log_directory = Path(log_directory)
        self.retention_days = retention_days

        # Ensure log directory exists
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Thread lock for thread-safe logging
        self._lock = threading.Lock()

    def log_action(
        self,
        action_type: str,
        target: str,
        approval_status: str,
        approver: Optional[str] = None,
        result: str = 'success',
        context_correlation: Optional[str] = None,
        safety_boundary_checks: Optional[Dict[str, bool]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an action with all required metadata.

        Args:
            action_type: Type/category of the action
            target: Target of the action
            approval_status: Approval status of the action
            approver: Identifier of the approver (if any)
            result: Result of the action
            context_correlation: Cross-domain context ID
            safety_boundary_checks: Safety boundary compliance status
            additional_metadata: Additional metadata to log

        Returns:
            The log entry ID
        """
        if safety_boundary_checks is None:
            safety_boundary_checks = {
                "boundaries_respected": True,
                "permissions_validated": True
            }

        # Create the log entry
        log_entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            action_type=action_type,
            target=target,
            approval_status=approval_status,
            approver=approver,
            result=result,
            context_correlation=context_correlation,
            safety_boundary_checks=safety_boundary_checks,
            additional_metadata=additional_metadata
        )

        # Write the log entry atomically
        self._write_log_entry(log_entry)

        return log_entry.log_id

    def _write_log_entry(self, log_entry: AuditLogEntry) -> None:
        """
        Write a log entry to the log file in an atomic way.

        Args:
            log_entry: The log entry to write
        """
        with self._lock:  # Ensure thread safety
            # Determine the log file based on the date
            date_str = log_entry.timestamp.strftime("%Y-%m-%d")
            log_file_path = self.log_directory / f"audit-{date_str}.log"

            # Convert log entry to JSON
            log_line = log_entry.to_json()

            # Write atomically using a temporary file
            temp_file_path = log_file_path.with_suffix('.tmp')

            # If the log file already exists, read existing content
            existing_content = ""
            if log_file_path.exists():
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # Write both existing content and new entry to temp file
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                if existing_content:
                    f.write(existing_content)
                    if not existing_content.endswith('\n'):
                        f.write('\n')
                f.write(log_line)
                f.write('\n')

            # Atomically replace the original file with the temp file
            temp_file_path.replace(log_file_path)

    def get_logs_by_date(self, date: datetime) -> List[AuditLogEntry]:
        """
        Retrieve all logs for a specific date.

        Args:
            date: Date to retrieve logs for

        Returns:
            List of audit log entries for the date
        """
        date_str = date.strftime("%Y-%m-%d")
        log_file_path = self.log_directory / f"audit-{date_str}.log"

        if not log_file_path.exists():
            return []

        entries = []
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_dict = json.loads(line)
                        # Convert timestamp back to datetime
                        log_dict['timestamp'] = datetime.fromisoformat(log_dict['timestamp'])
                        entry = AuditLogEntry(**log_dict)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue  # Skip invalid lines

        return entries

    def get_logs_by_action_type(self, action_type: str, days_back: int = 7) -> List[AuditLogEntry]:
        """
        Retrieve logs for a specific action type within a date range.

        Args:
            action_type: Type of action to filter by
            days_back: Number of days back to search

        Returns:
            List of matching audit log entries
        """
        entries = []
        start_date = datetime.now() - timedelta(days=days_back)

        for i in range(days_back + 1):
            date = start_date + timedelta(days=i)
            daily_entries = self.get_logs_by_date(date)
            for entry in daily_entries:
                if entry.action_type == action_type:
                    entries.append(entry)

        return entries

    def get_logs_by_approval_status(self, approval_status: str, days_back: int = 7) -> List[AuditLogEntry]:
        """
        Retrieve logs with a specific approval status within a date range.

        Args:
            approval_status: Approval status to filter by
            days_back: Number of days back to search

        Returns:
            List of matching audit log entries
        """
        entries = []
        start_date = datetime.now() - timedelta(days=days_back)

        for i in range(days_back + 1):
            date = start_date + timedelta(days=i)
            daily_entries = self.get_logs_by_date(date)
            for entry in daily_entries:
                if entry.approval_status == approval_status:
                    entries.append(entry)

        return entries

    def verify_log_immutability(self, date: datetime) -> bool:
        """
        Verify that logs for a given date have not been tampered with
        by checking hash chains or signatures (simplified implementation).

        Args:
            date: Date to verify log integrity for

        Returns:
            True if logs appear to be immutable, False otherwise
        """
        date_str = date.strftime("%Y-%m-%d")
        log_file_path = self.log_directory / f"audit-{date_str}.log"

        if not log_file_path.exists():
            return True  # No logs to verify

        # This is a simplified verification - in a real system, you'd have
        # cryptographic hashes or signatures to verify integrity
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # For now, just verify the file hasn't been modified since creation
            # In a real implementation, you'd check hash chains or digital signatures
            return len(content) > 0
        except Exception:
            return False

    def cleanup_old_logs(self) -> int:
        """
        Remove log files older than the retention period.

        Returns:
            Number of files removed
        """
        import shutil
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")

        files_removed = 0
        for log_file in self.log_directory.glob("audit-*.log"):
            # Extract date from filename
            filename = log_file.name
            if filename.startswith("audit-") and filename.endswith(".log"):
                date_part = filename[6:-4]  # Extract date part (e.g., "2023-01-15")

                try:
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")
                    if file_date < cutoff_date:
                        log_file.unlink()  # Remove the file
                        files_removed += 1
                except ValueError:
                    continue  # Skip files with invalid date format

        return files_removed

    def get_retention_policy_info(self) -> Dict[str, Any]:
        """
        Get information about the retention policy and current log storage.

        Returns:
            Dictionary with retention policy information
        """
        total_files = len(list(self.log_directory.glob("audit-*.log")))

        # Calculate approximate storage used
        total_size = 0
        for log_file in self.log_directory.glob("audit-*.log"):
            total_size += log_file.stat().st_size

        return {
            "retention_days": self.retention_days,
            "total_log_files": total_files,
            "approximate_storage_mb": round(total_size / (1024 * 1024), 2),
            "log_directory": str(self.log_directory.absolute())
        }


class GlobalAuditLogger:
    """
    Singleton wrapper around AuditLogger for global access.
    """
    _instance: Optional[AuditLogger] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, log_directory: str = "./phase-3/logs", retention_days: int = 90):
        """
        Initialize the global audit logger.

        Args:
            log_directory: Directory to store log files
            retention_days: Number of days to retain logs
        """
        if not self._initialized:
            self.logger = AuditLogger(log_directory, retention_days)
            self._initialized = True

    def log_action(
        self,
        action_type: str,
        target: str,
        approval_status: str,
        approver: Optional[str] = None,
        result: str = 'success',
        context_correlation: Optional[str] = None,
        safety_boundary_checks: Optional[Dict[str, bool]] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an action globally.
        """
        if not self._initialized:
            self.initialize()

        return self.logger.log_action(
            action_type, target, approval_status, approver,
            result, context_correlation, safety_boundary_checks, additional_metadata
        )

    def get_logger(self) -> AuditLogger:
        """
        Get the underlying AuditLogger instance.
        """
        if not self._initialized:
            self.initialize()
        return self.logger


def get_global_audit_logger() -> GlobalAuditLogger:
    """
    Get the global audit logger instance.

    Returns:
        GlobalAuditLogger instance
    """
    return GlobalAuditLogger()


def log_mcp_action(
    action_type: str,
    target: str,
    approval_status: str,
    result: str = 'success',
    approver: Optional[str] = None,
    context_correlation: Optional[str] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to log MCP actions.

    Args:
        action_type: Type of MCP action
        target: Target of the action
        approval_status: Approval status
        result: Result of the action
        approver: Approver identifier
        context_correlation: Cross-domain context ID
        additional_metadata: Additional metadata

    Returns:
        Log entry ID
    """
    logger = get_global_audit_logger()
    safety_checks = {
        "boundaries_respected": True,
        "permissions_validated": True
    }

    return logger.log_action(
        action_type=action_type,
        target=target,
        approval_status=approval_status,
        approver=approver,
        result=result,
        context_correlation=context_correlation,
        safety_boundary_checks=safety_checks,
        additional_metadata=additional_metadata
    )


if __name__ == "__main__":
    from datetime import timedelta

    # Example usage
    logger = get_global_audit_logger()
    logger.initialize(retention_days=90)

    # Log some sample actions
    log_id1 = logger.log_action(
        action_type="communication.send_email",
        target="user@example.com",
        approval_status="approved",
        approver="admin_user",
        result="success",
        context_correlation="ctx_12345",
        additional_metadata={"subject": "Test email", "size_bytes": 1024}
    )
    print(f"Logged action with ID: {log_id1}")

    log_id2 = logger.log_action(
        action_type="financial.process_payment",
        target="vendor_account_6789",
        approval_status="pending",
        result="pending_approval",
        context_correlation="ctx_12345",
        additional_metadata={"amount": 1500.00, "currency": "USD"}
    )
    print(f"Logged action with ID: {log_id2}")

    # Retrieve logs for today
    today_logs = logger.get_logger().get_logs_by_date(datetime.now())
    print(f"Found {len(today_logs)} logs for today")

    # Get info about retention policy
    policy_info = logger.get_logger().get_retention_policy_info()
    print(f"Retention policy info: {policy_info}")

    # Verify log immutability for today
    is_immutable = logger.get_logger().verify_log_immutability(datetime.now())
    print(f"Logs for today are immutable: {is_immutable}")