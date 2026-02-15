"""
Enhanced Email Watcher for Phase 2 - Functional Assistant (Silver Tier)

Extends the base watcher functionality with improved schema consistency and Phase 2 features.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from base_watcher import BaseWatcher


class EmailWatcher(BaseWatcher):
    """
    Enhanced email watcher that creates action items based on email triggers
    Compatible with Phase 2 requirements and schema consistency
    """

    def __init__(self, vault_path: Optional[str] = None, poll_interval: int = 60):
        """
        Initialize the enhanced email watcher.

        Args:
            vault_path: Path to the vault directory (uses config if None)
            poll_interval: Polling interval in seconds
        """
        super().__init__(name="email", poll_interval=poll_interval)

        if vault_path is None:
            try:
                from .config import VAULT_DIR
                self.vault_path = VAULT_DIR
            except ImportError:
                # Handle when run as main module
                import sys
                from pathlib import Path
                sys.path.append(str(Path(__file__).parent))
                from config import VAULT_DIR
                self.vault_path = VAULT_DIR
        else:
            self.vault_path = Path(vault_path)

        self.needs_action_path = self.vault_path / "Needs_Action"

        # Create the needs_action directory if it doesn't exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self) -> list:
        """
        Check the email source for new items.
        In this simulation, we'll generate some test emails periodically.

        Returns:
            List of email items that need processing
        """
        # This is a simulation - in a real implementation, this would connect to an email server
        # For demonstration, we'll create simulated emails based on some trigger conditions

        # Simulate checking for new emails by generating test data
        import random
        import time

        # Only generate new emails occasionally to simulate real email arrival
        if random.random() < 0.3:  # 30% chance of generating new emails during each check
            current_time = datetime.datetime.now()

            # Different types of simulated emails
            email_types = [
                {
                    "subject": "URGENT: Project deadline approaching",
                    "body": "The quarterly project deadline is approaching. Please review your deliverables and ensure they are on track for submission by Friday.",
                    "priority": "high"
                },
                {
                    "subject": "Meeting tomorrow at 10 AM",
                    "body": "Just confirming our meeting scheduled for tomorrow at 10 AM. Please come prepared with your progress report and any blockers you're facing.",
                    "priority": "normal"
                },
                {
                    "subject": "Monthly report review needed",
                    "body": "The monthly performance report is ready for your review. Please check the figures and provide your feedback by end of day.",
                    "priority": "normal"
                },
                {
                    "subject": "Action required: System maintenance",
                    "body": "Scheduled system maintenance will occur this weekend. Please ensure all critical work is saved and backed up before Saturday morning.",
                    "priority": "high"
                },
                {
                    "subject": "General newsletter",
                    "body": "This is just a general newsletter with no specific action required. Feel free to read at your convenience.",
                    "priority": "low"
                }
            ]

            # Randomly select a few emails to simulate
            num_emails = random.randint(1, 3)
            selected_emails = random.sample(email_types, min(num_emails, len(email_types)))

            return selected_emails

        return []  # No new emails to process

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email item and convert it to a standardized format.

        Args:
            item: Raw email item dictionary

        Returns:
            Dictionary with standardized format
        """
        subject = item.get('subject', 'No Subject')
        body = item.get('body', 'No Body')
        priority = item.get('priority', 'normal')

        # Create standardized output
        processed_item = {
            'title': f"Email Action: {subject[:50]}{'...' if len(subject) > 50 else ''}",
            'description': f"Email received with subject: '{subject}'\n\nBody excerpt: {body[:200]}{'...' if len(body) > 200 else ''}",
            'priority': priority,
            'source': 'email_imap',
            'action_required': 'Please review this email and take appropriate action.'
        }

        return processed_item

    def simulate_specific_email(self, subject: str, body: str, priority: str = "normal"):
        """
        Simulate a specific email trigger and create an action item if conditions are met.

        Args:
            subject: Email subject
            body: Email body content
            priority: Priority level (normal, high, urgent)
        """
        # Define trigger conditions
        trigger_keywords = [
            "urgent", "important", "meeting", "deadline",
            "approval", "review", "follow up", "action required", "asap"
        ]

        # Check if the email contains any trigger keywords
        email_content = f"{subject} {body}".lower()
        contains_trigger = any(keyword in email_content for keyword in trigger_keywords)

        if contains_trigger:
            title = f"Email Action: {subject[:50]}{'...' if len(subject) > 50 else ''}"
            description = f"Email received with subject: '{subject}'\n\nBody excerpt: {body[:200]}{'...' if len(body) > 200 else ''}"

            # Determine priority based on keywords
            high_priority_keywords = ["urgent", "important", "asap", "immediately", "critical", "deadline"]
            priority = "high" if any(kw in email_content for kw in high_priority_keywords) else priority

            return self.create_action_item(
                title=title,
                description=description,
                priority=priority,
                source="email_imap",
                action_required="Please review this email and take appropriate action."
            )

        return None

    def run_demo(self):
        """
        Run a demonstration of the email watcher functionality
        """
        print("Enhanced Email Watcher - Demonstration Mode")
        print("===========================================")

        # Simulate some emails that would trigger action items
        demo_emails = [
            {
                "subject": "URGENT: Project deadline approaching",
                "body": "The quarterly project deadline is approaching. Please review your deliverables and ensure they are on track for submission by Friday.",
                "priority": "high"
            },
            {
                "subject": "Meeting tomorrow at 10 AM",
                "body": "Just confirming our meeting scheduled for tomorrow at 10 AM. Please come prepared with your progress report and any blockers you're facing.",
                "priority": "normal"
            },
            {
                "subject": "Monthly report review needed",
                "body": "The monthly performance report is ready for your review. Please check the figures and provide your feedback by end of day.",
                "priority": "normal"
            },
            {
                "subject": "General newsletter",
                "body": "This is just a general newsletter with no specific action required. Feel free to read at your convenience.",
                "priority": "low"
            }
        ]

        for i, email in enumerate(demo_emails, 1):
            print(f"\nProcessing email {i}: {email['subject']}")
            result = self.simulate_specific_email(
                email['subject'],
                email['body'],
                email['priority']
            )

            if result:
                print(f"  [SUCCESS] Action item created: {result}")
            else:
                print(f"  - No action needed for this email")

        print(f"\nCheck the {self.needs_action_path} directory for created action items.")


def main():
    """
    Main function to demonstrate the enhanced email watcher functionality
    """
    # Create the watcher
    watcher = EmailWatcher()

    # Run the demo
    watcher.run_demo()


if __name__ == "__main__":
    main()