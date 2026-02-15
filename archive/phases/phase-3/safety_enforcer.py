"""
Safety Enforcer Module for Phase 3 - Autonomous Employee (Gold Tier)
Enforces safety and oversight mechanisms to maintain human accountability.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
import logging
from functools import wraps


class SafetyBoundary(Enum):
    """Enumeration of different safety boundaries."""
    FINANCIAL_EXECUTION = "financial_execution"
    COMMUNICATION_SEND = "communication_send"
    SYSTEM_MODIFICATION = "system_modification"
    DATA_ACCESS = "data_access"
    HUMAN_PRIVILEGE_ESCALATION = "human_privilege_escalation"


class OversightLevel(Enum):
    """Enumeration of different oversight levels."""
    AUTOMATED = "automated"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    PROHIBITED = "prohibited"


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    allowed: bool
    reason: str
    required_approver: Optional[str] = None
    escalation_needed: bool = False


@dataclass
class SafetyPolicy:
    """Definition of a safety policy."""
    boundary: SafetyBoundary
    oversight_level: OversightLevel
    description: str
    exception_conditions: List[str]
    escalation_contact: Optional[str] = None


class SafetyEnforcer:
    """
    Class responsible for enforcing safety and oversight mechanisms
    to maintain human accountability in the autonomous system.
    """

    def __init__(self):
        """Initialize the SafetyEnforcer."""
        self.policies: Dict[SafetyBoundary, SafetyPolicy] = {}
        self.human_override_tokens: Dict[str, datetime] = {}
        self.approved_actions: Dict[str, datetime] = {}
        self.escalation_queue: List[Dict[str, Any]] = []

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Initialize default policies
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default safety policies."""
        default_policies = [
            SafetyPolicy(
                boundary=SafetyBoundary.FINANCIAL_EXECUTION,
                oversight_level=OversightLevel.HUMAN_APPROVAL_REQUIRED,
                description="All financial executions require explicit human approval",
                exception_conditions=["emergency_funds_transfer"],
                escalation_contact="finance_team"
            ),
            SafetyPolicy(
                boundary=SafetyBoundary.COMMUNICATION_SEND,
                oversight_level=OversightLevel.AUTOMATED,
                description="Sending routine communications is allowed automatically",
                exception_conditions=["external_communication_with_financial_info"],
                escalation_contact="comms_team"
            ),
            SafetyPolicy(
                boundary=SafetyBoundary.SYSTEM_MODIFICATION,
                oversight_level=OversightLevel.HUMAN_IN_THE_LOOP,
                description="System modifications require human oversight",
                exception_conditions=["scheduled_maintenance_window"],
                escalation_contact="sysadmin_team"
            ),
            SafetyPolicy(
                boundary=SafetyBoundary.DATA_ACCESS,
                oversight_level=OversightLevel.AUTOMATED,
                description="Accessing non-sensitive data is allowed automatically",
                exception_conditions=["access_sensitive_customer_data"],
                escalation_contact="security_team"
            ),
            SafetyPolicy(
                boundary=SafetyBoundary.HUMAN_PRIVILEGE_ESCALATION,
                oversight_level=OversightLevel.PROHIBITED,
                description="Privilege escalation is prohibited",
                exception_conditions=["emergency_situation_with_token"],
                escalation_contact="security_admin"
            )
        ]

        for policy in default_policies:
            self.policies[policy.boundary] = policy

    def register_policy(self, policy: SafetyPolicy):
        """
        Register a new safety policy.

        Args:
            policy: The safety policy to register
        """
        self.policies[policy.boundary] = policy
        self.logger.info(f"Registered safety policy for boundary: {policy.boundary.value}")

    def check_action_allowed(self, boundary: SafetyBoundary, action_details: Dict[str, Any] = None) -> SafetyCheckResult:
        """
        Check if an action is allowed based on safety policies.

        Args:
            boundary: The safety boundary to check
            action_details: Additional details about the action

        Returns:
            SafetyCheckResult indicating whether the action is allowed
        """
        if boundary not in self.policies:
            self.logger.warning(f"No policy found for boundary: {boundary.value}")
            return SafetyCheckResult(
                allowed=False,
                reason=f"No safety policy defined for boundary: {boundary.value}"
            )

        policy = self.policies[boundary]

        # Check if this is an exception condition
        if action_details and "exception" in action_details:
            if action_details["exception"] in policy.exception_conditions:
                # For exception conditions, check if there's a valid override token
                if "override_token" in action_details:
                    token = action_details["override_token"]
                    if self._validate_override_token(token):
                        return SafetyCheckResult(
                            allowed=True,
                            reason=f"Action allowed due to valid exception: {action_details['exception']}"
                        )

        # Apply oversight level based on policy
        if policy.oversight_level == OversightLevel.AUTOMATED:
            return SafetyCheckResult(
                allowed=True,
                reason="Action allowed automatically based on policy"
            )
        elif policy.oversight_level == OversightLevel.HUMAN_APPROVAL_REQUIRED:
            # Check if action is already approved
            if action_details and "action_id" in action_details:
                action_id = action_details["action_id"]
                if action_id in self.approved_actions:
                    approval_time = self.approved_actions[action_id]
                    # Check if approval is still valid (e.g., within 1 hour)
                    if datetime.now() - approval_time < timedelta(hours=1):
                        return SafetyCheckResult(
                            allowed=True,
                            reason="Action allowed based on recent human approval"
                        )

            return SafetyCheckResult(
                allowed=False,
                reason="Action requires human approval",
                required_approver=policy.escalation_contact
            )
        elif policy.oversight_level == OversightLevel.HUMAN_IN_THE_LOOP:
            return SafetyCheckResult(
                allowed=False,
                reason="Action requires human in the loop oversight",
                required_approver=policy.escalation_contact,
                escalation_needed=True
            )
        elif policy.oversight_level == OversightLevel.PROHIBITED:
            return SafetyCheckResult(
                allowed=False,
                reason="Action is prohibited by safety policy",
                escalation_needed=True
            )

        # Default case - shouldn't reach here
        return SafetyCheckResult(
            allowed=False,
            reason="Unknown oversight level"
        )

    def request_human_approval(self, boundary: SafetyBoundary, action_details: Dict[str, Any]) -> str:
        """
        Request human approval for an action that requires it.

        Args:
            boundary: The safety boundary for the action
            action_details: Details about the action needing approval

        Returns:
            Approval token if approved, empty string if denied
        """
        policy = self.policies.get(boundary)
        if not policy:
            self.logger.error(f"No policy found for boundary: {boundary.value}")
            return ""

        self.logger.info(f"Requesting human approval for {boundary.value} action")

        # In a real system, this would send a notification to the appropriate human
        # For this implementation, we'll simulate the approval process

        # Add to escalation queue for tracking
        approval_request = {
            "boundary": boundary.value,
            "action_details": action_details,
            "requested_at": datetime.now(),
            "contact": policy.escalation_contact
        }
        self.escalation_queue.append(approval_request)

        # Return an empty string to indicate approval is pending
        # In a real system, this would return a token after human approval
        return ""

    def record_human_approval(self, action_id: str) -> bool:
        """
        Record that a human has approved a specific action.

        Args:
            action_id: ID of the action that was approved

        Returns:
            True if approval was recorded, False otherwise
        """
        self.approved_actions[action_id] = datetime.now()
        self.logger.info(f"Recorded human approval for action: {action_id}")
        return True

    def _validate_override_token(self, token: str) -> bool:
        """
        Validate an override token for exception conditions.

        Args:
            token: The override token to validate

        Returns:
            True if token is valid, False otherwise
        """
        if token in self.human_override_tokens:
            token_time = self.human_override_tokens[token]
            # Check if token is still valid (e.g., within 10 minutes)
            if datetime.now() - token_time < timedelta(minutes=10):
                return True
            else:
                # Token expired, remove it
                del self.human_override_tokens[token]

        return False

    def generate_override_token(self, reason: str = "") -> str:
        """
        Generate an override token for emergency situations.

        Args:
            reason: Reason for generating the override token

        Returns:
            Override token string
        """
        import uuid
        token = str(uuid.uuid4())
        self.human_override_tokens[token] = datetime.now()

        self.logger.warning(f"Generated override token for reason: {reason}")
        return token

    def enforce_boundary(self, boundary: SafetyBoundary, action_func: Callable, *args, **kwargs) -> Any:
        """
        Decorator-like method to enforce a safety boundary on an action.

        Args:
            boundary: The safety boundary to enforce
            action_func: The function to execute if allowed
            *args: Arguments to pass to the action function
            **kwargs: Keyword arguments to pass to the action function

        Returns:
            Result of the action function if allowed, raises exception otherwise
        """
        check_result = self.check_action_allowed(boundary, kwargs.get('action_details', {}))

        if not check_result.allowed:
            if check_result.escalation_needed:
                # Add to escalation queue
                escalation = {
                    "boundary": boundary.value,
                    "action_args": args,
                    "action_kwargs": kwargs,
                    "reason": check_result.reason,
                    "at": datetime.now()
                }
                self.escalation_queue.append(escalation)

                raise PermissionError(f"Action blocked by safety boundary '{boundary.value}'. Reason: {check_result.reason}")
            else:
                raise PermissionError(f"Action requires approval: {check_result.reason}")

        # Action is allowed, execute it
        try:
            result = action_func(*args, **kwargs)
            self.logger.info(f"Successfully executed action for boundary: {boundary.value}")
            return result
        except Exception as e:
            self.logger.error(f"Error executing action for boundary {boundary.value}: {str(e)}")
            raise

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get all pending approval requests.

        Returns:
            List of pending approval requests
        """
        return [req for req in self.escalation_queue if 'action_details' in req]

    def get_pending_escalations(self) -> List[Dict[str, Any]]:
        """
        Get all pending escalations that require human attention.

        Returns:
            List of pending escalations
        """
        return [esc for esc in self.escalation_queue if 'action_args' in esc]

    def validate_safety_compliance(self, action_type: str, target: str) -> Dict[str, bool]:
        """
        Validate that an action complies with safety boundaries.

        Args:
            action_type: Type of action to validate
            target: Target of the action

        Returns:
            Dictionary with compliance status
        """
        # Map action types to safety boundaries
        boundary_map = {
            "financial": SafetyBoundary.FINANCIAL_EXECUTION,
            "communication": SafetyBoundary.COMMUNICATION_SEND,
            "system": SafetyBoundary.SYSTEM_MODIFICATION,
            "data": SafetyBoundary.DATA_ACCESS,
        }

        # Determine the appropriate boundary based on action type
        boundary = None
        for key, value in boundary_map.items():
            if key in action_type.lower():
                boundary = value
                break

        if boundary is None:
            # Default to a conservative boundary
            boundary = SafetyBoundary.SYSTEM_MODIFICATION

        check_result = self.check_action_allowed(boundary)
        return {
            "boundaries_respected": check_result.allowed,
            "permissions_validated": True,
            "requires_approval": not check_result.allowed and check_result.required_approver is not None
        }

    def shutdown(self):
        """Perform cleanup operations before shutdown."""
        self.logger.info("SafetyEnforcer shutting down")
        # Clear any temporary tokens or approvals if needed
        self.human_override_tokens.clear()
        self.approved_actions.clear()


def get_safety_enforcer_instance() -> SafetyEnforcer:
    """
    Factory function to get a SafetyEnforcer instance.

    Returns:
        SafetyEnforcer instance
    """
    return SafetyEnforcer()


def safety_boundary(boundary: SafetyBoundary):
    """
    Decorator to enforce a safety boundary on a function.

    Args:
        boundary: The safety boundary to enforce
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            enforcer = get_safety_enforcer_instance()
            return enforcer.enforce_boundary(boundary, func, *args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage
    enforcer = get_safety_enforcer_instance()

    # Test financial action (should require approval)
    try:
        result = enforcer.check_action_allowed(SafetyBoundary.FINANCIAL_EXECUTION)
        print(f"Financial action allowed: {result.allowed}, reason: {result.reason}")
    except Exception as e:
        print(f"Financial action blocked: {e}")

    # Test communication action (should be allowed automatically)
    result = enforcer.check_action_allowed(SafetyBoundary.COMMUNICATION_SEND)
    print(f"Communication action allowed: {result.allowed}, reason: {result.reason}")

    # Test with action details
    action_details = {
        "action_id": "act_12345",
        "amount": 1500.00,
        "recipient": "vendor"
    }

    # This would normally require approval
    result = enforcer.check_action_allowed(SafetyBoundary.FINANCIAL_EXECUTION, action_details)
    print(f"Financial action with details allowed: {result.allowed}, reason: {result.reason}")

    # Generate an override token for emergency
    token = enforcer.generate_override_token("Emergency fund transfer required")
    print(f"Generated override token: {token}")

    # Test with override token
    action_with_exception = {
        "exception": "emergency_funds_transfer",
        "override_token": token
    }
    result = enforcer.check_action_allowed(SafetyBoundary.FINANCIAL_EXECUTION, action_with_exception)
    print(f"Emergency financial action allowed: {result.allowed}, reason: {result.reason}")

    # Validate safety compliance
    compliance = enforcer.validate_safety_compliance("financial.payment", "account_6789")
    print(f"Safety compliance: {compliance}")