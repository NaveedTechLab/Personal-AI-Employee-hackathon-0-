"""
MCP Client for Phase 2 - Functional Assistant (Silver Tier)

Client module for communicating with the MCP server to execute external actions.
"""

import requests
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from config import MCP_SERVER_URL, MCP_SERVER_ENABLED


class MCPClient:
    """
    Client for communicating with the MCP server to execute external actions.
    All actions require explicit approval before execution.
    """

    def __init__(self, server_url: Optional[str] = None):
        """
        Initialize the MCP client.

        Args:
            server_url: URL of the MCP server (uses config default if None)
        """
        if server_url is None:
            self.server_url = MCP_SERVER_URL
        else:
            self.server_url = server_url

        self.enabled = MCP_SERVER_ENABLED
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Personal-AI-Employee-MCP-Client/1.0'
        })

    def send_email(self, to: str, subject: str, body: str, approval_id: str) -> Dict[str, Any]:
        """
        Send an email via the MCP server after approval.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            approval_id: ID of the approval that authorized this action

        Returns:
            Dictionary with response status and details
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'MCP server is disabled',
                'error': 'MCP_SERVER_DISABLED'
            }

        payload = {
            'to': to,
            'subject': subject,
            'body': body,
            'approval_id': approval_id
        }

        try:
            response = self.session.post(
                f"{self.server_url}/send-email",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'status': 'success',
                    'message_id': result.get('message_id'),
                    'server_response': result
                }
            else:
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'server_response': response.text
                }

        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'error': 'CONNECTION_ERROR',
                'message': 'Unable to connect to MCP server'
            }
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error': 'TIMEOUT',
                'message': 'Request to MCP server timed out'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': 'UNKNOWN_ERROR',
                'message': str(e)
            }

    def check_approval_status(self, approval_id: str) -> Dict[str, Any]:
        """
        Check the status of a specific approval request.

        Args:
            approval_id: ID of the approval request to check

        Returns:
            Dictionary with approval status and details
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'MCP server is disabled',
                'error': 'MCP_SERVER_DISABLED'
            }

        try:
            response = self.session.get(
                f"{self.server_url}/status/{approval_id}",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text
                }

        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'error': 'CONNECTION_ERROR',
                'message': 'Unable to connect to MCP server'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': 'UNKNOWN_ERROR',
                'message': str(e)
            }

    def execute_action(self, action_type: str, action_data: Dict[str, Any], approval_id: str) -> Dict[str, Any]:
        """
        Execute a generic action via the MCP server after approval.

        Args:
            action_type: Type of action to execute (e.g., 'send_email', 'create_calendar_event')
            action_data: Data required for the action
            approval_id: ID of the approval that authorized this action

        Returns:
            Dictionary with response status and details
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'MCP server is disabled',
                'error': 'MCP_SERVER_DISABLED'
            }

        # Route to specific action handlers
        if action_type == 'send_email':
            return self.send_email(
                to=action_data.get('to'),
                subject=action_data.get('subject'),
                body=action_data.get('body'),
                approval_id=approval_id
            )

        # Add other action types as needed
        return {
            'status': 'error',
            'error': 'UNSUPPORTED_ACTION_TYPE',
            'message': f'Action type {action_type} is not supported'
        }

    def ping(self) -> bool:
        """
        Check if the MCP server is reachable.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


# Singleton instance
mcp_client = MCPClient()