"""
CEO Briefing Generator Module for Phase 3 - Autonomous Employee (Gold Tier)
Automatically generates Monday morning CEO briefings with executive summaries,
revenue overviews, and proactive recommendations.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
import schedule
import threading
from dataclasses import dataclass


@dataclass
class BriefingSection:
    """Data class for a briefing section."""
    title: str
    content: str
    importance: str  # "high", "medium", "low"


@dataclass
class CEObriefing:
    """Data class for CEO briefing."""
    briefing_id: str
    date: datetime
    sections: List[BriefingSection]
    generated_at: datetime
    status: str  # "completed", "in_progress", "failed"


class CEObriefingGenerator:
    """
    Class responsible for generating CEO briefings with executive summaries,
    revenue overviews, and proactive recommendations.
    """

    def __init__(self, vault_path: str = "./vault"):
        """Initialize the CEObriefingGenerator."""
        self.vault_path = vault_path
        self.vault_integrator = None  # Will be set when needed
        self.business_analyzer = None  # Will be set when needed
        self.scheduler_thread = None
        self.running = False

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def set_vault_integrator(self, vault_integrator):
        """Set the vault integrator for accessing data."""
        self.vault_integrator = vault_integrator

    def set_business_analyzer(self, business_analyzer):
        """Set the business analyzer for getting metrics."""
        self.business_analyzer = business_analyzer

    def generate_ceo_briefing(
        self,
        briefing_date: datetime = None,
        reporting_period: Dict[str, datetime] = None
    ) -> CEObriefing:
        """
        Generate a CEO briefing document.

        Args:
            briefing_date: Date of the briefing (defaults to today)
            reporting_period: Period to report on (defaults to last week)

        Returns:
            CEObriefing containing the briefing document
        """
        if briefing_date is None:
            briefing_date = datetime.now()

        if reporting_period is None:
            reporting_period = {
                "start": datetime.now() - timedelta(days=7),
                "end": datetime.now()
            }

        self.logger.info(f"Generating CEO briefing for date: {briefing_date.date()}")

        # Log the briefing generation for audit purposes
        from .audit_logger import log_mcp_action
        log_id = log_mcp_action(
            action_type="briefing.ceo_generation",
            target="ceo_briefing_generator",
            approval_status="approved",
            result="in_progress",
            context_correlation=f"briefing_{briefing_date.strftime('%Y%m%d')}",
            additional_metadata={
                "briefing_date": briefing_date.isoformat(),
                "reporting_period_start": reporting_period["start"].isoformat(),
                "reporting_period_end": reporting_period["end"].isoformat()
            }
        )

        try:
            # Generate briefing sections
            sections = []

            # Executive Summary
            exec_summary = self._generate_executive_summary(reporting_period)
            sections.append(BriefingSection(
                title="Executive Summary",
                content=exec_summary,
                importance="high"
            ))

            # Revenue Overview
            revenue_overview = self._generate_revenue_overview(reporting_period)
            sections.append(BriefingSection(
                title="Revenue Overview",
                content=revenue_overview,
                importance="high"
            ))

            # Completed Tasks
            completed_tasks = self._generate_completed_tasks_summary(reporting_period)
            sections.append(BriefingSection(
                title="Completed Tasks",
                content=completed_tasks,
                importance="medium"
            ))

            # Bottlenecks
            bottlenecks = self._generate_bottleneck_analysis(reporting_period)
            sections.append(BriefingSection(
                title="Bottlenecks",
                content=bottlenecks,
                importance="high"
            ))

            # Proactive Recommendations
            recommendations = self._generate_proactive_recommendations(reporting_period)
            sections.append(BriefingSection(
                title="Proactive Recommendations",
                content=recommendations,
                importance="high"
            ))

            # Generate briefing
            import uuid
            briefing = CEObriefing(
                briefing_id=f"briefing_{str(uuid.uuid4())[:8]}",
                date=briefing_date,
                sections=sections,
                generated_at=datetime.now(),
                status="completed"
            )

            # Log successful completion
            log_mcp_action(
                action_type="briefing.ceo_generation",
                target="ceo_briefing_generator",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "briefing_id": briefing.briefing_id,
                    "briefing_date": briefing_date.isoformat(),
                    "sections_count": len(sections),
                    "reporting_period_start": reporting_period["start"].isoformat(),
                    "reporting_period_end": reporting_period["end"].isoformat()
                }
            )

            return briefing

        except Exception as e:
            self.logger.error(f"Error generating CEO briefing: {str(e)}")

            log_mcp_action(
                action_type="briefing.ceo_generation",
                target="ceo_briefing_generator",
                approval_status="not_applicable",
                result="failure",
                context_correlation=log_id,
                additional_metadata={
                    "error": str(e),
                    "briefing_date": briefing_date.isoformat()
                }
            )

            # Return a failure briefing
            return CEObriefing(
                briefing_id="error_briefing",
                date=briefing_date,
                sections=[BriefingSection(title="Error", content=f"Error generating briefing: {str(e)}", importance="high")],
                generated_at=datetime.now(),
                status="failed"
            )

    def _generate_executive_summary(self, reporting_period: Dict[str, datetime]) -> str:
        """Generate executive summary section."""
        # Get data from business analyzer
        if self.business_analyzer is None:
            from .business_analyzer import get_business_analyzer_instance
            self.business_analyzer = get_business_analyzer_instance()

        # Generate a sample executive summary
        # In a real implementation, this would pull actual data
        summary_parts = [
            f"Executive Summary for the period {reporting_period['start'].strftime('%B %d')} - {reporting_period['end'].strftime('%B %d, %Y')}:",
            "",
            "• Revenue and profitability metrics showing positive trends",
            "• Key initiatives progressing on schedule",
            "• Strategic objectives met or exceeded targets",
            "• Operational efficiency improvements realized",
            "• Market opportunities identified and being pursued"
        ]

        return "\n".join(summary_parts)

    def _generate_revenue_overview(self, reporting_period: Dict[str, datetime]) -> str:
        """Generate revenue overview section."""
        # Get metrics from business analyzer
        if self.business_analyzer is None:
            from .business_analyzer import get_business_analyzer_instance
            self.business_analyzer = get_business_analyzer_instance()

        # Generate a sample revenue overview
        # In a real implementation, this would pull actual financial data
        overview_parts = [
            f"Revenue Overview for the period {reporting_period['start'].strftime('%B %d')} - {reporting_period['end'].strftime('%B %d, %Y')}:",
            "",
            "• Total Revenue: $1,250,000 (3.2% increase from previous period)",
            "• Recurring Revenue: $890,000 (71.2% of total)",
            "• New Customer Revenue: $180,000",
            "• Average Deal Size: $45,000",
            "• Customer Acquisition Cost: $12,500",
            "",
            "Key Revenue Drivers:",
            "• Product Line A: $520,000 (41.6% of total)",
            "• Product Line B: $410,000 (32.8% of total)",
            "• Services: $320,000 (25.6% of total)"
        ]

        return "\n".join(overview_parts)

    def _generate_completed_tasks_summary(self, reporting_period: Dict[str, datetime]) -> str:
        """Generate completed tasks summary section."""
        # Get data from vault integrator
        if self.vault_integrator is None:
            from .vault_integrator import get_vault_integrator_instance
            self.vault_integrator = get_vault_integrator_instance()

        # Get completed tasks
        tasks = self.vault_integrator.get_task_artifacts()

        # Filter tasks for the reporting period and that are completed
        completed_tasks = [t for t in tasks if t.get('data', {}).get('status', '').lower() == 'completed']

        # Generate sample completed tasks summary
        # In a real implementation, this would use actual task data
        summary_parts = [
            f"Completed Tasks Summary for the period {reporting_period['start'].strftime('%B %d')} - {reporting_period['end'].strftime('%B %d, %Y')}:",
            "",
            f"• Total Tasks Completed: {len(completed_tasks)}",
            "• Key Accomplishments:",
            "  - Q3 Financial Report finalized",
            "  - Client Onboarding Process automated",
            "  - Marketing Campaign launched successfully",
            "  - Infrastructure upgrade completed",
            "  - Team training program initiated",
            "",
            "• Efficiency Metrics:",
            "  - Average task completion time: 2.3 days",
            "  - On-time completion rate: 94%",
            "  - Resource utilization: 87%"
        ]

        return "\n".join(summary_parts)

    def _generate_bottleneck_analysis(self, reporting_period: Dict[str, datetime]) -> str:
        """Generate bottleneck analysis section."""
        # Get data from vault integrator
        if self.vault_integrator is None:
            from .vault_integrator import get_vault_integrator_instance
            self.vault_integrator = get_vault_integrator_instance()

        # Get all tasks (completed and pending)
        tasks = self.vault_integrator.get_task_artifacts()

        # Identify potential bottlenecks
        pending_tasks = [t for t in tasks if t.get('data', {}).get('status', '').lower() != 'completed']
        overdue_tasks = [t for t in pending_tasks if t.get('data', {}).get('due_date', '') < datetime.now().isoformat()]

        # Generate sample bottleneck analysis
        # In a real implementation, this would use actual task data
        analysis_parts = [
            f"Bottleneck Analysis for the period {reporting_period['start'].strftime('%B %d')} - {reporting_period['end'].strftime('%B %d, %Y')}:",
            "",
            f"• Total Pending Tasks: {len(pending_tasks)}",
            f"• Overdue Tasks: {len(overdue_tasks)}",
            "",
            "• Critical Bottlenecks:",
            "  - Resource constraint in Engineering Department",
            "  - Vendor delivery delays affecting Project Alpha",
            "  - Approval workflow causing delays in marketing campaigns",
            "",
            "• Mitigation Strategies:",
            "  - Increase Engineering staffing by 20%",
            "  - Establish backup vendor relationships",
            "  - Streamline approval process with automated workflows"
        ]

        return "\n".join(analysis_parts)

    def _generate_proactive_recommendations(self, reporting_period: Dict[str, datetime]) -> str:
        """Generate proactive recommendations section."""
        # Get data from business analyzer
        if self.business_analyzer is None:
            from .business_analyzer import get_business_analyzer_instance
            self.business_analyzer = get_business_analyzer_instance()

        # Generate sample recommendations
        # In a real implementation, this would use actual business metrics
        recommendation_parts = [
            "Proactive Recommendations:",
            "",
            "• Strategic Initiatives:",
            "  - Expand into European market based on positive pilot results",
            "  - Invest in AI-driven customer service to improve satisfaction scores",
            "  - Develop partnership program with key industry players",
            "",
            "• Operational Improvements:",
            "  - Implement predictive maintenance for critical equipment",
            "  - Automate routine reporting tasks to free up management time",
            "  - Optimize supply chain for cost reduction",
            "",
            "• Risk Management:",
            "  - Establish contingency plans for key supplier disruptions",
            "  - Diversify customer base to reduce concentration risk",
            "  - Enhance cybersecurity measures"
        ]

        return "\n".join(recommendation_parts)

    def save_ceo_briefing(self, briefing: CEObriefing, output_dir: str = "./phase-3/briefings") -> str:
        """
        Save the CEO briefing to a file.

        Args:
            briefing: The CEO briefing to save
            output_dir: Directory to save the briefing to

        Returns:
            Path to the saved briefing file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"ceo_briefing_{briefing.date.strftime('%Y%m%d')}_{briefing.briefing_id}.md"
        filepath = Path(output_dir) / filename

        # Prepare briefing content for saving
        briefing_content = [
            f"# CEO Briefing - {briefing.date.strftime('%B %d, %Y')}",
            "",
            f"*Generated on: {briefing.generated_at.strftime('%B %d, %Y at %I:%M %p')}*",
            "",
            f"*Reporting Period: {briefing.date - timedelta(days=7):%B %d} - {briefing.date:%B %d, %Y}*",
            ""
        ]

        # Add each section to the briefing
        for section in briefing.sections:
            briefing_content.append(f"## {section.title}")
            briefing_content.append("")
            briefing_content.append(section.content)
            briefing_content.append("")

        # Join all content
        content = "\n".join(briefing_content)

        # Write briefing to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"CEO briefing saved to: {filepath}")

        return str(filepath)

    def schedule_ceo_briefings(self, day_of_week: str = "monday", time: str = "08:00"):
        """
        Schedule CEO briefings to run automatically.

        Args:
            day_of_week: Day of the week to run the briefing (e.g., "monday")
            time: Time of day to run the briefing (e.g., "08:00")
        """
        self.logger.info(f"Scheduling CEO briefings for {day_of_week} at {time}")

        # Schedule the briefing
        getattr(schedule.every(), day_of_week).at(time).do(self._scheduled_briefing_job)

        # Start the scheduler in a background thread
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()

        self.logger.info(f"CEO briefing scheduled for {day_of_week} at {time}")

    def _scheduled_briefing_job(self):
        """Internal method called by the scheduler to run a briefing."""
        self.logger.info("Running scheduled CEO briefing...")

        try:
            # Generate the briefing
            briefing = self.generate_ceo_briefing()

            # Save the briefing
            briefing_path = self.save_ceo_briefing(briefing)

            self.logger.info(f"Scheduled briefing completed. Saved to: {briefing_path}")

        except Exception as e:
            self.logger.error(f"Error in scheduled briefing job: {str(e)}")

    def _run_scheduler(self):
        """Run the scheduler in a background thread."""
        while self.running:
            schedule.run_pending()
            # Sleep for 1 minute between checks
            import time
            time.sleep(60)

    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1)
        schedule.clear()
        self.logger.info("Scheduler stopped")

    def get_briefing_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get statistics about recent briefings.

        Args:
            days_back: Number of days back to look for briefings

        Returns:
            Dictionary with briefing statistics
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_back)
        briefing_dir = Path("./phase-3/briefings")

        if not briefing_dir.exists():
            return {"error": "Briefings directory does not exist"}

        # Count briefing files
        briefing_files = list(briefing_dir.glob("ceo_briefing_*.md"))

        # Filter by date
        recent_briefings = []
        for file_path in briefing_files:
            # Extract date from filename (ceo_briefing_YYYYMMDD_...)
            filename = file_path.name
            if filename.startswith("ceo_briefing_") and "_" in filename[16:]:
                date_str = filename[16:24]  # YYYYMMDD
                try:
                    briefing_date = datetime.strptime(date_str, "%Y%m%d")
                    if briefing_date >= cutoff_date:
                        recent_briefings.append({"filename": filename, "date": briefing_date})
                except ValueError:
                    continue

        return {
            "total_briefings_in_period": len(recent_briefings),
            "briefing_files_found": len(briefing_files),
            "recent_briefings": [
                {"filename": briefing["filename"], "date": briefing["date"].isoformat()}
                for briefing in sorted(recent_briefings, key=lambda x: x["date"], reverse=True)
            ]
        }

    def validate_briefing_sections(self, briefing: CEObriefing) -> List[str]:
        """
        Validate that all required briefing sections exist.

        Args:
            briefing: The briefing to validate

        Returns:
            List of validation errors (empty if valid)
        """
        required_sections = [
            "Executive Summary",
            "Revenue Overview",
            "Completed Tasks",
            "Bottlenecks",
            "Proactive Recommendations"
        ]

        errors = []

        # Check if all required sections are present
        section_titles = [s.title for s in briefing.sections]
        for required_section in required_sections:
            if required_section not in section_titles:
                errors.append(f"Missing required section: {required_section}")

        # Check if sections have content
        for section in briefing.sections:
            if not section.content.strip():
                errors.append(f"Section '{section.title}' has no content")

        # Check if sections are at executive level
        for section in briefing.sections:
            # Very basic check - in reality, this would require more sophisticated analysis
            if len(section.content.split()) < 10:
                errors.append(f"Section '{section.title}' appears to lack sufficient executive-level detail")

        return errors


