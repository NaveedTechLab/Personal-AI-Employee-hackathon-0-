"""
Coordinator for Phase 2 - Functional Assistant (Silver Tier)

Coordinates all components of the system: watchers, plan generation, approval workflow,
MCP integration, and scheduling.
"""

import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from email_watcher import EmailWatcher
from filesystem_watcher import FilesystemWatcher
from base_watcher import WatcherManager
from plan_generator import plan_generator
from approval_workflow import approval_workflow
from mcp_client import mcp_client
from scheduler import Scheduler, run_claude_execution_cycle
from vault_manager import vault_manager
from schema_validator import schema_validator


class Coordinator:
    """
    Coordinates all components of the Personal AI Employee system.
    """

    def __init__(self):
        """Initialize the coordinator with all system components."""
        # Initialize watchers
        self.email_watcher = EmailWatcher()
        self.filesystem_watcher = FilesystemWatcher()
        self.watcher_manager = WatcherManager()

        # Register watchers with the manager
        self.watcher_manager.register_watcher(self.email_watcher)
        self.watcher_manager.register_watcher(self.filesystem_watcher)

        # Initialize scheduler
        self.scheduler = Scheduler()

        # Add Claude execution cycle to scheduler
        self.scheduler.add_job(run_claude_execution_cycle)

        # Component status tracking
        self.components_running = {
            'email_watcher': False,
            'filesystem_watcher': False,
            'scheduler': False,
            'approval_workflow': True  # Always available
            }

    def start_watchers(self):
        """Start both watchers in separate threads."""
        print("Starting watchers...")

        # Create threads for each watcher
        email_thread = threading.Thread(target=self.email_watcher.run_continuous, daemon=True)
        filesystem_thread = threading.Thread(target=self.filesystem_watcher.run_continuous, daemon=True)

        # Start the threads
        email_thread.start()
        filesystem_thread.start()

        # Update status
        self.components_running['email_watcher'] = True
        self.components_running['filesystem_watcher'] = True

        print("Watchers started successfully")

    def start_scheduler(self):
        """Start the scheduler."""
        print("Starting scheduler...")
        self.scheduler.start()
        self.components_running['scheduler'] = True
        print("Scheduler started successfully")

    def process_needs_action_items(self):
        """
        Process items in the Needs_Action directory.
        This could involve creating plans for complex items or taking other actions.
        """
        needs_action_items = vault_manager.list_needs_action_items()

        for item_path in needs_action_items:
            print(f"Processing item: {item_path.name}")

            # Read the item content to determine what to do
            content = vault_manager.read_file_content(item_path)

            # For complex items, generate a plan
            if self._is_complex_task(content):
                print(f"Generating plan for complex task: {item_path.name}")
                self._generate_plan_for_item(item_path, content)

            # For approval-required items, create approval request
            elif self._requires_approval(content):
                print(f"Creating approval request for: {item_path.name}")
                self._create_approval_request_for_item(item_path, content)

    def _is_complex_task(self, content: str) -> bool:
        """
        Determine if an item represents a complex task that requires planning.

        Args:
            content: Content of the action item

        Returns:
            True if the task is complex, False otherwise
        """
        # Look for indicators of complex tasks
        complex_indicators = [
            'multiple steps', 'series of', 'complex', 'involve several',
            'requires planning', 'multi-step', 'several components'
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in complex_indicators)

    def _requires_approval(self, content: str) -> bool:
        """
        Determine if an item requires approval before action.

        Args:
            content: Content of the action item

        Returns:
            True if approval is required, False otherwise
        """
        # Look for indicators that require approval
        approval_indicators = [
            'email', 'send message', 'contact', 'reach out', 'external action',
            'meeting', 'calendar', 'schedule', 'approval needed', 'requires permission'
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in approval_indicators)

    def _generate_plan_for_item(self, item_path: Path, content: str):
        """
        Generate a plan for a complex item.

        Args:
            item_path: Path to the action item
            content: Content of the action item
        """
        # Extract task information from the item
        title = f"Plan for: {item_path.stem}"

        # Simple extraction - in a real system this would be more sophisticated
        objectives = [f"Process the task described in {item_path.name}"]
        steps = [
            {'description': f'Review the original item: {item_path.name}', 'requires_approval': False},
            {'description': 'Analyze the requirements', 'requires_approval': False},
            {'description': 'Execute the necessary actions', 'requires_approval': True},
            {'description': 'Verify completion', 'requires_approval': False}
        ]

        # Create the plan
        plan_path = plan_generator.create_plan(
            title=title,
            objectives=objectives,
            steps=steps
        )

        print(f"Plan created: {plan_path}")

    def _create_approval_request_for_item(self, item_path: Path, content: str):
        """
        Create an approval request for an item that requires approval.

        Args:
            item_path: Path to the action item
            content: Content of the action item
        """
        description = f"External action required based on item: {item_path.name}"
        action_type = "external_action"

        # Create approval request
        approval_file = approval_workflow.create_approval_request(
            action_type=action_type,
            description=description
        )

        print(f"Approval request created: {approval_file}")

    def process_approved_requests(self):
        """Process all approved requests by executing the corresponding actions."""
        approval_workflow.process_approved_requests()

    def process_rejected_requests(self):
        """Process all rejected requests by cancelling the corresponding actions."""
        approval_workflow.process_rejected_requests()

    def run_single_cycle(self):
        """
        Run a single cycle of the coordinator to process all pending items.
        """
        print(f"[CYCLE START] Coordinator cycle started at {datetime.now()}")

        # Process any pending approval requests
        print("Checking for pending approvals...")
        pending_approvals = approval_workflow.check_for_pending_approvals()
        print(f"Found {len(pending_approvals)} pending approval requests")

        # Process items in Needs_Action
        print("Processing Needs_Action items...")
        self.process_needs_action_items()

        # Process approved requests
        print("Processing approved requests...")
        self.process_approved_requests()

        # Process rejected requests
        print("Processing rejected requests...")
        self.process_rejected_requests()

        print(f"[CYCLE END] Coordinator cycle completed at {datetime.now()}")

    def run_continuous(self):
        """
        Run the coordinator continuously, processing items at regular intervals.
        """
        print("Starting continuous coordinator...")

        try:
            while True:
                self.run_single_cycle()
                # Wait for 30 seconds before the next cycle
                time.sleep(30)
        except KeyboardInterrupt:
            print("Stopping coordinator...")
            self.stop()

    def stop(self):
        """Stop all components of the coordinator."""
        print("Stopping coordinator components...")

        # Stop watchers
        if self.components_running['email_watcher']:
            self.email_watcher.stop()
            self.components_running['email_watcher'] = False

        if self.components_running['filesystem_watcher']:
            self.filesystem_watcher.stop()
            self.components_running['filesystem_watcher'] = False

        # Stop scheduler
        if self.components_running['scheduler']:
            self.scheduler.stop()
            self.components_running['scheduler'] = False

        print("Coordinator stopped.")


def main():
    """
    Main function to run the coordinator system.
    """
    print("Personal AI Employee - Phase 2 Coordinator")
    print("===========================================")

    # Create coordinator instance
    coordinator = Coordinator()

    # Start the coordinator
    try:
        coordinator.run_continuous()
    except KeyboardInterrupt:
        print("\nShutting down coordinator...")
        coordinator.stop()


if __name__ == "__main__":
    main()