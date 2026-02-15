"""
Context Correlator Module for Phase 3 - Autonomous Employee (Gold Tier)
Responsible for correlating signals across different domains to enable
cross-domain reasoning capabilities.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import hashlib
from enum import Enum


class SignalType(Enum):
    """Enumeration of different signal types for cross-domain correlation."""
    COMMUNICATION = "communication"
    TASK = "task"
    BUSINESS_GOAL = "business_goal"
    FINANCIAL_LOG = "financial_log"
    PERSONAL_INFO = "personal_info"
    OTHER = "other"


@dataclass
class Signal:
    """Represents a signal from any domain with associated metadata."""
    id: str
    content: str
    source_domain: str
    signal_type: SignalType
    timestamp: datetime
    relevance_score: float = 1.0
    tags: List[str] = None
    correlation_ids: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.correlation_ids is None:
            self.correlation_ids = []


@dataclass
class CorrelationResult:
    """Represents the result of a correlation operation."""
    primary_signal: Signal
    related_signals: List[Signal]
    correlation_strength: float
    correlation_reason: str
    timestamp: datetime


class ContextCorrelator:
    """
    Class responsible for correlating signals across different domains
    to enable cross-domain reasoning capabilities.
    """

    def __init__(self):
        """Initialize the ContextCorrelator."""
        self.signals: List[Signal] = []
        self.correlations: List[CorrelationResult] = []
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for identifying different types of correlations."""
        return {
            'email_pattern': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone_pattern': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'date_pattern': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            'currency_pattern': re.compile(r'\$\d+(?:,\d{3})*(?:\.\d{2})?'),
            'project_pattern': re.compile(r'#\w+|\b[A-Z]{2,}-\d+\b'),  # Hashtags or JIRA-style identifiers
            'person_pattern': re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),  # Names
            'location_pattern': re.compile(r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b'),  # City, ST
        }

    def add_signal(self, content: str, source_domain: str, signal_type: SignalType) -> Signal:
        """
        Add a new signal to the correlator.

        Args:
            content: The content of the signal
            source_domain: The domain the signal originates from
            signal_type: The type of signal

        Returns:
            The created Signal object
        """
        signal_id = hashlib.md5(f"{content}{source_domain}{signal_type.value}{datetime.now()}".encode()).hexdigest()[:12]

        signal = Signal(
            id=signal_id,
            content=content,
            source_domain=source_domain,
            signal_type=signal_type,
            timestamp=datetime.now(),
            tags=self._extract_tags(content)
        )

        self.signals.append(signal)
        return signal

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content using regex patterns."""
        tags = []
        content_lower = content.lower()

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(content)
            for match in matches:
                # Clean up the match if needed
                clean_match = str(match).strip()
                if clean_match not in tags:
                    tags.append(clean_match)

        # Additional keyword-based tagging
        keywords = ['urgent', 'important', 'deadline', 'meeting', 'payment', 'invoice', 'client', 'project']
        for keyword in keywords:
            if keyword in content_lower:
                if keyword not in tags:
                    tags.append(keyword)

        return tags

    def correlate_signals(self, signal_a: Signal, signal_b: Signal) -> Optional[CorrelationResult]:
        """
        Attempt to correlate two signals and return the correlation result.

        Args:
            signal_a: First signal to correlate
            signal_b: Second signal to correlate

        Returns:
            CorrelationResult if correlation exists, None otherwise
        """
        # Skip if signals are from the same domain and type (no need to correlate similar items)
        if signal_a.source_domain == signal_b.source_domain and signal_a.signal_type == signal_b.signal_type:
            return None

        # Calculate correlation strength based on shared tags and content similarity
        shared_tags = set(signal_a.tags) & set(signal_b.tags)
        tag_correlation = len(shared_tags) / max(len(signal_a.tags), len(signal_b.tags)) if signal_a.tags or signal_b.tags else 0

        # Calculate content similarity using simple overlap
        content_similarity = self._calculate_content_similarity(signal_a.content, signal_b.content)

        # Calculate temporal proximity (signals closer in time are more likely to be related)
        time_diff = abs((signal_a.timestamp - signal_b.timestamp).total_seconds())
        temporal_correlation = max(0, 1 - (time_diff / (24 * 3600)))  # Normalize to 1 day window

        # Weighted correlation score
        correlation_strength = (tag_correlation * 0.4) + (content_similarity * 0.4) + (temporal_correlation * 0.2)

        if correlation_strength > 0.3:  # Threshold for considering signals correlated
            # Determine correlation reason
            reasons = []
            if shared_tags:
                reasons.append(f"shared tags: {', '.join(shared_tags[:3])}")
            if content_similarity > 0.3:
                reasons.append("high content similarity")
            if temporal_correlation > 0.5:
                reasons.append("temporal proximity")

            correlation_result = CorrelationResult(
                primary_signal=signal_a,
                related_signals=[signal_b],
                correlation_strength=correlation_strength,
                correlation_reason=" and ".join(reasons),
                timestamp=datetime.now()
            )

            # Add to correlations list
            self.correlations.append(correlation_result)

            # Update correlation IDs in signals
            signal_a.correlation_ids.append(signal_b.id)
            signal_b.correlation_ids.append(signal_a.id)

            return correlation_result

        return None

    def _calculate_content_similarity(self, content_a: str, content_b: str) -> float:
        """Calculate content similarity using simple word overlap."""
        words_a = set(content_a.lower().split())
        words_b = set(content_b.lower().split())

        intersection = words_a & words_b
        union = words_a | words_b

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def correlate_all_signals(self) -> List[CorrelationResult]:
        """
        Correlate all signals in the system.

        Returns:
            List of all correlation results
        """
        correlations = []

        for i, signal_a in enumerate(self.signals):
            for j, signal_b in enumerate(self.signals[i+1:], i+1):
                correlation = self.correlate_signals(signal_a, signal_b)
                if correlation:
                    correlations.append(correlation)

        return correlations

    def find_related_signals(self, signal_id: str) -> List[Signal]:
        """
        Find all signals related to a given signal ID.

        Args:
            signal_id: ID of the signal to find relations for

        Returns:
            List of related signals
        """
        target_signal = next((s for s in self.signals if s.id == signal_id), None)
        if not target_signal:
            return []

        related_signals = []
        for correlation in self.correlations:
            if correlation.primary_signal.id == signal_id:
                related_signals.extend(correlation.related_signals)
            elif any(rs.id == signal_id for rs in correlation.related_signals):
                related_signals.append(correlation.primary_signal)

        # Remove duplicates while preserving order
        seen_ids = set()
        unique_related = []
        for signal in related_signals:
            if signal.id not in seen_ids:
                seen_ids.add(signal.id)
                unique_related.append(signal)

        return unique_related

    def get_cross_domain_signals(self) -> Dict[Tuple[str, SignalType], List[Signal]]:
        """
        Get signals grouped by domain and type to facilitate cross-domain analysis.

        Returns:
            Dictionary mapping (domain, signal_type) to list of signals
        """
        grouped_signals = {}

        for signal in self.signals:
            key = (signal.source_domain, signal.signal_type)
            if key not in grouped_signals:
                grouped_signals[key] = []
            grouped_signals[key].append(signal)

        return grouped_signals

    def find_correlations_by_type(self, signal_type_a: SignalType, signal_type_b: SignalType) -> List[CorrelationResult]:
        """
        Find correlations between specific signal types.

        Args:
            signal_type_a: First signal type
            signal_type_b: Second signal type

        Returns:
            List of correlations between the specified types
        """
        relevant_correlations = []

        for correlation in self.correlations:
            primary_type = correlation.primary_signal.signal_type
            related_types = [rs.signal_type for rs in correlation.related_signals]

            # Check if this correlation involves both types
            if (primary_type == signal_type_a and signal_type_b in related_types) or \
               (primary_type == signal_type_b and signal_type_a in related_types) or \
               (primary_type == signal_type_a and any(rs.signal_type == signal_type_b for rs in correlation.related_signals)) or \
               (primary_type == signal_type_b and any(rs.signal_type == signal_type_a for rs in correlation.related_signals)):
                relevant_correlations.append(correlation)

        return relevant_correlations

    def generate_cross_domain_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights based on cross-domain correlations.

        Returns:
            List of insight dictionaries
        """
        insights = []

        # Find correlations between different domains
        for correlation in self.correlations:
            insight = {
                'primary_signal': {
                    'id': correlation.primary_signal.id,
                    'type': correlation.primary_signal.signal_type.value,
                    'domain': correlation.primary_signal.source_domain,
                    'summary': correlation.primary_signal.content[:100] + "..." if len(correlation.primary_signal.content) > 100 else correlation.primary_signal.content
                },
                'related_signals': [
                    {
                        'id': rs.id,
                        'type': rs.signal_type.value,
                        'domain': rs.source_domain,
                        'summary': rs.content[:100] + "..." if len(rs.content) > 100 else rs.content
                    } for rs in correlation.related_signals
                ],
                'correlation_strength': correlation.correlation_strength,
                'reason': correlation.correlation_reason,
                'timestamp': correlation.timestamp.isoformat()
            }
            insights.append(insight)

        return insights