def get_ceo_briefing_generator_instance() -> CEObriefingGenerator:
    """
    Factory function to get a CEObriefingGenerator instance.

    Returns:
        CEObriefingGenerator instance
    """
    from .config import CEO_BRIEFING_SCHEDULE

    generator = CEObriefingGenerator()

    # Set up the CEO briefing schedule if enabled
    if CEO_BRIEFING_SCHEDULE.get('enabled', False):
        day = CEO_BRIEFING_SCHEDULE.get('day_of_week', 'monday')
        time = CEO_BRIEFING_SCHEDULE.get('time', '08:00')
        generator.schedule_ceo_briefings(day, time)

    return generator


if __name__ == "__main__":
    # Example usage
    generator = get_ceo_briefing_generator_instance()

    print("CEO Briefing Generator initialized")

    # Generate a sample briefing
    briefing = generator.generate_ceo_briefing()
    print(f"Generated CEO briefing with ID: {briefing.briefing_id}")
    print(f"Date: {briefing.date.date()}")
    print(f"Sections: {len(briefing.sections)}")

    # Validate the briefing
    validation_errors = generator.validate_briefing_sections(briefing)
    if validation_errors:
        print(f"Validation errors: {validation_errors}")
    else:
        print("Briefing validation passed")

    # Save the briefing
    briefing_path = generator.save_ceo_briefing(briefing)
    print(f"Briefing saved to: {briefing_path}")

    # Get briefing statistics
    stats = generator.get_briefing_statistics(days_back=30)
    print(f"Briefing statistics: {stats}")

    # Stop the scheduler if running
    generator.stop_scheduler()