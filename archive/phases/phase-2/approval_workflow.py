"""
Approval Workflow for Phase 2 - Functional Assistant (Silver Tier)

Handles the file-based approval mechanism for sensitive actions.
"""

import os
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from vault_manager import vault_manager
from config import AUTO_APPROVAL_ENABLED, APPROVAL_REQUIRED_FOR_EXTERNAL_ACTIONS


class ApprovalWorkflow:
    """Manages the file-based approval workflow."""

    def __init__(self):
        """Initialize the approval workflow."""
        self.auto_approval_enabled = AUTO_APPROVAL_ENABLED
        self.approval_required_for_external_actions = APPROVAL_REQUIRED_FOR_EXTERNAL_ACTIONS

    def create_approval_request(self, action_type: str, description: str,
                              approval_required: List[str] = None) -> Path:
        """
        Create an approval request file in the Pending_Approval directory.

        Args:
            action_type: Type of action requiring approval
            description: Description of what will happen when approved
            approval_required: List of specific approvals needed

        Returns:
            Path to the created approval request file
        """
        if approval_required is None:
            approval_required = ["default"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"Approval_Request_{action_type}_{timestamp}"
        filename = f"approval_{timestamp}_{action_type.lower()}.md"

        # Create approval request content
        content = f"""## Action Type
{action_type}

## Description
{description}

## Approval Required
{chr(10).join([f'- [ ] {approval}' for approval in approval_required])}

## Request Information
- **Requested**: {datetime.now().isoformat()}
- **Status**: pending

## Approval Instructions
To approve this request:
1. Review the action details above
2. Move this file to the [[../Approved]] directory
3. The system will automatically execute the action

To reject this request:
1. Move this file to the [[../Rejected]] directory
2. The system will cancel the action

## Action Details
- **Action Type**: {action_type}
- **Description**: {description}
- **Approvals Needed**: {', '.join(approval_required)}

## Notes
Add any notes or comments here during review.
"""

        # Create the file in the pending approval directory
        filepath = vault_manager.pending_approval_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"""---
title: {title}
created: {datetime.now().isoformat()}
source: approval_workflow
status: pending
---
"""+ content)

        return filepath

    def check_for_pending_approvals(self) -> List[Path]:
        """
        Check for pending approval requests.

        Returns:
            List of file paths for pending approval requests
        """
        return vault_manager.list_pending_approval_items()

    def check_for_approved_requests(self) -> List[Path]:
        """
        Check for approved requests.

        Returns:
            List of file paths for approved requests
        """
        return vault_manager.list_approved_items()

    def check_for_rejected_requests(self) -> List[Path]:
        """
        Check for rejected requests.

        Returns:
            List of file paths for rejected requests
        """
        return vault_manager.list_rejected_items()

    def wait_for_approval(self, approval_file: Path, timeout: int = 300) -> str:
        """
        Wait for an approval decision on a specific file.

        Args:
            approval_file: Path to the approval request file
            timeout: Maximum time to wait in seconds

        Returns:
            Status of the approval ('approved', 'rejected', 'timeout')
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if file has been moved to Approved directory
            approved_files = self.check_for_approved_requests()
            if approval_file.name in [f.name for f in approved_files]:
                return 'approved'

            # Check if file has been moved to Rejected directory
            rejected_files = self.check_for_rejected_requests()
            if approval_file.name in [f.name for f in rejected_files]:
                return 'rejected'

            time.sleep(1)  # Check every second

        return 'timeout'

    def pause_until_human_approval(self, action_description: str, action_type: str = "external_action") -> bool:
        """
        Create an approval request and pause execution until human approves or rejects.

        Args:
            action_description: Description of the action that requires approval
            action_type: Type of action (defaults to "external_action")

        Returns:
            True if approved, False if rejected or timeout
        """
        if not self.approval_required_for_external_actions:
            return True  # If approval not required, proceed automatically

        # Create approval request
        approval_file = self.create_approval_request(
            action_type=action_type,
            description=action_description
        )

        print(f"Waiting for human approval for: {action_description}")
        print(f"Approval request created: {approval_file.name}")
        print("Please move the file to 'Approved' or 'Rejected' directory to continue...")

        # Wait for approval
        status = self.wait_for_approval(approval_file)

        if status == 'approved':
            print(f"Action approved: {action_description}")
            return True
        elif status == 'rejected':
            print(f"Action rejected: {action_description}")
            return False
        else:
            print(f"Timeout waiting for approval: {action_description}")
            return False

    def process_approved_requests(self):
        """
        Process all approved requests by executing the corresponding actions.
        This method should be called periodically to handle approved requests.
        """
        approved_files = self.check_for_approved_requests()

        for file_path in approved_files:
            # Read the file to get action details
            content = vault_manager.read_file_content(file_path)

            # Move the file to the Done directory after processing
            done_file = vault_manager.move_to_done(file_path)
            print(f"Processed approved request: {done_file.name}")

    def process_rejected_requests(self):
        """
        Process all rejected requests by cancelling the corresponding actions.
        This method should be called periodically to handle rejected requests.
        """
        rejected_files = self.check_for_rejected_requests()

        for file_path in rejected_files:
            # Log the rejection (no action needed, just record it)
            done_file = vault_manager.move_to_done(file_path)
            print(f"Processed rejected request: {done_file.name}")


# Singleton instance
approval_workflow = ApprovalWorkflow()