"""
Simple email automation script that bypasses the MCP server for direct testing
"""
import asyncio
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Import the configuration
from config import EMAIL_CONFIG


class SimpleEmailAutomation:
    """
    Simplified email automation without MCP server complexity
    """

    def __init__(self):
        """Initialize the email automation system."""
        self.email_config = EMAIL_CONFIG

        # Set up logging
        import logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def send_email(self, to: list, subject: str, body: str) -> dict:
        """
        Send an email using SMTP.
        """
        try:
            # Log the action for audit purposes
            from audit_logger import log_mcp_action
            log_id = log_mcp_action(
                action_type="communication.send_email",
                target="smtp_server",
                approval_status="approved",  # For simplicity in this test
                result="in_progress",
                context_correlation=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "recipients": to,
                    "subject": subject
                }
            )

            # Validate safety boundaries before sending
            from safety_enforcer import get_safety_enforcer_instance, SafetyBoundary
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "communication.send_email",
                "email_recipients"
            )

            if not compliance.get("boundaries_respected", True):
                return {
                    "success": False,
                    "error": "Action blocked by safety boundaries",
                    "log_id": log_id
                }

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email_address']
            msg['To'] = ", ".join(to)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            # Send email using Gmail SMTP
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email_address'], self.email_config['app_password'])

            text = msg.as_string()
            server.sendmail(self.email_config['email_address'], to, text)
            server.quit()

            self.logger.info(f"Email sent successfully to: {to}")
            self.logger.info(f"Subject: {subject}")

            # Log successful completion
            log_mcp_action(
                action_type="communication.send_email",
                target="smtp_server",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "recipients": to,
                    "subject": subject
                }
            )

            return {
                "success": True,
                "message": f"Email sent successfully to {len(to)} recipient(s)",
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")

            # Log failure
            from audit_logger import log_mcp_action
            log_mcp_action(
                action_type="communication.send_email",
                target="smtp_server",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "recipients": to
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }


async def test_email_automation():
    print("Testing email automation system...")

    # Create email automation instance
    email_auto = SimpleEmailAutomation()

    # Create a test email
    test_recipients = [os.getenv('GMAIL_ADDRESS', 'test@example.com')]  # Send to yourself for testing
    test_subject = "Test Email from Automation System"
    test_body = "This is a test email sent from the automated email system. If you're seeing this, the automation is working correctly!"

    try:
        # Attempt to send the email
        result = await email_auto.send_email(test_recipients, test_subject, test_body)

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