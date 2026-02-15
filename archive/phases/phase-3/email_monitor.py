"""
Email Monitoring System - Monitors inbox and drafts replies to new emails every 10 minutes
"""
import asyncio
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from communication_mcp import get_communication_mcp_instance

# Load environment variables
load_dotenv()

class EmailMonitor:
    def __init__(self):
        self.comm_mcp = None
        self.last_checked = None
        self.monitoring = False
        self.processed_emails = set()  # Track email IDs that have been processed
        self.processed_emails_file = "./email_drafts/processed_emails.json"

    def load_processed_emails(self):
        """Load previously processed email IDs from file."""
        try:
            if os.path.exists(self.processed_emails_file):
                with open(self.processed_emails_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_emails = set(data.get('processed_emails', []))
        except Exception as e:
            print(f"Error loading processed emails: {str(e)}")
            self.processed_emails = set()

    def save_processed_emails(self):
        """Save processed email IDs to file."""
        try:
            # Create drafts directory if it doesn't exist
            drafts_dir = os.path.dirname(self.processed_emails_file)
            os.makedirs(drafts_dir, exist_ok=True)

            with open(self.processed_emails_file, 'w', encoding='utf-8') as f:
                json.dump({'processed_emails': list(self.processed_emails)}, f)
        except Exception as e:
            print(f"Error saving processed emails: {str(e)}")

    async def initialize(self):
        """Initialize the email monitoring system."""
        self.comm_mcp = get_communication_mcp_instance()
        # Load previously processed email IDs
        self.load_processed_emails()
        print("Email Monitor initialized")

        # Set last checked to 10 minutes ago initially
        self.last_checked = datetime.now() - timedelta(minutes=10)

    async def get_new_emails(self):
        """Get emails that have not been processed yet."""
        try:
            # Get all unread emails
            response = await self.comm_mcp.get_unread_emails(None)

            if response.get('success'):
                emails = response.get('unread_emails', [])

                # Filter out emails that have already been processed
                # Use email ID if available, otherwise use a combination of from, subject, and date as identifier
                new_emails = []
                for email in emails:
                    # Create a unique identifier for the email
                    email_id = email.get('id', f"{email.get('from', '')}_{email.get('subject', '')}_{email.get('date', '')}")

                    # Only add if we haven't processed this email before
                    if email_id not in self.processed_emails:
                        new_emails.append(email)
                        # Add to processed set to avoid processing again
                        self.processed_emails.add(email_id)

                return new_emails
            else:
                print(f"Failed to get emails: {response.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            print(f"Error getting emails: {str(e)}")
            return []

    async def draft_reply_for_email(self, email):
        """Draft a reply for a specific email."""
        try:
            # Create a request object for the draft_reply function
            request = type('Request', (), {
                'email_content': email.get('body', ''),
                'email_subject': email.get('subject', 'No Subject'),
                'sender': email.get('from', 'Unknown Sender')
            })()

            response = await self.comm_mcp.draft_reply(request)

            if response.get('success'):
                draft = response['drafted_reply']

                # Save the draft to a file for your review
                await self.save_draft_to_file(draft, email)

                print(f"[SUCCESS] Drafted reply for email from {email.get('from', 'Unknown')}".encode('ascii', 'replace').decode('ascii'))
                print(f"  Subject: {email.get('subject', 'No Subject')}".encode('ascii', 'replace').decode('ascii'))
                print(f"  Draft saved for your review")
                return True
            else:
                print(f"[FAILED] Failed to draft reply: {response.get('error', 'Unknown error')}".encode('ascii', 'replace').decode('ascii'))
                return False

        except Exception as e:
            print(f"Error drafting reply: {str(e)}")
            return False

    async def save_draft_to_file(self, draft, original_email):
        """Save the draft reply to a file for review."""
        try:
            # Create drafts directory if it doesn't exist
            drafts_dir = "./email_drafts"
            os.makedirs(drafts_dir, exist_ok=True)

            # Create a filename based on timestamp and sender
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sender_clean = original_email.get('from', 'unknown')
            # Sanitize the sender name for use in filename by removing/replacing invalid characters
            sender_clean = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in sender_clean)
            filename = f"draft_reply_{timestamp}_{sender_clean}.txt"
            filepath = os.path.join(drafts_dir, filename)

            # Write the draft with context
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=== ORIGINAL EMAIL ===\n")
                f.write(f"From: {original_email.get('from', 'Unknown')}\n")
                f.write(f"Subject: {original_email.get('subject', 'No Subject')}\n")
                f.write(f"Date: {original_email.get('date', 'Unknown')}\n")
                f.write(f"Body:\n{original_email.get('body', '')}\n\n")
                f.write("="*50 + "\n\n")
                f.write("=== DRAFTED REPLY ===\n")
                f.write(f"To: {draft['to']}\n")
                f.write(f"Subject: {draft['subject']}\n")
                f.write(f"Body:\n{draft['body']}\n")
                f.write("\n" + "="*50 + "\n")
                f.write("STATUS: DRAFT - Please review before sending\n")

            print(f"  Draft saved to: {filepath}")

        except Exception as e:
            print(f"Error saving draft to file: {str(e)}")

    async def monitor_once(self):
        """Perform one monitoring cycle - check for new emails and draft replies."""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking for new emails...")

        # Get new emails
        new_emails = await self.get_new_emails()

        if not new_emails:
            print("No new emails found.")
            return

        print(f"Found {len(new_emails)} new email(s). Drafting replies...")

        # Draft replies for each new email
        for email in new_emails:
            success = await self.draft_reply_for_email(email)

            # Small delay between processing emails
            await asyncio.sleep(1)

        # Update last checked time
        self.last_checked = datetime.now()

        # Save processed email IDs to persist across monitoring cycles
        self.save_processed_emails()

        print(f"Finished processing. Next check in 10 minutes.")

    async def start_monitoring(self):
        """Start the email monitoring loop."""
        await self.initialize()

        print("Starting email monitoring system...")
        print("Checking for new emails every 10 minutes...")
        print("Press Ctrl+C to stop monitoring.")

        self.monitoring = True

        try:
            while self.monitoring:
                await self.monitor_once()

                # Wait for 10 minutes (600 seconds) before next check
                print(f"Waiting 10 minutes until next check...")
                for i in range(600, 0, -1):
                    if not self.monitoring:  # Allow stopping during wait
                        break
                    if i % 60 == 0:
                        print(f"  {i//60} minute(s) remaining...")
                    elif i <= 10:
                        print(f"  {i} second(s) remaining...")
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop the email monitoring."""
        self.monitoring = False
        print("Email monitoring stopped.")


async def main():
    """Main function to run the email monitor."""
    monitor = EmailMonitor()

    try:
        await monitor.start_monitoring()
    except Exception as e:
        print(f"Error in email monitoring: {str(e)}")


if __name__ == "__main__":
    print("Email Monitoring System")
    print("=======================")
    print("This system will:")
    print("- Check your inbox every 10 minutes")
    print("- Find new/unread emails")
    print("- Automatically draft replies using Claude AI")
    print("- Save drafts to ./email_drafts/ for your review")
    print("- You can then review and send the drafts manually")
    print()

    asyncio.run(main())