def get_context_correlator_instance() -> ContextCorrelator:
    """
    Factory function to get a ContextCorrelator instance.

    Returns:
        ContextCorrelator instance
    """
    return ContextCorrelator()


if __name__ == "__main__":
    # Example usage
    correlator = get_context_correlator_instance()

    # Add some sample signals
    email_signal = correlator.add_signal(
        content="Hi John, please review the Q3 budget proposal by Friday. We need to finalize the numbers before the board meeting.",
        source_domain="communications",
        signal_type=SignalType.COMMUNICATION
    )

    task_signal = correlator.add_signal(
        content="Review Q3 budget proposal with finance team",
        source_domain="tasks",
        signal_type=SignalType.TASK
    )

    goal_signal = correlator.add_signal(
        content="Finalize Q3 budget for board presentation by end of week",
        source_domain="business_goals",
        signal_type=SignalType.BUSINESS_GOAL
    )

    # Correlate all signals
    correlations = correlator.correlate_all_signals()
    print(f"Found {len(correlations)} correlations")

    # Generate insights
    insights = correlator.generate_cross_domain_insights()
    print(f"Generated {len(insights)} cross-domain insights")

    for insight in insights:
        print(f"Correlation strength: {insight['correlation_strength']:.2f}")
        print(f"Reason: {insight['reason']}")
        print("---")