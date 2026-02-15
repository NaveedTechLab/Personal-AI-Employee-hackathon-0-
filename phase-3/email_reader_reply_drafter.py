"""
Email Reader and Reply Drafter - Demonstrates Claude Code reading emails and drafting replies
"""
import asyncio
import os
from dotenv import load_dotenv
from communication_mcp import get_communication_mcp_instance

# Load environment variables
load_dotenv()


async def demonstrate_email_reading_and_reply_drafting():
    print("=== Email Reader and Reply Drafter Demo ===\n")

    # Create communication MCP instance
    comm_mcp = get_communication_mcp_instance()

    print("1. Reading recent emails...")
    try:
        # Get recent emails
        emails_response = await comm_mcp.search_emails(None)

        if emails_response.get('success'):
            emails = emails_response.get('emails', [])
            print(f"Found {len(emails)} recent emails:")

            for i, email in enumerate(emails[-3:], 1):  # Show last 3 emails
                print(f"  Email {i}:")
                print(f"    From: {email.get('from', 'Unknown')}")
                print(f"    Subject: {email.get('subject', 'No Subject')}")
                print(f"    Date: {email.get('date', 'Unknown')}")
                print(f"    Body Preview: {email.get('body', '')[:100]}...")
                print()

                # Draft a reply to each email
                print(f"  2. Drafting reply for email {i}...")
                draft_request = type('Request', (), {
                    'email_content': email.get('body', ''),
                    'email_subject': email.get('subject', 'No Subject'),
                    'sender': email.get('from', 'Unknown Sender')
                })()

                reply_response = await comm_mcp.draft_reply(draft_request)

                if reply_response.get('success'):
                    draft = reply_response['drafted_reply']
                    print(f"    [SUCCESS] Reply drafted successfully!")
                    print(f"    To: {draft['to']}")
                    print(f"    Subject: {draft['subject']}")
                    print(f"    Body Preview: {draft['body'][:100]}...")
                    print()
                else:
                    print(f"    [FAILED] Failed to draft reply: {reply_response.get('error', 'Unknown error')}")
                    print()
        else:
            print(f"[FAILED] Failed to get emails: {emails_response.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"[ERROR] Error during email reading: {str(e)}")

    print("\n3. Checking for unread emails...")
    try:
        # Get unread emails
        unread_response = await comm_mcp.get_unread_emails(None)

        if unread_response.get('success'):
            unread_emails = unread_response.get('unread_emails', [])
            print(f"Found {len(unread_emails)} unread emails:")

            for i, email in enumerate(unread_emails, 1):
                print(f"  Unread Email {i}:")
                print(f"    From: {email.get('from', 'Unknown')}")
                print(f"    Subject: {email.get('subject', 'No Subject')}")
                print(f"    Date: {email.get('date', 'Unknown')}")
                print(f"    Body Preview: {email.get('body', '')[:100]}...")
                print()

                # Draft a reply to each unread email
                print(f"  4. Drafting reply for unread email {i}...")
                draft_request = type('Request', (), {
                    'email_content': email.get('body', ''),
                    'email_subject': email.get('subject', 'No Subject'),
                    'sender': email.get('from', 'Unknown Sender')
                })()

                reply_response = await comm_mcp.draft_reply(draft_request)

                if reply_response.get('success'):
                    draft = reply_response['drafted_reply']
                    print(f"    [SUCCESS] Reply drafted successfully!")
                    print(f"    To: {draft['to']}")
                    print(f"    Subject: {draft['subject']}")
                    print(f"    Body Preview: {draft['body'][:100]}...")
                    print()
                else:
                    print(f"    [FAILED] Failed to draft reply: {reply_response.get('error', 'Unknown error')}")
                    print()
        else:
            print(f"[FAILED] Failed to get unread emails: {unread_response.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"✗ Error during unread email check: {str(e)}")

    print("=== Demo Complete ===")
    print("Claude Code can now:")
    print("- Read your emails (both recent and unread)")
    print("- Analyze email content to understand context and intent")
    print("- Automatically draft appropriate replies based on content")
    print("- Maintain professional tone and appropriate responses")
    print("- Log all actions for audit purposes")


async def main():
    print("Starting Email Reader and Reply Drafter...")
    await demonstrate_email_reading_and_reply_drafting()


if __name__ == "__main__":
    asyncio.run(main())