"""
Simple Email Monitor - Checks for new emails and drafts replies (runs once)
"""
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from communication_mcp import get_communication_mcp_instance

# Load environment variables
load_dotenv()

class SimpleEmailMonitor:
    def __init__(self):
        self.comm_mcp = None
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
        print("Simple Email Monitor initialized")

    async def check_and_draft_replies(self):
        """Check for new emails and draft replies."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking for new emails...")

        # Get unread emails
        response = await self.comm_mcp.get_unread_emails(None)

        if not response.get('success'):
            print(f"Failed to get emails: {response.get('error', 'Unknown error')}")
            return

        emails = response.get('unread_emails', [])

        if not emails:
            print("No new emails found.")
            return

        # Filter out emails that have already been processed in previous runs
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

        if not new_emails:
            print("No new emails to process (all emails have been processed in previous runs).")
            return

        print(f"Found {len(new_emails)} new email(s) to process. Drafting replies...")

        # Draft replies for each new email
        for i, email in enumerate(new_emails, 1):
            print(f"\nProcessing email {i}/{len(new_emails)}:")
            print(f"  From: {email.get('from', 'Unknown')}".encode('ascii', 'replace').decode('ascii'))
            print(f"  Subject: {email.get('subject', 'No Subject')}".encode('ascii', 'replace').decode('ascii'))

            # Create a request object for the draft_reply function
            request = type('Request', (), {
                'email_content': email.get('body', ''),
                'email_subject': email.get('subject', 'No Subject'),
                'sender': email.get('from', 'Unknown Sender')
            })()

            # Draft the reply
            draft_response = await self.comm_mcp.draft_reply(request)

            if draft_response.get('success'):
                draft = draft_response['drafted_reply']

                # Save the draft to a file for your review
                await self.save_draft_to_file(draft, email)

                print(f"  [SUCCESS] Reply drafted and saved for: {email.get('from', 'Unknown')}")
            else:
                print(f"  [FAILED] Failed to draft reply: {draft_response.get('error', 'Unknown error')}")

            # Small delay between processing emails
            await asyncio.sleep(0.5)

        print(f"\nCompleted processing {len(new_emails)} new email(s).")
        print("Drafts saved in ./email_drafts/ for your review.")

        # Save processed email IDs to persist across runs
        self.save_processed_emails()

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
                f.write(f"Draft created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        except Exception as e:
            print(f"Error saving draft to file: {str(e)}")

async def main():
    """Main function to run the simple email monitor."""
    print("Simple Email Monitor")
    print("====================")
    print("Checking for new emails and drafting replies...")
    print()

    monitor = SimpleEmailMonitor()
    await monitor.initialize()
    await monitor.check_and_draft_replies()

    print("\nProcess completed!")
    print("Check the ./email_drafts/ folder for your email reply drafts.")
    print("Review the drafts and send them manually when ready.")

if __name__ == "__main__":
    asyncio.run(main())