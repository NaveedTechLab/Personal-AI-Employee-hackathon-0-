"""
Test script to verify email automation functionality
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the communication MCP
from communication_mcp import CommunicationMCP, SendMessageRequest, EmailContent

async def test_email_automation():
    print("Testing email automation system...")

    # Create communication MCP instance
    comm_mcp = CommunicationMCP()

    # Create a test email request
    test_email = SendMessageRequest(
        content=EmailContent(
            to=[os.getenv('GMAIL_ADDRESS', 'test@example.com')],  # Send to yourself for testing
            subject="Test Email from Automation System",
            body="This is a test email sent from the automated email system. If you're seeing this, the automation is working correctly!",
            cc=None,
            bcc=None
        ),
        provider="gmail"
    )

    try:
        # Attempt to send the email
        result = await comm_mcp.send_email(test_email)

        if result.get('success', False):
            print("[SUCCESS] Email sent successfully!")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Log ID: {result.get('log_id', 'No log ID')}")
        else:
            print("[FAILED] Email failed to send")
            print(f"Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"[ERROR] Error during email test: {str(e)}")

if __name__ == "__main__":
    print("Starting email automation test...")
    asyncio.run(test_email_automation())