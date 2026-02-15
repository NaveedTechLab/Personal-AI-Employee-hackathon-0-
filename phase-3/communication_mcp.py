"""
Communication MCP Server for Phase 3 - Autonomous Employee (Gold Tier)
Handles communication actions like sending emails, messages, and social media posts.
"""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from fastmcp import FastMCP
from fastmcp.tools import Tool
from pydantic import BaseModel, Field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailContent(BaseModel):
    """Model for email content."""
    to: List[str] = Field(..., description="List of recipient email addresses")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")


class SendMessageRequest(BaseModel):
    """Request model for sending messages."""
    content: EmailContent = Field(..., description="Email content to send")
    provider: str = Field("smtp", description="Provider to use for sending")


class CommunicationMCP:
    """
    MCP Server for handling communication actions like emails and messages.
    """

    def __init__(self):
        """Initialize the Communication MCP server."""
        self.mcp = FastMCP(
            name="communication-mcp",
            instructions="Handles communication actions like sending emails, messages, and social media posts"
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register tools for the communication MCP server."""
        from fastmcp.tools import Tool

        # Create and register tools
        send_email_tool = Tool.from_function(
            self.send_email,
            name="send_email",
            description="Send an email to one or more recipients"
        )
        self.mcp.add_tool(send_email_tool)

        search_emails_tool = Tool.from_function(
            self.search_emails,
            name="search_emails",
            description="Search through email communications"
        )
        self.mcp.add_tool(search_emails_tool)

        get_unread_emails_tool = Tool.from_function(
            self.get_unread_emails,
            name="get_unread_emails",
            description="Get unread emails from the inbox"
        )
        self.mcp.add_tool(get_unread_emails_tool)

        draft_reply_tool = Tool.from_function(
            self.draft_reply,
            name="draft_reply",
            description="Draft a reply to an email based on its content"
        )
        self.mcp.add_tool(draft_reply_tool)

    async def send_email(self, request: SendMessageRequest) -> Dict[str, Any]:
        """
        Send an email using SMTP.

        Args:
            request: Request containing email content

        Returns:
            Dictionary with result of the email sending operation
        """
        try:
            # Log the action for audit purposes
            from audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="communication.send_email",
                target="smtp_server",
                approval_status="pending",  # This would be determined by safety enforcer
                result="in_progress",
                context_correlation=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "recipients": request.content.to,
                    "subject": request.content.subject,
                    "provider": request.provider
                }
            )

            # Validate safety boundaries before sending
            from safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "communication.send_email",
                "email_recipients"
            )

            if not compliance.get("boundaries_respected", True):
                # Safety check failed
                log_mcp_action(
                    action_type="communication.send_email",
                    target="smtp_server",
                    approval_status="rejected",
                    result="blocked_by_safety",
                    context_correlation=log_id,
                    additional_metadata={
                        "reason": "safety_boundary_violation",
                        "compliance": compliance
                    }
                )
                return {
                    "success": False,
                    "error": "Action blocked by safety boundaries",
                    "log_id": log_id
                }

            # Check if approval is required
            from safety_enforcer import SafetyBoundary
            requires_approval = safety_enforcer.check_action_allowed(
                SafetyBoundary.COMMUNICATION_SEND,
                {"action": "send_email", "recipients": request.content.to}
            ).allowed == False

            if requires_approval:
                # Request human approval before sending
                approval_result = safety_enforcer.request_human_approval(
                    SafetyBoundary.COMMUNICATION_SEND,
                    {"action": "send_email", "recipients": request.content.to, "subject": request.content.subject}
                )

                if not approval_result:
                    log_mcp_action(
                        action_type="communication.send_email",
                        target="smtp_server",
                        approval_status="pending_approval",
                        result="waiting_for_approval",
                        context_correlation=log_id,
                        additional_metadata={
                            "approval_required": True,
                            "recipients": request.content.to
                        }
                    )
                    return {
                        "success": False,
                        "error": "Email requires human approval",
                        "log_id": log_id,
                        "requires_approval": True
                    }

            # Get email configuration from config
            from .config import EMAIL_CONFIG as config
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart()
            msg['From'] = config['email_address']
            msg['To'] = ", ".join(request.content.to)
            msg['Subject'] = request.content.subject

            msg.attach(MIMEText(request.content.body, 'plain'))

            # Send email using Gmail SMTP
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['email_address'], config['app_password'])

            text = msg.as_string()
            server.sendmail(config['email_address'], request.content.to, text)
            server.quit()

            self.logger.info(f"Email sent successfully to: {request.content.to}")
            self.logger.info(f"Subject: {request.content.subject}")

            # Log successful completion
            log_mcp_action(
                action_type="communication.send_email",
                target="smtp_server",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "recipients": request.content.to,
                    "subject": request.content.subject,
                    "provider": request.provider
                }
            )

            return {
                "success": True,
                "message": f"Email sent successfully to {len(request.content.to)} recipient(s)",
                "log_id": log_id,
                "recipients": request.content.to
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
                    "recipients": getattr(request, 'content', {}).to if hasattr(getattr(request, 'content', None), 'to') else []
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    async def search_emails(self, request: BaseModel) -> Dict[str, Any]:
        """
        Search through email communications.

        Args:
            request: Request parameters for searching emails

        Returns:
            Dictionary with search results
        """
        try:
            # Log the action
            from audit_logger import log_mcp_action
            log_id = log_mcp_action(
                action_type="communication.search_emails",
                target="email_archive",
                approval_status="read_only",
                result="in_progress",
                context_correlation=f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "search_type": "read_operation"
                }
            )

            # Get email configuration
            from config import EMAIL_CONFIG
            import imaplib
            import email
            from email.header import decode_header

            # Connect to Gmail IMAP server
            mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['smtp_server'])
            mail.login(EMAIL_CONFIG['email_address'], EMAIL_CONFIG['app_password'])

            # Select mailbox
            mail.select('inbox')

            # Search for emails (using ALL for demo, can be modified with search criteria)
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()

            # Get the most recent 5 emails
            emails = []
            for e_id in email_ids[-5:]:  # Get last 5 emails
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])

                # Decode subject
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()

                # Get sender
                sender = msg['From']

                # Get date
                date = msg['Date']

                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                email_info = {
                    "id": e_id.decode(),
                    "from": sender,
                    "subject": subject,
                    "date": date,
                    "body": body[:500] + "..." if len(body) > 500 else body  # Truncate long bodies
                }
                emails.append(email_info)

            mail.close()
            mail.logout()

            # Log successful completion
            log_mcp_action(
                action_type="communication.search_emails",
                target="email_archive",
                approval_status="read_only",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "emails_found": len(emails),
                    "search_type": "read_operation"
                }
            )

            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error searching emails: {str(e)}")

            # Log failure
            from audit_logger import log_mcp_action
            log_mcp_action(
                action_type="communication.search_emails",
                target="email_archive",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e)
                }
            )

            return {
                "success": False,
                "error": str(e),
                "emails": [],
                "count": 0
            }

    async def get_unread_emails(self, request: BaseModel) -> Dict[str, Any]:
        """
        Get unread emails from the inbox.

        Args:
            request: Request parameters for getting unread emails

        Returns:
            Dictionary with unread email results
        """
        try:
            # Log the action
            from audit_logger import log_mcp_action
            log_id = log_mcp_action(
                action_type="communication.get_unread_emails",
                target="inbox",
                approval_status="read_only",
                result="in_progress",
                context_correlation=f"inbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "action_type": "read_operation"
                }
            )

            # Get email configuration
            from config import EMAIL_CONFIG
            import imaplib
            import email
            from email.header import decode_header

            # Connect to Gmail IMAP server
            mail = imaplib.IMAP4_SSL(EMAIL_CONFIG['smtp_server'])
            mail.login(EMAIL_CONFIG['email_address'], EMAIL_CONFIG['app_password'])

            # Select mailbox
            mail.select('inbox')

            # Search for UNSEEN (unread) emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()

            # Get unread emails
            unread_emails = []
            for e_id in email_ids[-5:]:  # Get last 5 unread emails
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])

                # Decode subject
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()

                # Get sender
                sender = msg['From']

                # Get date
                date = msg['Date']

                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                email_info = {
                    "id": e_id.decode(),
                    "from": sender,
                    "subject": subject,
                    "date": date,
                    "body": body[:500] + "..." if len(body) > 500 else body  # Truncate long bodies
                }
                unread_emails.append(email_info)

            mail.close()
            mail.logout()

            # Log successful completion
            log_mcp_action(
                action_type="communication.get_unread_emails",
                target="inbox",
                approval_status="read_only",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "unread_emails_found": len(unread_emails),
                    "action_type": "read_operation"
                }
            )

            return {
                "success": True,
                "unread_emails": unread_emails,
                "count": len(unread_emails),
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error getting unread emails: {str(e)}")

            # Log failure
            from audit_logger import log_mcp_action
            log_mcp_action(
                action_type="communication.get_unread_emails",
                target="inbox",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"inbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e)
                }
            )

            return {
                "success": False,
                "error": str(e),
                "unread_emails": [],
                "count": 0
            }

    async def draft_reply(self, request: BaseModel) -> Dict[str, Any]:
        """
        Draft a reply to an email based on its content.

        Args:
            request: Request containing email content to draft a reply for

        Returns:
            Dictionary with drafted reply
        """
        try:
            # Log the action
            from audit_logger import log_mcp_action
            log_id = log_mcp_action(
                action_type="communication.draft_reply",
                target="reply_drafter",
                approval_status="read_only",  # Only drafting, not sending
                result="in_progress",
                context_correlation=f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "action_type": "draft_operation"
                }
            )

            # Get the email content from the request
            email_content = getattr(request, 'email_content', '')
            email_subject = getattr(request, 'email_subject', 'Re: Untitled')
            sender = getattr(request, 'sender', 'Unknown Sender')

            # Basic AI-powered reply drafting
            # This is a simplified version - in a real system, this would connect to an LLM
            reply_draft = self._generate_reply_draft(email_content, email_subject, sender)

            # Log successful completion
            log_mcp_action(
                action_type="communication.draft_reply",
                target="reply_drafter",
                approval_status="read_only",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "original_subject": email_subject,
                    "reply_length": len(reply_draft),
                    "action_type": "draft_operation"
                }
            )

            return {
                "success": True,
                "drafted_reply": {
                    "to": sender,
                    "subject": f"Re: {email_subject}" if not email_subject.startswith('Re:') else email_subject,
                    "body": reply_draft,
                    "original_email_content": email_content[:200] + "..." if len(email_content) > 200 else email_content
                },
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error drafting reply: {str(e)}")

            # Log failure
            from audit_logger import log_mcp_action
            log_mcp_action(
                action_type="communication.draft_reply",
                target="reply_drafter",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e)
                }
            )

            return {
                "success": False,
                "error": str(e),
                "drafted_reply": None
            }

    def _generate_reply_draft(self, email_content: str, email_subject: str, sender: str) -> str:
        """
        Generate a draft reply based on email content.

        Args:
            email_content: Content of the email to reply to
            email_subject: Subject of the email
            sender: Sender of the email

        Returns:
            Drafted reply content
        """
        import re

        # Convert to lowercase for analysis
        content_lower = email_content.lower()
        subject_lower = email_subject.lower()

        # Identify key topics and intent
        urgent_words = ['urgent', 'asap', 'immediately', 'today', 'now', 'important']
        meeting_words = ['meeting', 'schedule', 'appointment', 'discuss', 'call']
        question_words = ['can you', 'could you', 'would you', 'please', 'help', 'question', 'when', 'where', 'what', 'how', 'why', '?']
        thanks_words = ['thank you', 'thanks', 'appreciate']

        # Check for urgency
        is_urgent = any(word in content_lower for word in urgent_words)

        # Check for meeting requests
        has_meeting_request = any(word in content_lower for word in meeting_words)

        # Check for questions
        has_questions = any(word in content_lower for word in question_words)

        # Check for thanks
        has_thanks = any(word in content_lower for word in thanks_words)

        # Generate personalized response based on content analysis
        reply_parts = []

        # Greeting
        reply_parts.append(f"Dear {sender.split('@')[0] if '@' in sender else sender},")

        # Acknowledgment based on content
        if has_thanks:
            reply_parts.append("Thank you for your message and kind words.")
        elif is_urgent:
            reply_parts.append("Thank you for reaching out. I've received your urgent message and will address it promptly.")
        elif has_questions:
            reply_parts.append("Thank you for your inquiry. I'm happy to help with your request.")
        else:
            reply_parts.append("Thank you for your email. I appreciate you reaching out.")

        reply_parts.append("")  # Empty line

        # Main response based on content
        if has_meeting_request:
            reply_parts.append("Regarding your request for a meeting, I would be happy to schedule a discussion. Could you please provide a few potential times that work for your schedule?")
        elif has_questions:
            reply_parts.append("I will look into your request and provide a detailed response shortly.")
        elif is_urgent:
            reply_parts.append("I understand the urgency of your matter and will prioritize it. You can expect a response within the next few hours.")
        else:
            reply_parts.append("I am currently reviewing your message and will get back to you with a complete response soon.")

        reply_parts.append("")  # Empty line

        # Closing
        if is_urgent:
            reply_parts.append("Best regards,\nAI Assistant")
        else:
            reply_parts.append("Best regards,\nAI Assistant")

        return "\n".join(reply_parts)

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the communication MCP server.

        Returns:
            Dictionary with server information
        """
        return {
            "name": "Communication MCP Server",
            "version": "1.0.0",
            "description": "Handles communication actions like sending emails, messages, and social media posts",
            "responsibility": "Communication actions only",
            "available_tools": [
                "send_email",
                "search_emails",
                "get_unread_emails"
            ],
            "status": "running",
            "started_at": datetime.now().isoformat()
        }

    async def run(self, port: int = 8000):
        """
        Run the Communication MCP server.

        Args:
            port: Port to run the server on
        """
        self.logger.info(f"Starting Communication MCP Server on port {port}")
        await self.mcp.run(port=port)


def get_communication_mcp_instance() -> CommunicationMCP:
    """
    Factory function to get a CommunicationMCP instance.

    Returns:
        CommunicationMCP instance
    """
    return CommunicationMCP()


if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Communication MCP Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()

    async def main():
        comm_mcp = get_communication_mcp_instance()

        print("Communication MCP Server Info:")
        info = comm_mcp.get_server_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

        print(f"\nStarting server on port {args.port}...")
        await comm_mcp.run(port=args.port)

    # Run the server
    asyncio.run(main())