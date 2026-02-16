"""
MCP Manager Module for Phase 3 - Autonomous Employee (Gold Tier)
Manages multiple MCP servers with distinct responsibilities and permission boundaries.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging
from urllib.parse import urljoin


class MCPActionType(Enum):
    """Enumeration of different MCP action types."""
    COMMUNICATION = "communication"
    BROWSER_ACTION = "browser_action"
    SCHEDULING = "scheduling"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"


class MCPPermissionLevel(Enum):
    """Enumeration of different permission levels for MCP actions."""
    READ_ONLY = "read_only"
    APPROVAL_REQUIRED = "approval_required"
    EXECUTE_ALLOWED = "execute_allowed"
    ADMIN = "admin"


@dataclass
class MCPConfig:
    """Configuration for an MCP server."""
    name: str
    url: str
    timeout: int
    enabled: bool
    permission_boundaries: List[MCPActionType]
    default_permission: MCPPermissionLevel


@dataclass
class MCPAction:
    """Represents an action to be executed by an MCP server."""
    id: str
    action_type: MCPActionType
    target: str
    parameters: Dict[str, Any]
    permission_level: MCPPermissionLevel
    timestamp: datetime
    requires_approval: bool = False


@dataclass
class MCPResponse:
    """Response from an MCP server."""
    action_id: str
    status: str  # 'success', 'failure', 'pending_approval'
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MCPManager:
    """
    Class responsible for managing multiple MCP servers with distinct
    responsibilities and enforcing permission boundaries.
    """

    def __init__(self, config: Dict[str, MCPConfig]):
        """
        Initialize the MCPManager with server configurations.

        Args:
            config: Dictionary mapping server names to MCPConfig objects
        """
        self.configs = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.approval_callbacks: Dict[str, Callable] = {}

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    async def initialize(self):
        """Initialize the MCPManager by creating an HTTP session."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        self.logger.info("MCPManager initialized")

    async def close(self):
        """Close the MCPManager and clean up resources."""
        if self.session:
            await self.session.close()
        self.logger.info("MCPManager closed")

    def register_approval_callback(self, action_type: MCPActionType, callback: Callable):
        """
        Register a callback function to handle approval requests for specific action types.

        Args:
            action_type: The type of action to register the callback for
            callback: The callback function to handle approval
        """
        self.approval_callbacks[action_type.value] = callback

    async def execute_action(self, action: MCPAction) -> MCPResponse:
        """
        Execute an action using the appropriate MCP server based on action type.

        Args:
            action: The action to execute

        Returns:
            MCPResponse with the result of the action
        """
        try:
            # Determine which MCP server should handle this action
            mcp_server = self._get_appropriate_mcp_server(action.action_type)

            if not mcp_server:
                return MCPResponse(
                    action_id=action.id,
                    status='failure',
                    error=f"No MCP server configured for action type: {action.action_type.value}"
                )

            # Check permissions for this action
            if not self._check_permissions(mcp_server, action):
                return MCPResponse(
                    action_id=action.id,
                    status='failure',
                    error=f"Insufficient permissions for action type: {action.action_type.value}"
                )

            # Handle approval requirements
            if action.requires_approval or action.permission_level == MCPPermissionLevel.APPROVAL_REQUIRED:
                approved = await self._request_approval(action)
                if not approved:
                    return MCPResponse(
                        action_id=action.id,
                        status='pending_approval',
                        error="Action requires approval and was not approved"
                    )

            # Execute the action on the appropriate MCP server
            response = await self._send_action_to_mcp(mcp_server, action)
            return response

        except Exception as e:
            self.logger.error(f"Error executing action {action.id}: {str(e)}")
            return MCPResponse(
                action_id=action.id,
                status='failure',
                error=str(e)
            )

    def _get_appropriate_mcp_server(self, action_type: MCPActionType) -> Optional[str]:
        """
        Determine which MCP server is appropriate for the given action type.

        Args:
            action_type: The type of action to route

        Returns:
            Name of the appropriate MCP server, or None if none found
        """
        for server_name, config in self.configs.items():
            if config.enabled and action_type in config.permission_boundaries:
                return server_name

        # Default routing based on action type
        if action_type == MCPActionType.COMMUNICATION:
            return 'communication'
        elif action_type == MCPActionType.BROWSER_ACTION:
            return 'browser'
        elif action_type == MCPActionType.SCHEDULING:
            return 'scheduling'

        return None

    def _check_permissions(self, server_name: str, action: MCPAction) -> bool:
        """
        Check if the action has appropriate permissions for the target server.

        Args:
            server_name: Name of the server to check permissions for
            action: The action to check permissions for

        Returns:
            True if permissions are adequate, False otherwise
        """
        if server_name not in self.configs:
            return False

        config = self.configs[server_name]

        # Check if the action type is allowed for this server
        if action.action_type not in config.permission_boundaries:
            return False

        # Check if the action's permission level meets or exceeds the server's requirements
        required_level = config.default_permission
        action_level = action.permission_level

        # Define permission hierarchy
        permission_hierarchy = {
            MCPPermissionLevel.READ_ONLY: 0,
            MCPPermissionLevel.APPROVAL_REQUIRED: 1,
            MCPPermissionLevel.EXECUTE_ALLOWED: 2,
            MCPPermissionLevel.ADMIN: 3
        }

        return permission_hierarchy[action_level] >= permission_hierarchy[required_level]

    async def _request_approval(self, action: MCPAction) -> bool:
        """
        Request approval for an action that requires it.

        Args:
            action: The action requiring approval

        Returns:
            True if approved, False otherwise
        """
        self.logger.info(f"Requesting approval for action {action.id} of type {action.action_type.value}")

        # Check if there's a specific callback for this action type
        callback_key = action.action_type.value
        if callback_key in self.approval_callbacks:
            try:
                # Call the registered approval callback
                approved = await self.approval_callbacks[callback_key](action)
                return approved
            except Exception as e:
                self.logger.error(f"Error in approval callback: {str(e)}")
                return False

        # Default approval behavior - deny actions requiring approval
        self.logger.warning(f"No approval callback registered for action type {action.action_type.value}")
        return False

    async def _send_action_to_mcp(self, server_name: str, action: MCPAction) -> MCPResponse:
        """
        Send an action to the specified MCP server.

        Args:
            server_name: Name of the MCP server to send the action to
            action: The action to send

        Returns:
            MCPResponse from the server
        """
        if not self.session:
            raise RuntimeError("MCPManager not initialized")

        config = self.configs[server_name]

        # Prepare the payload
        payload = {
            "action_id": action.id,
            "action_type": action.action_type.value,
            "target": action.target,
            "parameters": action.parameters,
            "timestamp": action.timestamp.isoformat(),
            "permission_level": action.permission_level.value
        }

        try:
            # Send the action to the MCP server
            url = urljoin(config.url, "/execute")
            async with self.session.post(url, json=payload, timeout=config.timeout) as response:
                response_data = await response.json()

                # Create MCPResponse from the server response
                return MCPResponse(
                    action_id=action.id,
                    status=response_data.get('status', 'unknown'),
                    result=response_data.get('result'),
                    error=response_data.get('error'),
                    timestamp=datetime.fromisoformat(response_data.get('timestamp', datetime.now().isoformat()))
                )

        except asyncio.TimeoutError:
            return MCPResponse(
                action_id=action.id,
                status='failure',
                error=f"Timeout contacting MCP server at {config.url}"
            )
        except Exception as e:
            return MCPResponse(
                action_id=action.id,
                status='failure',
                error=f"Error communicating with MCP server: {str(e)}"
            )

    async def get_server_status(self, server_name: str) -> Dict[str, Any]:
        """
        Get the status of a specific MCP server.

        Args:
            server_name: Name of the server to check

        Returns:
            Status information from the server
        """
        if not self.session:
            raise RuntimeError("MCPManager not initialized")

        if server_name not in self.configs:
            return {"error": f"Server {server_name} not configured"}

        config = self.configs[server_name]

        try:
            url = urljoin(config.url, "/status")
            async with self.session.get(url, timeout=config.timeout) as response:
                if response.status == 200:
                    status_data = await response.json()
                    status_data['online'] = True
                    status_data['last_check'] = datetime.now().isoformat()
                    return status_data
                else:
                    return {
                        "online": False,
                        "error": f"Server returned status {response.status}",
                        "last_check": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "online": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

    async def get_all_server_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all configured MCP servers.

        Returns:
            Dictionary mapping server names to their status information
        """
        statuses = {}
        for server_name in self.configs.keys():
            statuses[server_name] = await self.get_server_status(server_name)
        return statuses

    def validate_non_overlapping_authority(self) -> Dict[str, List[str]]:
        """
        Validate that MCP servers have non-overlapping authority where required.

        Returns:
            Dictionary mapping servers to lists of overlapping action types
        """
        overlaps = {}
        server_configs = list(self.configs.items())

        for i, (server1_name, server1_config) in enumerate(server_configs):
            for server2_name, server2_config in server_configs[i+1:]:
                # Find overlapping action types
                overlap = set(server1_config.permission_boundaries) & set(server2_config.permission_boundaries)

                # Check if overlaps are allowed based on configuration
                if overlap:
                    # Some overlaps might be acceptable (e.g., read-only access)
                    # For now, we'll flag all overlaps for review
                    overlaps[f"{server1_name}_vs_{server2_name}"] = [action.value for action in overlap]

        return overlaps


def get_mcp_manager_instance() -> MCPManager:
    """
    Factory function to get an MCPManager instance with default configuration.

    Returns:
        MCPManager instance
    """
    from .config import MCP_SERVERS as config_dict

    configs = {}
    for server_name, server_config in config_dict.items():
        permission_boundaries = []

        # Map server names to appropriate action types
        if server_name == 'communication':
            permission_boundaries = [MCPActionType.COMMUNICATION, MCPActionType.FILE_OPERATION]
        elif server_name == 'browser':
            permission_boundaries = [MCPActionType.BROWSER_ACTION, MCPActionType.SYSTEM_COMMAND]
        elif server_name == 'scheduling':
            permission_boundaries = [MCPActionType.SCHEDULING, MCPActionType.COMMUNICATION]

        configs[server_name] = MCPConfig(
            name=server_name,
            url=server_config['url'],
            timeout=server_config['timeout'],
            enabled=server_config['enabled'],
            permission_boundaries=permission_boundaries,
            default_permission=MCPPermissionLevel.APPROVAL_REQUIRED if server_name != 'communication' else MCPPermissionLevel.READ_ONLY
        )

    return MCPManager(configs)


if __name__ == "__main__":
    import uuid

    # Example usage
    async def main():
        # Create MCPManager instance
        manager = get_mcp_manager_instance()
        await manager.initialize()

        # Register an approval callback for financial actions
        async def financial_approval_callback(action):
            print(f"Financial action {action.id} requires approval: {action.target}")
            # In a real system, this would prompt a human for approval
            return False  # Deny by default for safety

        manager.register_approval_callback(MCPActionType.SCHEDULING, financial_approval_callback)

        # Create a sample action
        action = MCPAction(
            id=str(uuid.uuid4()),
            action_type=MCPActionType.COMMUNICATION,
            target="send_email",
            parameters={"to": "user@example.com", "subject": "Test", "body": "Test message"},
            permission_level=MCPPermissionLevel.EXECUTE_ALLOWED,
            timestamp=datetime.now(),
            requires_approval=False
        )

        # Execute the action
        response = await manager.execute_action(action)
        print(f"Action response: {response.status}")
        if response.error:
            print(f"Error: {response.error}")

        # Check server statuses
        statuses = await manager.get_all_server_status()
        print(f"Server statuses: {statuses}")

        # Validate non-overlapping authority
        overlaps = manager.validate_non_overlapping_authority()
        print(f"Authority overlaps: {overlaps}")

        # Clean up
        await manager.close()

    # Run the example
    asyncio.run(main())