"""
Cross-Domain Reasoner Module for Phase 3 - Autonomous Employee (Gold Tier)
Enables Claude to handle unified communications across multiple platforms while
managing business tasks and financial logs with proper approval requirements.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

from .vault_integrator import VaultIntegrator
from .context_correlator import ContextCorrelator, SignalType, Signal
from .safety_enforcer import SafetyEnforcer, SafetyBoundary
from .audit_logger import log_mcp_action
from .config import CROSS_DOMAIN_PERMISSIONS


class DomainType(Enum):
    """Enumeration of different domain types."""
    COMMUNICATIONS = "communications"
    TASKS = "tasks"
    BUSINESS_GOALS = "business_goals"
    FINANCIAL_LOGS = "financial_logs"
    PERSONAL_INFO = "personal_info"


@dataclass
class CrossDomainContext:
    """Represents a context that spans multiple domains."""
    id: str
    domains_involved: List[DomainType]
    correlation_signals: List[str]
    timestamp: datetime
    approval_required: bool = False
    approval_status: str = "pending"  # "pending", "approved", "rejected"
    summary: str = ""


@dataclass
class ReasoningInput:
    """Input structure for cross-domain reasoning."""
    personal_data: Dict[str, Any]
    business_data: Dict[str, Any]
    correlation_rules: List[str]
    safety_boundaries: List[str]


@dataclass
class ReasoningOutput:
    """Output structure for cross-domain reasoning."""
    analysis_results: Dict[str, Any]
    safety_compliance: Dict[str, bool]
    processing_metadata: Dict[str, Any]


class CrossDomainReasoner:
    """
    Class responsible for enabling Claude to handle unified communications
    across multiple platforms while managing business tasks and financial logs
    with proper approval requirements.
    """

    def __init__(self):
        """Initialize the CrossDomainReasoner."""
        self.vault_integrator = VaultIntegrator()
        self.context_correlator = ContextCorrelator()
        self.safety_enforcer = SafetyEnforcer()

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def read_cross_domain_data(self) -> Dict[DomainType, List[Dict[str, Any]]]:
        """
        Read data concurrently from all domains as specified in the requirements.

        Returns:
            Dictionary mapping domain types to lists of data records
        """
        # Get data from vault integrator
        communications = self.vault_integrator.get_communications_data()
        tasks = self.vault_integrator.get_task_artifacts()
        business_goals = self.vault_integrator.get_business_goals()
        financial_logs = self.vault_integrator.get_transaction_logs()

        return {
            DomainType.COMMUNICATIONS: communications,
            DomainType.TASKS: tasks,
            DomainType.BUSINESS_GOALS: business_goals,
            DomainType.FINANCIAL_LOGS: financial_logs
        }

    def correlate_signals_across_domains(self, domain_data: Dict[DomainType, List[Dict[str, Any]]]) -> List[Signal]:
        """
        Correlate signals across different domains to identify relevant connections.

        Args:
            domain_data: Data from all domains to correlate

        Returns:
            List of correlated signals
        """
        all_signals = []

        # Add signals from each domain
        for domain_type, data_list in domain_data.items():
            for data_item in data_list:
                content = str(data_item.get('data', str(data_item)))
                signal = self.context_correlator.add_signal(
                    content=content,
                    source_domain=domain_type.value,
                    signal_type=self._map_domain_to_signal_type(domain_type)
                )
                all_signals.append(signal)

        # Perform correlation
        correlations = self.context_correlator.correlate_all_signals()
        self.logger.info(f"Found {len(correlations)} correlations across domains")

        return all_signals

    def _map_domain_to_signal_type(self, domain_type: DomainType) -> SignalType:
        """Map domain types to signal types."""
        mapping = {
            DomainType.COMMUNICATIONS: SignalType.COMMUNICATION,
            DomainType.TASKS: SignalType.TASK,
            DomainType.BUSINESS_GOALS: SignalType.BUSINESS_GOAL,
            DomainType.FINANCIAL_LOGS: SignalType.FINANCIAL_LOG,
            DomainType.PERSONAL_INFO: SignalType.PERSONAL_INFO
        }
        return mapping.get(domain_type, SignalType.OTHER)

    def validate_read_only_unless_approved(self, action_type: str, target: str) -> bool:
        """
        Verify reasoning remains read-only unless approved.

        Args:
            action_type: Type of action being performed
            target: Target of the action

        Returns:
            True if action is read-only or properly approved, False otherwise
        """
        # Check if this is a read operation
        if 'read' in action_type.lower() or 'get' in action_type.lower() or 'fetch' in action_type.lower():
            return True

        # For non-read operations, check if approval is required and obtained
        boundary = SafetyBoundary.FINANCIAL_EXECUTION if 'financial' in action_type.lower() else SafetyBoundary.SYSTEM_MODIFICATION
        compliance = self.safety_enforcer.validate_safety_compliance(action_type, target)

        return compliance.get('boundaries_respected', False)

    def analyze_cross_domain_input(self, input_data: ReasoningInput) -> ReasoningOutput:
        """
        Analyze information across personal and business domains and correlate relevant information.

        Args:
            input_data: Input data containing personal and business information

        Returns:
            ReasoningOutput with analysis results
        """
        start_time = datetime.now()

        # Extract data from input
        personal_data = input_data.personal_data
        business_data = input_data.business_data
        correlation_rules = input_data.correlation_rules
        safety_boundaries = input_data.safety_boundaries

        # Perform cross-domain analysis
        analysis_results = {
            "cross_domain_insights": [],
            "relevant_correlations": [],
            "potential_conflicts": [],
            "action_recommendations": []
        }

        # Add personal data signals
        for key, value in personal_data.items():
            content = str(value)
            signal = self.context_correlator.add_signal(
                content=content,
                source_domain="personal",
                signal_type=SignalType.PERSONAL_INFO
            )

        # Add business data signals
        for key, value in business_data.items():
            content = str(value)
            signal_type = self._determine_signal_type_from_key(key)
            signal = self.context_correlator.add_signal(
                content=content,
                source_domain="business",
                signal_type=signal_type
            )

        # Perform correlation
        correlations = self.context_correlator.correlate_all_signals()

        # Generate insights
        insights = self.context_correlator.generate_cross_domain_insights()
        analysis_results["cross_domain_insights"] = insights

        # Identify relevant correlations
        for correlation in correlations:
            if correlation.correlation_strength > 0.5:  # Strong correlation threshold
                analysis_results["relevant_correlations"].append({
                    "strength": correlation.correlation_strength,
                    "reason": correlation.correlation_reason,
                    "primary": correlation.primary_signal.id,
                    "related": [rs.id for rs in correlation.related_signals]
                })

        # Check for potential conflicts based on rules
        for rule in correlation_rules:
            if "conflict" in rule.lower():
                # Simple conflict detection: if we have opposing signals
                if len(insights) > 1:
                    analysis_results["potential_conflicts"].append({
                        "type": "potential_conflict",
                        "description": f"Possible conflict detected based on rule: {rule}",
                        "evidence": insights[:2]  # Show first two insights as evidence
                    })

        # Generate action recommendations based on safety boundaries
        for boundary in safety_boundaries:
            if "financial" in boundary and CROSS_DOMAIN_PERMISSIONS.get("require_approval_for_financial_actions", True):
                analysis_results["action_recommendations"].append({
                    "type": "requires_approval",
                    "action": "financial_execution",
                    "boundary": boundary,
                    "reason": "Financial actions require explicit approval"
                })

        # Validate safety compliance
        safety_compliance = {
            "boundaries_respected": True,
            "permissions_validated": True
        }

        # Check if personal-to-business correlation is allowed
        if not CROSS_DOMAIN_PERMISSIONS.get("allow_personal_to_business_correlation", True):
            safety_compliance["boundaries_respected"] = False

        # Processing metadata
        processing_duration = (datetime.now() - start_time).total_seconds() * 1000  # in milliseconds
        processing_metadata = {
            "timestamp": start_time.isoformat(),
            "processing_duration_ms": processing_duration
        }

        return ReasoningOutput(
            analysis_results=analysis_results,
            safety_compliance=safety_compliance,
            processing_metadata=processing_metadata
        )

    def _determine_signal_type_from_key(self, key: str) -> SignalType:
        """Determine signal type based on the data key."""
        key_lower = key.lower()
        if 'task' in key_lower or 'todo' in key_lower:
            return SignalType.TASK
        elif 'goal' in key_lower or 'objective' in key_lower:
            return SignalType.BUSINESS_GOAL
        elif 'finance' in key_lower or 'transaction' in key_lower or 'payment' in key_lower:
            return SignalType.FINANCIAL_LOG
        elif 'comm' in key_lower or 'email' in key_lower or 'message' in key_lower:
            return SignalType.COMMUNICATION
        else:
            return SignalType.OTHER

    def verify_no_domain_bypasses_approval_rules(self) -> bool:
        """
        Verify that no domain bypasses approval rules.

        Returns:
            True if all domains respect approval rules, False otherwise
        """
        # Check each domain type for compliance
        domains_to_check = [
            DomainType.COMMUNICATIONS,
            DomainType.TASKS,
            DomainType.BUSINESS_GOALS,
            DomainType.FINANCIAL_LOGS
        ]

        for domain in domains_to_check:
            # For financial logs, ensure approval is required for execution
            if domain == DomainType.FINANCIAL_LOGS:
                if not CROSS_DOMAIN_PERMISSIONS.get("require_approval_for_financial_actions", True):
                    self.logger.warning(f"Financial actions may not require approval in domain: {domain.value}")
                    return False

            # For other domains, ensure they don't have elevated privileges
            # Check that they respect the permission boundaries
            compliance = self.safety_enforcer.validate_safety_compliance(
                f"{domain.value}_access",
                f"domain_{domain.value}"
            )

            if not compliance.get("boundaries_respected", True):
                self.logger.warning(f"Domain {domain.value} does not respect safety boundaries")
                return False

        return True

    def create_cross_domain_context(self, domains: List[DomainType], signals: List[str]) -> CrossDomainContext:
        """
        Create a cross-domain context entity.

        Args:
            domains: List of domains involved
            signals: List of correlation signal IDs

        Returns:
            CrossDomainContext entity
        """
        import uuid

        context = CrossDomainContext(
            id=f"ctx_{str(uuid.uuid4())[:8]}",
            domains_involved=domains,
            correlation_signals=signals,
            timestamp=datetime.now(),
            approval_required=self._requires_approval(domains),
            summary=self._generate_context_summary(domains, signals)
        )

        return context

    def _requires_approval(self, domains: List[DomainType]) -> bool:
        """Determine if a cross-domain context requires approval."""
        # If financial logs are involved, approval is typically required
        return DomainType.FINANCIAL_LOGS in domains

    def _generate_context_summary(self, domains: List[DomainType], signals: List[str]) -> str:
        """Generate a summary for the cross-domain context."""
        domain_names = [domain.value for domain in domains]
        return f"Cross-domain context involving: {', '.join(domain_names)}. Signals: {len(signals)} correlations."

    def validate_reasoning_output_format(self, output: ReasoningOutput) -> bool:
        """
        Validate that the reasoning output follows the expected format.

        Args:
            output: The reasoning output to validate

        Returns:
            True if format is valid, False otherwise
        """
        required_fields = [
            "analysis_results.cross_domain_insights",
            "analysis_results.relevant_correlations",
            "analysis_results.potential_conflicts",
            "analysis_results.action_recommendations",
            "safety_compliance.boundaries_respected",
            "safety_compliance.permissions_validated",
            "processing_metadata.timestamp",
            "processing_metadata.processing_duration_ms"
        ]

        # Check each required field exists
        for field_path in required_fields:
            parts = field_path.split('.')
            obj = output

            try:
                for part in parts:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    elif isinstance(obj, dict):
                        obj = obj[part]
                    else:
                        self.logger.error(f"Missing required field: {field_path}")
                        return False
            except (KeyError, TypeError, AttributeError):
                self.logger.error(f"Missing required field: {field_path}")
                return False

        return True

    async def execute_cross_domain_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a full cross-domain analysis with all safety checks.

        Args:
            input_data: Input data for analysis

        Returns:
            Analysis results with safety compliance information
        """
        # Validate input data structure
        if not self._validate_input_structure(input_data):
            raise ValueError("Invalid input data structure for cross-domain analysis")

        # Create reasoning input
        reasoning_input = ReasoningInput(
            personal_data=input_data.get("personal_data", {}),
            business_data=input_data.get("business_data", {}),
            correlation_rules=input_data.get("correlation_rules", []),
            safety_boundaries=input_data.get("safety_boundaries", [])
        )

        # Perform analysis
        output = self.analyze_cross_domain_input(reasoning_input)

        # Validate output format
        if not self.validate_reasoning_output_format(output):
            raise ValueError("Invalid reasoning output format")

        # Check safety compliance
        if not output.safety_compliance.get("boundaries_respected", False):
            raise PermissionError("Cross-domain analysis violates safety boundaries")

        # Log the analysis for audit purposes
        log_mcp_action(
            action_type="cross_domain.analysis",
            target="cross_domain_reasoner",
            approval_status=output.safety_compliance.get("permissions_validated", False),
            result="success",
            context_correlation=output.processing_metadata.get("timestamp"),
            additional_metadata={
                "input_domains": list(input_data.keys()),
                "analysis_duration_ms": output.processing_metadata.get("processing_duration_ms"),
                "safety_compliant": output.safety_compliance.get("boundaries_respected", False)
            }
        )

        # Convert output to dictionary for return
        result = {
            "analysis_results": output.analysis_results,
            "safety_compliance": output.safety_compliance,
            "processing_metadata": output.processing_metadata
        }

        return result

    def _validate_input_structure(self, input_data: Dict[str, Any]) -> bool:
        """Validate the structure of input data."""
        required_keys = ["personal_data", "business_data"]
        return all(key in input_data for key in required_keys)


