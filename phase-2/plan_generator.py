"""
Plan Generator for Phase 2 - Functional Assistant (Silver Tier)

Generates structured Plan.md files that define objectives, contain ordered checklist steps,
and explicitly mark steps requiring approval.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import PLAN_OUTPUT_DIR
from utils import generate_unique_id, format_timestamp


class PlanGenerator:
    """
    Generates structured Plan.md files for complex tasks and workflows.
    """

    def __init__(self, output_directory: Optional[Path] = None):
        """
        Initialize the plan generator.

        Args:
            output_directory: Directory to save Plan.md files (uses config default if None)
        """
        if output_directory is None:
            self.output_directory = Path(PLAN_OUTPUT_DIR)
        else:
            self.output_directory = Path(output_directory)

        # Create output directory if it doesn't exist
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def create_plan(self, title: str, objectives: List[str], steps: List[Dict[str, Any]],
                   approval_steps: Optional[List[int]] = None) -> Path:
        """
        Create a structured Plan.md file with objectives, steps, and approval markers.

        Args:
            title: Title of the plan
            objectives: List of objectives for the plan
            steps: List of step dictionaries with 'description' and 'requires_approval' keys
            approval_steps: List of step indices that require approval (alternative way to specify)

        Returns:
            Path to the created Plan.md file
        """
        if approval_steps is None:
            approval_steps = []

        # Generate unique ID for the plan
        plan_id = generate_unique_id(f"{title}_{datetime.now().isoformat()}", 12)

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"plan_{timestamp}_{plan_id}.md"
        filepath = self.output_directory / filename

        # Build the plan content
        content = f"""---
title: {title}
created: {format_timestamp()}
plan_id: {plan_id}
status: pending
---

# {title}

## Objectives
"""

        for i, objective in enumerate(objectives, 1):
            content += f"{i}. {objective}\n"

        content += "\n## Steps\n\n"

        for i, step in enumerate(steps, 1):
            step_desc = step.get('description', f'Step {i}')
            requires_approval = step.get('requires_approval', False)

            # Check if this step is in the approval_steps list
            if i in approval_steps:
                requires_approval = True

            if requires_approval:
                content += f"{i}. [ ] **[APPROVAL REQUIRED]** {step_desc}\n"
            else:
                content += f"{i}. [ ] {step_desc}\n"

        content += f"""

## Approval Requirements
- Steps marked with **[APPROVAL REQUIRED]** must be approved before execution
- Total steps requiring approval: {len([s for s in steps if s.get('requires_approval', False)]) + len(approval_steps)}
- Total steps in plan: {len(steps)}

## Dependencies
- Steps must be executed in order
- Approval-gated steps require human confirmation before proceeding

## Success Criteria
- All steps marked as completed
- All approval-required steps properly approved
- Objectives achieved as defined above

## Notes
Add any additional notes or considerations for executing this plan.
"""

        # Write the plan to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def create_email_followup_plan(self, recipient: str, subject: str, followup_points: List[str]) -> Path:
        """
        Create a specific plan for email follow-up tasks.

        Args:
            recipient: Email recipient
            subject: Email subject
            followup_points: List of points to follow up on

        Returns:
            Path to the created Plan.md file
        """
        objectives = [
            f"Follow up with {recipient} regarding {subject}",
            "Address all outstanding points from the conversation",
            "Schedule next steps or meetings as needed"
        ]

        steps = []
        for point in followup_points:
            steps.append({
                'description': f"Address: {point}",
                'requires_approval': True  # Email actions require approval
            })

        # Add closing steps
        steps.append({
            'description': f"Send follow-up email to {recipient}",
            'requires_approval': True
        })
        steps.append({
            'description': f"Log the follow-up in the system",
            'requires_approval': False
        })

        return self.create_plan(
            title=f"Email Follow-up: {subject}",
            objectives=objectives,
            steps=steps
        )

    def create_project_review_plan(self, project_name: str, review_areas: List[str], stakeholders: List[str]) -> Path:
        """
        Create a specific plan for project review tasks.

        Args:
            project_name: Name of the project
            review_areas: Areas to review
            stakeholders: Stakeholders to involve

        Returns:
            Path to the created Plan.md file
        """
        objectives = [
            f"Conduct comprehensive review of {project_name}",
            "Evaluate progress against milestones and goals",
            "Identify risks, issues, and opportunities for improvement"
        ]

        steps = []

        # Add preparation steps
        steps.append({
            'description': f"Gather all project documentation for {project_name}",
            'requires_approval': False
        })

        # Add review steps
        for area in review_areas:
            steps.append({
                'description': f"Review project status in area: {area}",
                'requires_approval': False
            })

        # Add stakeholder steps
        for stakeholder in stakeholders:
            steps.append({
                'description': f"Schedule review meeting with {stakeholder}",
                'requires_approval': True  # Meetings may require approval
            })

        # Add reporting steps
        steps.append({
            'description': f"Compile review findings for {project_name}",
            'requires_approval': False
        })

        steps.append({
            'description': f"Send review report to stakeholders",
            'requires_approval': True  # Reports may need approval before sending
        })

        return self.create_plan(
            title=f"Project Review: {project_name}",
            objectives=objectives,
            steps=steps
        )

    def create_weekly_task_plan(self, week_dates: str, priority_tasks: List[str], routine_tasks: List[str]) -> Path:
        """
        Create a specific plan for weekly task management.

        Args:
            week_dates: Date range for the week
            priority_tasks: High-priority tasks for the week
            routine_tasks: Routine tasks for the week

        Returns:
            Path to the created Plan.md file
        """
        objectives = [
            f"Complete priority tasks for the week of {week_dates}",
            "Maintain progress on routine responsibilities",
            "Prepare for upcoming deadlines and meetings"
        ]

        steps = []

        # Add priority tasks (these may require approval if they involve external actions)
        for task in priority_tasks:
            steps.append({
                'description': f"Complete priority task: {task}",
                'requires_approval': 'external' in task.lower()  # If task involves external actions, require approval
            })

        # Add routine tasks
        for task in routine_tasks:
            steps.append({
                'description': f"Perform routine task: {task}",
                'requires_approval': 'approve' in task.lower() or 'external' in task.lower()
            })

        # Add wrap-up steps
        steps.append({
            'description': "Review week's accomplishments",
            'requires_approval': False
        })

        steps.append({
            'description': "Prepare next week's plan",
            'requires_approval': False
        })

        return self.create_plan(
            title=f"Weekly Plan: {week_dates}",
            objectives=objectives,
            steps=steps
        )


# Singleton instance
plan_generator = PlanGenerator()