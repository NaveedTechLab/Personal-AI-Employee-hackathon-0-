"""
Cross-Domain Context Model for Phase 3 - Autonomous Employee (Gold Tier)
Defines the entity structure for cross-domain contexts that span multiple domains.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class ContextStatus(Enum):
    """Enumeration of possible context statuses."""
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class DomainType(Enum):
    """Enumeration of different domain types."""
    COMMUNICATIONS = "communications"
    TASKS = "tasks"
    BUSINESS_GOALS = "business_goals"
    FINANCIAL_LOGS = "financial_logs"
    PERSONAL_INFO = "personal_info"


class CrossDomainContext:
    """
    Entity representing a context that spans multiple domains.
    This class serves as a model for cross-domain reasoning contexts.
    """

    def __init__(
        self,
        domains_involved: List[DomainType],
        correlation_signals: List[str],
        summary: str = "",
        approval_required: bool = False,
        approval_status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a cross-domain context.

        Args:
            domains_involved: List of domains involved in this context
            correlation_signals: List of correlation signal IDs
            summary: Summary description of the context
            approval_required: Whether this context requires approval
            approval_status: Current approval status
            metadata: Additional metadata for the context
        """
        self.id = f"ctx_{str(uuid.uuid4())[:8]}"
        self.domains_involved = domains_involved
        self.correlation_signals = correlation_signals
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.summary = summary
        self.approval_required = approval_required
        self.approval_status = approval_status
        self.status = ContextStatus.ACTIVE
        self.metadata = metadata or {}
        self.related_contexts: List[str] = []  # IDs of related contexts
        self.action_history: List[Dict[str, Any]] = []

    def add_action_to_history(self, action_type: str, details: Dict[str, Any], result: str = "success"):
        """
        Add an action to the context's history.

        Args:
            action_type: Type of action performed
            details: Details about the action
            result: Result of the action
        """
        action_record = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "details": details,
            "result": result
        }
        self.action_history.append(action_record)
        self.updated_at = datetime.now()

    def update_status(self, new_status: ContextStatus):
        """
        Update the context status.

        Args:
            new_status: New status for the context
        """
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        # Add status change to action history
        self.add_action_to_history(
            action_type="status_change",
            details={
                "old_status": old_status.value,
                "new_status": new_status.value
            },
            result="success"
        )

    def add_related_context(self, context_id: str):
        """
        Add a reference to a related context.

        Args:
            context_id: ID of the related context
        """
        if context_id not in self.related_contexts:
            self.related_contexts.append(context_id)
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary representation.

        Returns:
            Dictionary representation of the context
        """
        return {
            "id": self.id,
            "domains_involved": [domain.value for domain in self.domains_involved],
            "correlation_signals": self.correlation_signals,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "summary": self.summary,
            "approval_required": self.approval_required,
            "approval_status": self.approval_status,
            "status": self.status.value,
            "metadata": self.metadata,
            "related_contexts": self.related_contexts,
            "action_history": self.action_history
        }

    def from_dict(cls, data: Dict[str, Any]):
        """
        Create a CrossDomainContext from a dictionary.

        Args:
            data: Dictionary containing context data

        Returns:
            CrossDomainContext instance
        """
        # Import here to avoid circular imports
        from typing import get_type_hints

        # Create a new instance without calling __init__
        instance = cls.__new__(cls)

        # Set attributes from the data dictionary
        instance.id = data["id"]
        instance.domains_involved = [DomainType(domain) for domain in data["domains_involved"]]
        instance.correlation_signals = data["correlation_signals"]
        instance.created_at = datetime.fromisoformat(data["created_at"])
        instance.updated_at = datetime.fromisoformat(data["updated_at"])
        instance.summary = data.get("summary", "")
        instance.approval_required = data.get("approval_required", False)
        instance.approval_status = data.get("approval_status", "pending")
        instance.status = ContextStatus(data.get("status", "active"))
        instance.metadata = data.get("metadata", {})
        instance.related_contexts = data.get("related_contexts", [])
        instance.action_history = data.get("action_history", [])

        return instance

    def requires_approval(self) -> bool:
        """
        Check if this context requires approval.

        Returns:
            True if approval is required, False otherwise
        """
        # Approval required if explicitly set or if financial domain is involved
        return (self.approval_required or
                DomainType.FINANCIAL_LOGS in self.domains_involved)

    def is_complete(self) -> bool:
        """
        Check if this context is complete.

        Returns:
            True if context is complete, False otherwise
        """
        return self.status == ContextStatus.COMPLETED

    def validate_for_approval(self) -> List[str]:
        """
        Validate the context before requesting approval.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check if required fields are present
        if not self.domains_involved:
            errors.append("At least one domain must be involved")

        if not self.correlation_signals:
            errors.append("At least one correlation signal is required")

        if not self.summary:
            errors.append("Summary is required")

        # Check if approval is required but status is not pending
        if self.requires_approval() and self.approval_status != "pending":
            errors.append(f"Approval status should be 'pending' when approval is required, got '{self.approval_status}'")

        return errors

    def get_domain_summary(self) -> Dict[str, int]:
        """
        Get a summary of domains involved in this context.

        Returns:
            Dictionary mapping domain types to their counts
        """
        summary = {}
        for domain in self.domains_involved:
            domain_name = domain.value
            summary[domain_name] = summary.get(domain_name, 0) + 1
        return summary


def create_cross_domain_context(
    domains: List[DomainType],
    signals: List[str],
    summary: str = "",
    approval_required: bool = False,
    approval_status: str = "pending",
    metadata: Optional[Dict[str, Any]] = None
) -> CrossDomainContext:
    """
    Factory function to create a cross-domain context.

    Args:
        domains: List of domains involved
        signals: List of correlation signal IDs
        summary: Summary description
        approval_required: Whether approval is required
        approval_status: Current approval status
        metadata: Additional metadata

    Returns:
        CrossDomainContext instance
    """
    return CrossDomainContext(
        domains_involved=domains,
        correlation_signals=signals,
        summary=summary,
        approval_required=approval_required,
        approval_status=approval_status,
        metadata=metadata
    )


if __name__ == "__main__":
    # Example usage
    from datetime import timedelta

    # Create a cross-domain context
    context = create_cross_domain_context(
        domains=[DomainType.COMMUNICATIONS, DomainType.FINANCIAL_LOGS, DomainType.TASKS],
        signals=["signal_1", "signal_2", "signal_3"],
        summary="Budget review involving communications with finance team and financial data analysis",
        approval_required=True,
        metadata={"priority": "high", "department": "finance"}
    )

    print(f"Created context with ID: {context.id}")
    print(f"Domains involved: {[d.value for d in context.domains_involved]}")
    print(f"Requires approval: {context.requires_approval()}")
    print(f"Summary: {context.summary}")

    # Add an action to history
    context.add_action_to_history(
        action_type="data_analysis",
        details={"tool_used": "cross_domain_reasoner", "result": "positive_correlation_found"},
        result="success"
    )

    # Update status
    context.update_status(ContextStatus.ACTIVE)

    # Print context dictionary
    context_dict = context.to_dict()
    print(f"Context dictionary keys: {list(context_dict.keys())}")
    print(f"Action history: {len(context.action_history)} actions")

    # Validate for approval
    validation_errors = context.validate_for_approval()
    print(f"Validation errors: {validation_errors}")