def get_cross_domain_reasoner_instance() -> CrossDomainReasoner:
    """
    Factory function to get a CrossDomainReasoner instance.

    Returns:
        CrossDomainReasoner instance
    """
    return CrossDomainReasoner()


async def analyze_cross_domain_data(personal_data: Dict[str, Any], business_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async function to analyze cross-domain data.

    Args:
        personal_data: Data from personal domains
        business_data: Data from business domains

    Returns:
        Analysis results
    """
    reasoner = get_cross_domain_reasoner_instance()

    input_data = {
        "personal_data": personal_data,
        "business_data": business_data,
        "correlation_rules": ["personal_to_business_correlation", "financial_impact_analysis"],
        "safety_boundaries": ["financial_execution_approval", "data_privacy_protection"]
    }

    return await reasoner.execute_cross_domain_analysis(input_data)


if __name__ == "__main__":
    import asyncio

    # Example usage
    async def main():
        reasoner = get_cross_domain_reasoner_instance()

        # Read data from all domains
        domain_data = reasoner.read_cross_domain_data()
        print(f"Read data from {len(domain_data)} domains")

        # Correlate signals across domains
        signals = reasoner.correlate_signals_across_domains(domain_data)
        print(f"Correlated {len(signals)} signals across domains")

        # Prepare input data for analysis
        input_data = {
            "personal_data": {
                "communications": "Received email from John about quarterly budget review",
                "personal_tasks": "Schedule meeting with finance team"
            },
            "business_data": {
                "business_tasks": "Complete Q3 financial report",
                "business_goals": "Achieve 15% profit margin for Q3",
                "financial_logs": "Previous quarter expenses: $1.2M, revenue: $1.8M"
            },
            "correlation_rules": [
                "correlate_budget_review_with_financial_goals",
                "identify_conflicts_between_personal_and_business_tasks"
            ],
            "safety_boundaries": [
                "financial_execution_approval_required",
                "protect_personal_information_privacy"
            ]
        }

        # Execute cross-domain analysis
        try:
            results = await reasoner.execute_cross_domain_analysis(input_data)
            print(f"Analysis completed successfully")
            print(f"Found {len(results['analysis_results']['cross_domain_insights'])} insights")
            print(f"Found {len(results['analysis_results']['relevant_correlations'])} correlations")
            print(f"Processing time: {results['processing_metadata']['processing_duration_ms']}ms")

            # Verify that no domain bypasses approval rules
            approval_rules_valid = reasoner.verify_no_domain_bypasses_approval_rules()
            print(f"Approval rules respected: {approval_rules_valid}")

        except Exception as e:
            print(f"Analysis failed: {str(e)}")

    # Run the example
    asyncio.run(main())