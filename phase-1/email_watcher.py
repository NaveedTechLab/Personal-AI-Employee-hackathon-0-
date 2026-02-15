#!/usr/bin/env python3
"""
Basic Email Watcher for Personal AI Employee

This script monitors an email inbox and creates action items in the Needs_Action folder
when specific trigger conditions are met. This is a basic implementation that demonstrates
the concept without actual email connection (which would require credentials).
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional


class EmailWatcher:
    """
    Basic email watcher that creates action items based on simulated email triggers
    """

    def __init__(self, vault_path: str, needs_action_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action_path = Path(needs_action_path)

        # Create the needs_action directory if it doesn't exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)

    def create_action_item(self, title: str, description: str, source: str = "email", priority: str = "normal"):
        """
        Create a markdown action item in the Needs_Action directory
        """
        # Generate a unique filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize title for use in filename (remove characters that are invalid in Windows)
        sanitized_title = "".join(c for c in title.lower().replace(' ', '_').replace('-', '_') if c.isalnum() or c in '._-')
        filename = f"action_{timestamp}_{sanitized_title}.md"
        filepath = self.needs_action_path / filename

        # Create the markdown content with frontmatter
        content = f"""---
title: {title}
created: {datetime.datetime.now().isoformat()}
source: {source}
priority: {priority}
status: pending
---

# {title}

## Description
{description}

## Source Information
- **Source**: {source}
- **Received**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Priority**: {priority}

## Action Required
Please review this item and take appropriate action.

## Related Links
- [[../Dashboard]]
- [[../Company_Handbook]]

## Notes
Add any notes or comments here during review.
"""

        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Created action item: {filepath}")
        return filepath

    def simulate_email_trigger(self, subject: str, body: str):
        """
        Simulate an email trigger and create an action item if conditions are met
        """
        # Define trigger conditions
        trigger_keywords = [
            "urgent", "important", "meeting", "deadline",
            "approval", "review", "follow up", "action required"
        ]

        # Check if the email contains any trigger keywords
        email_content = f"{subject} {body}".lower()
        contains_trigger = any(keyword in email_content for keyword in trigger_keywords)

        if contains_trigger:
            title = f"Email Action: {subject[:50]}{'...' if len(subject) > 50 else ''}"
            description = f"Email received with subject: '{subject}'\n\nBody excerpt: {body[:200]}{'...' if len(body) > 200 else ''}"

            # Determine priority based on keywords
            high_priority_keywords = ["urgent", "important", "asap", "immediately", "critical"]
            priority = "high" if any(kw in email_content for kw in high_priority_keywords) else "normal"

            return self.create_action_item(title, description, source="simulated_email", priority=priority)

        return None


def main():
    """
    Main function to demonstrate the email watcher functionality
    """
    # Set up paths
    vault_path = "E:/hackathon 0 qwen/Personal-AI-Employee/phase-1/vault"
    needs_action_path = f"{vault_path}/Needs_Action"

    # Create the watcher
    watcher = EmailWatcher(vault_path, needs_action_path)

    print("Email Watcher - Demonstration Mode")
    print("=================================")

    # Simulate some emails that would trigger action items
    test_emails = [
        {
            "subject": "URGENT: Project deadline approaching",
            "body": "The quarterly project deadline is approaching. Please review your deliverables and ensure they are on track for submission by Friday."
        },
        {
            "subject": "Meeting tomorrow at 10 AM",
            "body": "Just confirming our meeting scheduled for tomorrow at 10 AM. Please come prepared with your progress report and any blockers you're facing."
        },
        {
            "subject": "Monthly report review needed",
            "body": "The monthly performance report is ready for your review. Please check the figures and provide your feedback by end of day."
        },
        {
            "subject": "General newsletter",
            "body": "This is just a general newsletter with no specific action required. Feel free to read at your convenience."
        }
    ]

    for i, email in enumerate(test_emails, 1):
        print(f"\nProcessing email {i}: {email['subject']}")
        result = watcher.simulate_email_trigger(email['subject'], email['body'])

        if result:
            print(f"  [SUCCESS] Action item created: {result}")
        else:
            print(f"  - No action needed for this email")

    print(f"\nCheck the {needs_action_path} directory for created action items.")


if __name__ == "__main__":
    main()