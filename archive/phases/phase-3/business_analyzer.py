"""
Business Analyzer Module for Phase 3 - Autonomous Employee (Gold Tier)
Handles business audit and analysis including weekly audits and CEO briefings.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import pandas as pd
from pathlib import Path
import schedule
import threading


@dataclass
class BusinessMetrics:
    """Data class for business metrics."""
    revenue: float = 0.0
    expenses: float = 0.0
    profit: float = 0.0
    tasks_completed: int = 0
    tasks_pending: int = 0
    goals_achieved: int = 0
    goals_total: int = 0
    anomalies_detected: int = 0
    risk_indicators: List[str] = None

    def __post_init__(self):
        if self.risk_indicators is None:
            self.risk_indicators = []


@dataclass
class AuditReport:
    """Data class for audit reports."""
    report_id: str
    period_start: datetime
    period_end: datetime
    metrics: BusinessMetrics
    insights: List[str]
    recommendations: List[str]
    anomalies: List[Dict[str, Any]]
    generated_at: datetime
    status: str  # "completed", "in_progress", "failed"


class BusinessAnalyzer:
    """
    Class responsible for business audit and analysis including weekly audits
    and CEO briefings.
    """

    def __init__(self, vault_path: str = "./vault"):
        """Initialize the BusinessAnalyzer."""
        self.vault_path = vault_path
        self.vault_integrator = None  # Will be set when needed
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

    def generate_weekly_audit(
        self,
        period_start: datetime = None,
        period_end: datetime = None
    ) -> AuditReport:
        """
        Generate a weekly business audit report.

        Args:
            period_start: Start date of the audit period (defaults to one week ago)
            period_end: End date of the audit period (defaults to now)

        Returns:
            AuditReport containing the analysis
        """
        if period_start is None:
            period_start = datetime.now() - timedelta(days=7)
        if period_end is None:
            period_end = datetime.now()

        self.logger.info(f"Generating weekly audit for period: {period_start.date()} to {period_end.date()}")

        # Log the audit generation for audit purposes
        from .audit_logger import log_mcp_action
        log_id = log_mcp_action(
            action_type="audit.weekly_generation",
            target="business_analyzer",
            approval_status="approved",
            result="in_progress",
            context_correlation=f"audit_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}",
            additional_metadata={
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }
        )

        try:
            # Aggregate data from various sources
            business_goals = self._aggregate_business_goals(period_start, period_end)
            completed_tasks = self._aggregate_completed_tasks(period_start, period_end)
            transaction_logs = self._aggregate_transaction_logs(period_start, period_end)

            # Calculate metrics
            metrics = self._calculate_business_metrics(
                business_goals,
                completed_tasks,
                transaction_logs
            )

            # Generate insights
            insights = self._generate_insights(metrics, business_goals, completed_tasks, transaction_logs)

            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, business_goals, completed_tasks)

            # Detect anomalies
            anomalies = self._detect_anomalies(transaction_logs)

            # Create audit report
            import uuid
            report = AuditReport(
                report_id=f"audit_{str(uuid.uuid4())[:8]}",
                period_start=period_start,
                period_end=period_end,
                metrics=metrics,
                insights=insights,
                recommendations=recommendations,
                anomalies=anomalies,
                generated_at=datetime.now(),
                status="completed"
            )

            # Log successful completion
            log_mcp_action(
                action_type="audit.weekly_generation",
                target="business_analyzer",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "report_id": report.report_id,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "metrics_calculated": True,
                    "insights_generated": len(insights),
                    "recommendations_generated": len(recommendations)
                }
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating weekly audit: {str(e)}")

            log_mcp_action(
                action_type="audit.weekly_generation",
                target="business_analyzer",
                approval_status="not_applicable",
                result="failure",
                context_correlation=log_id,
                additional_metadata={
                    "error": str(e),
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat()
                }
            )

            # Return a failure report
            return AuditReport(
                report_id="error_report",
                period_start=period_start,
                period_end=period_end,
                metrics=BusinessMetrics(),
                insights=[],
                recommendations=[],
                anomalies=[],
                generated_at=datetime.now(),
                status="failed"
            )

    def _aggregate_business_goals(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Aggregate business goals for the audit period."""
        if self.vault_integrator is None:
            from .vault_integrator import get_vault_integrator_instance
            self.vault_integrator = get_vault_integrator_instance()

        # Get business goals from vault
        goals = self.vault_integrator.get_business_goals()

        # Filter goals for the audit period
        period_goals = []
        for goal in goals:
            # In a real implementation, we would check the goal's timeframe
            # For this example, we'll include all goals
            period_goals.append(goal)

        return period_goals

    def _aggregate_completed_tasks(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Aggregate completed tasks for the audit period."""
        if self.vault_integrator is None:
            from .vault_integrator import get_vault_integrator_instance
            self.vault_integrator = get_vault_integrator_instance()

        # Get task artifacts from vault
        tasks = self.vault_integrator.get_task_artifacts()

        # Filter tasks for the audit period
        period_tasks = []
        for task in tasks:
            # In a real implementation, we would check the task's completion date
            # For this example, we'll include all tasks
            period_tasks.append(task)

        return period_tasks

    def _aggregate_transaction_logs(self, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Aggregate transaction logs for the audit period."""
        if self.vault_integrator is None:
            from .vault_integrator import get_vault_integrator_instance
            self.vault_integrator = get_vault_integrator_instance()

        # Get transaction logs from vault
        transactions = self.vault_integrator.get_transaction_logs()

        # Filter transactions for the audit period
        period_transactions = []
        for transaction in transactions:
            # In a real implementation, we would check the transaction's date
            # For this example, we'll include all transactions
            period_transactions.append(transaction)

        return period_transactions

    def _calculate_business_metrics(
        self,
        business_goals: List[Dict[str, Any]],
        completed_tasks: List[Dict[str, Any]],
        transaction_logs: List[Dict[str, Any]]
    ) -> BusinessMetrics:
        """Calculate business metrics from aggregated data."""
        # Calculate revenue and expenses from transaction logs
        revenue = 0.0
        expenses = 0.0

        for transaction in transaction_logs:
            data = transaction.get('data', {})
            if isinstance(data, dict):
                amount = data.get('amount', 0)
                transaction_type = data.get('type', '').lower()

                if transaction_type in ['revenue', 'income', 'sale', 'payment_received']:
                    revenue += abs(amount)
                elif transaction_type in ['expense', 'cost', 'payment_sent', 'purchase']:
                    expenses += abs(amount)

        # Calculate tasks metrics
        tasks_completed = len([t for t in completed_tasks if t.get('data', {}).get('status') == 'completed'])
        tasks_pending = len(completed_tasks) - tasks_completed

        # Calculate goals metrics
        goals_achieved = len([g for g in business_goals if g.get('data', {}).get('status') == 'achieved'])
        goals_total = len(business_goals)

        # Calculate profit
        profit = revenue - expenses

        # Detect anomalies
        anomalies_detected = self._count_anomalies(transaction_logs)

        # Generate risk indicators
        risk_indicators = self._assess_risks(revenue, expenses, tasks_pending, business_goals)

        return BusinessMetrics(
            revenue=revenue,
            expenses=expenses,
            profit=profit,
            tasks_completed=tasks_completed,
            tasks_pending=tasks_pending,
            goals_achieved=goals_achieved,
            goals_total=goals_total,
            anomalies_detected=anomalies_detected,
            risk_indicators=risk_indicators
        )

    def _count_anomalies(self, transaction_logs: List[Dict[str, Any]]) -> int:
        """Count potential anomalies in transaction logs."""
        anomaly_count = 0

        for transaction in transaction_logs:
            data = transaction.get('data', {})
            amount = data.get('amount', 0)

            # Simple anomaly detection: transactions over $10,000
            if abs(amount) > 10000:
                anomaly_count += 1

        return anomaly_count

    def _assess_risks(
        self,
        revenue: float,
        expenses: float,
        tasks_pending: int,
        business_goals: List[Dict[str, Any]]
    ) -> List[str]:
        """Assess potential risks based on business metrics."""
        risks = []

        # Revenue vs expenses risk
        if expenses > revenue:
            risks.append("Expenses exceed revenue - potential cash flow issue")

        # High pending tasks risk
        if tasks_pending > 10:  # arbitrary threshold
            risks.append(f"High number of pending tasks ({tasks_pending}) - potential bottleneck")

        # Goal achievement risk
        if len(business_goals) > 0:
            goal_completion_rate = sum(1 for g in business_goals if g.get('data', {}).get('status') == 'achieved') / len(business_goals)
            if goal_completion_rate < 0.5:  # less than 50% completion
                risks.append(f"Low goal achievement rate ({goal_completion_rate:.1%})")

        return risks

    def _generate_insights(
        self,
        metrics: BusinessMetrics,
        business_goals: List[Dict[str, Any]],
        completed_tasks: List[Dict[str, Any]],
        transaction_logs: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate business insights from metrics and data."""
        insights = []

        # Revenue and profit insights
        if metrics.revenue > 0:
            insights.append(f"Total revenue: ${metrics.revenue:,.2f}")
        if metrics.profit != 0:
            insight_type = "profit" if metrics.profit > 0 else "loss"
            insights.append(f"Net {insight_type}: ${abs(metrics.profit):,.2f}")

        # Task insights
        if metrics.tasks_completed > 0:
            insights.append(f"Completed {metrics.tasks_completed} tasks")
        if metrics.tasks_pending > 0:
            insights.append(f"{metrics.tasks_pending} tasks remain pending")

        # Goal insights
        if metrics.goals_total > 0:
            achievement_rate = (metrics.goals_achieved / metrics.goals_total) * 100 if metrics.goals_total > 0 else 0
            insights.append(f"Achieved {metrics.goals_achieved} of {metrics.goals_total} goals ({achievement_rate:.1f}%)")

        # Anomaly insights
        if metrics.anomalies_detected > 0:
            insights.append(f"Detected {metrics.anomalies_detected} potential anomalies in transactions")

        # Risk insights
        if metrics.risk_indicators:
            insights.append(f"Identified {len(metrics.risk_indicators)} risk factors")

        return insights

    def _generate_recommendations(
        self,
        metrics: BusinessMetrics,
        business_goals: List[Dict[str, Any]],
        completed_tasks: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on metrics and data."""
        recommendations = []

        # Financial recommendations
        if metrics.expenses > metrics.revenue:
            recommendations.append("Consider cost reduction measures to address negative cash flow")
        else:
            profit_margin = (metrics.revenue - metrics.expenses) / metrics.revenue if metrics.revenue > 0 else 0
            if profit_margin < 0.1:
                recommendations.append("Consider strategies to improve profit margins")

        # Task recommendations
        if metrics.tasks_pending > 10:
            recommendations.append("Consider redistributing workload or adding resources to address pending tasks")

        # Goal recommendations
        goal_completion_rate = (metrics.goals_achieved / metrics.goals_total) * 100 if metrics.goals_total > 0 else 0
        if goal_completion_rate < 70:
            recommendations.append("Review goal-setting process and consider breaking down larger goals into smaller milestones")

        # General recommendations
        if metrics.anomalies_detected > 0:
            recommendations.append("Review flagged transactions for potential issues")

        if metrics.risk_indicators:
            recommendations.append("Address identified risk factors promptly")

        return recommendations

    def _detect_anomalies(self, transaction_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in transaction logs."""
        anomalies = []

        for i, transaction in enumerate(transaction_logs):
            data = transaction.get('data', {})
            amount = data.get('amount', 0)

            # Simple anomaly detection: transactions over $10,000
            if abs(amount) > 10000:
                anomalies.append({
                    "transaction_index": i,
                    "amount": amount,
                    "reason": "Amount exceeds $10,000 threshold",
                    "timestamp": transaction.get('timestamp', datetime.now().isoformat())
                })

        return anomalies

    def save_audit_report(self, report: AuditReport, output_dir: str = "./phase-3/audits") -> str:
        """
        Save the audit report to a file.

        Args:
            report: The audit report to save
            output_dir: Directory to save the report to

        Returns:
            Path to the saved report file
        """
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename = f"audit_report_{report.period_start.strftime('%Y%m%d')}_{report.report_id}.json"
        filepath = Path(output_dir) / filename

        # Prepare report data for saving
        report_data = {
            "report_id": report.report_id,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "metrics": {
                "revenue": report.metrics.revenue,
                "expenses": report.metrics.expenses,
                "profit": report.metrics.profit,
                "tasks_completed": report.metrics.tasks_completed,
                "tasks_pending": report.metrics.tasks_pending,
                "goals_achieved": report.metrics.goals_achieved,
                "goals_total": report.metrics.goals_total,
                "anomalies_detected": report.metrics.anomalies_detected,
                "risk_indicators": report.metrics.risk_indicators
            },
            "insights": report.insights,
            "recommendations": report.recommendations,
            "anomalies": report.anomalies,
            "generated_at": report.generated_at.isoformat(),
            "status": report.status
        }

        # Write report to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        self.logger.info(f"Audit report saved to: {filepath}")

        return str(filepath)

    def schedule_weekly_audits(self, day_of_week: str = "monday", time: str = "09:00"):
        """
        Schedule weekly audits to run automatically.

        Args:
            day_of_week: Day of the week to run the audit (e.g., "monday")
            time: Time of day to run the audit (e.g., "09:00")
        """
        self.logger.info(f"Scheduling weekly audits for {day_of_week} at {time}")

        # Clear any existing schedules
        schedule.clear()

        # Schedule the audit
        getattr(schedule.every(), day_of_week).at(time).do(self._scheduled_audit_job)

        # Start the scheduler in a background thread
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()

        self.logger.info(f"Weekly audit scheduled for {day_of_week} at {time}")

    def _scheduled_audit_job(self):
        """Internal method called by the scheduler to run an audit."""
        self.logger.info("Running scheduled weekly audit...")

        try:
            # Generate the audit report
            report = self.generate_weekly_audit()

            # Save the report
            report_path = self.save_audit_report(report)

            self.logger.info(f"Scheduled audit completed. Report saved to: {report_path}")

        except Exception as e:
            self.logger.error(f"Error in scheduled audit job: {str(e)}")

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

    def get_audit_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get statistics about recent audits.

        Args:
            days_back: Number of days back to look for audits

        Returns:
            Dictionary with audit statistics
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_back)
        audit_dir = Path("./phase-3/audits")

        if not audit_dir.exists():
            return {"error": "Audits directory does not exist"}

        # Count audit files
        audit_files = list(audit_dir.glob("audit_report_*.json"))

        # Filter by date
        recent_audits = []
        for file_path in audit_files:
            # Extract date from filename (audit_report_YYYYMMDD_...)
            filename = file_path.name
            if filename.startswith("audit_report_") and "_" in filename[13:]:
                date_str = filename[13:21]  # YYYYMMDD
                try:
                    audit_date = datetime.strptime(date_str, "%Y%m%d")
                    if audit_date >= cutoff_date:
                        recent_audits.append({"filename": filename, "date": audit_date})
                except ValueError:
                    continue

        return {
            "total_audits_in_period": len(recent_audits),
            "audit_files_found": len(audit_files),
            "recent_audits": [
                {"filename": audit["filename"], "date": audit["date"].isoformat()}
                for audit in sorted(recent_audits, key=lambda x: x["date"], reverse=True)
            ]
        }


def get_business_analyzer_instance() -> BusinessAnalyzer:
    """
    Factory function to get a BusinessAnalyzer instance.

    Returns:
        BusinessAnalyzer instance
    """
    from .config import WEEKLY_AUDIT_SCHEDULE

    analyzer = BusinessAnalyzer()

    # Set up the weekly audit schedule if enabled
    if WEEKLY_AUDIT_SCHEDULE.get('enabled', False):
        day = WEEKLY_AUDIT_SCHEDULE.get('day_of_week', 'monday')
        time = WEEKLY_AUDIT_SCHEDULE.get('time', '09:00')
        analyzer.schedule_weekly_audits(day, time)

    return analyzer


if __name__ == "__main__":
    # Example usage
    analyzer = get_business_analyzer_instance()

    print("Business Analyzer initialized")

    # Generate a sample audit report
    report = analyzer.generate_weekly_audit()
    print(f"Generated audit report with ID: {report.report_id}")
    print(f"Period: {report.period_start.date()} to {report.period_end.date()}")
    print(f"Metrics - Revenue: ${report.metrics.revenue}, Profit: ${report.metrics.profit}")
    print(f"Insights: {len(report.insights)}, Recommendations: {len(report.recommendations)}")

    # Save the report
    report_path = analyzer.save_audit_report(report)
    print(f"Report saved to: {report_path}")

    # Get audit statistics
    stats = analyzer.get_audit_statistics(days_back=30)
    print(f"Audit statistics: {stats}")

    # Stop the scheduler if running
    analyzer.stop_scheduler()