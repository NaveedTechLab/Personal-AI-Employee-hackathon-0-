"""
Scheduling MCP Server for Phase 3 - Autonomous Employee (Gold Tier)
Handles scheduling actions like calendar management, appointment booking, and task scheduling.
"""

import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from fastmcp import FastMCP, Tool
from pydantic import BaseModel, Field
import schedule
import threading


class CreateEventRequest(BaseModel):
    """Request model for creating a calendar event."""
    title: str = Field(..., description="Title of the event")
    start_time: str = Field(..., description="Start time of the event in ISO format")
    end_time: str = Field(..., description="End time of the event in ISO format")
    attendees: Optional[list[str]] = Field(None, description="List of attendee email addresses")
    description: Optional[str] = Field(None, description="Description of the event")


class ScheduleTaskRequest(BaseModel):
    """Request model for scheduling a task."""
    task_name: str = Field(..., description="Name of the task to schedule")
    execution_time: str = Field(..., description="Time to execute the task in ISO format")
    recurrence: Optional[str] = Field(None, description="Recurrence pattern (daily, weekly, monthly)")


class GetCalendarEventsRequest(BaseModel):
    """Request model for getting calendar events."""
    start_date: str = Field(..., description="Start date in ISO format")
    end_date: str = Field(..., description="End date in ISO format")
    calendar_id: Optional[str] = Field(None, description="Specific calendar to query")


class DeleteEventRequest(BaseModel):
    """Request model for deleting a calendar event."""
    event_id: str = Field(..., description="ID of the event to delete")
    calendar_id: Optional[str] = Field(None, description="Specific calendar")


class SchedulingMCP:
    """
    MCP Server for handling scheduling actions like calendar management,
    appointment booking, and task scheduling.
    """

    def __init__(self):
        """Initialize the Scheduling MCP server."""
        self.mcp = FastMCP(
            name="scheduling-mcp",
            description="Handles scheduling actions like calendar management, appointment booking, and task scheduling"
        )

        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Store scheduled events/tasks
        self.events: Dict[str, Dict[str, Any]] = {}
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}

        # Register tools
        self._register_tools()

        # Start scheduler thread
        self.scheduler_thread = None
        self.running = False

    def _register_tools(self):
        """Register tools for the scheduling MCP server."""
        self.mcp.tool(
            name="create_calendar_event",
            description="Create a calendar event with attendees and details",
            input_model=CreateEventRequest
        )(self.create_calendar_event)

        self.mcp.tool(
            name="schedule_task",
            description="Schedule a task to run at a specific time",
            input_model=ScheduleTaskRequest
        )(self.schedule_task)

        self.mcp.tool(
            name="get_calendar_events",
            description="Get calendar events within a date range",
            input_model=GetCalendarEventsRequest
        )(self.get_calendar_events)

        self.mcp.tool(
            name="delete_calendar_event",
            description="Delete a calendar event",
            input_model=DeleteEventRequest
        )(self.delete_calendar_event)

    async def create_calendar_event(self, request: CreateEventRequest) -> Dict[str, Any]:
        """
        Create a calendar event with attendees and details.

        Args:
            request: Request containing event details

        Returns:
            Dictionary with event creation results
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="scheduling.create_event",
                target="calendar_system",
                approval_status="pending",
                result="in_progress",
                context_correlation=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "title": request.title,
                    "start_time": request.start_time,
                    "attendees_count": len(request.attendees) if request.attendees else 0
                }
            )

            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "scheduling.create_event",
                "calendar_system"
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="scheduling.create_event",
                    target="calendar_system",
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
                    "error": "Event creation blocked by safety boundaries",
                    "log_id": log_id
                }

            # Check if approval is required for this type of action
            requires_approval = safety_enforcer.check_action_allowed(
                safety_enforcer._get_boundary_for_action("scheduling.create_event"),
                {"action": "create_event", "title": request.title, "attendees": request.attendees}
            ).allowed == False

            if requires_approval:
                # Request human approval before creating event
                approval_result = safety_enforcer.request_human_approval(
                    safety_enforcer._get_boundary_for_action("scheduling.create_event"),
                    {"action": "create_event", "title": request.title, "attendees": request.attendees}
                )

                if not approval_result:
                    log_mcp_action(
                        action_type="scheduling.create_event",
                        target="calendar_system",
                        approval_status="pending_approval",
                        result="waiting_for_approval",
                        context_correlation=log_id,
                        additional_metadata={
                            "approval_required": True,
                            "title": request.title
                        }
                    )
                    return {
                        "success": False,
                        "error": "Event creation requires human approval",
                        "log_id": log_id,
                        "requires_approval": True
                    }

            # Generate a unique event ID
            import uuid
            event_id = f"event_{str(uuid.uuid4())[:8]}"

            # Create the event
            event = {
                "id": event_id,
                "title": request.title,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "attendees": request.attendees or [],
                "description": request.description or "",
                "created_at": datetime.now().isoformat(),
                "status": "confirmed"
            }

            # Store the event
            self.events[event_id] = event

            # Log successful completion
            log_mcp_action(
                action_type="scheduling.create_event",
                target="calendar_system",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "event_id": event_id,
                    "title": request.title,
                    "attendees_count": len(event["attendees"])
                }
            )

            return {
                "success": True,
                "event_id": event_id,
                "title": request.title,
                "start_time": request.start_time,
                "attendees": event["attendees"],
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error creating calendar event: {str(e)}")

            log_mcp_action(
                action_type="scheduling.create_event",
                target="calendar_system",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "title": getattr(request, 'title', 'unknown')
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    async def schedule_task(self, request: ScheduleTaskRequest) -> Dict[str, Any]:
        """
        Schedule a task to run at a specific time.

        Args:
            request: Request containing task scheduling details

        Returns:
            Dictionary with task scheduling results
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="scheduling.schedule_task",
                target="task_scheduler",
                approval_status="pending",
                result="in_progress",
                context_correlation=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "task_name": request.task_name,
                    "execution_time": request.execution_time,
                    "recurrence": request.recurrence
                }
            )

            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "scheduling.schedule_task",
                "task_scheduler"
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="scheduling.schedule_task",
                    target="task_scheduler",
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
                    "error": "Task scheduling blocked by safety boundaries",
                    "log_id": log_id
                }

            # Check if approval is required for this type of action
            requires_approval = safety_enforcer.check_action_allowed(
                safety_enforcer._get_boundary_for_action("scheduling.schedule_task"),
                {"action": "schedule_task", "task_name": request.task_name}
            ).allowed == False

            if requires_approval:
                # Request human approval before scheduling task
                approval_result = safety_enforcer.request_human_approval(
                    safety_enforcer._get_boundary_for_action("scheduling.schedule_task"),
                    {"action": "schedule_task", "task_name": request.task_name}
                )

                if not approval_result:
                    log_mcp_action(
                        action_type="scheduling.schedule_task",
                        target="task_scheduler",
                        approval_status="pending_approval",
                        result="waiting_for_approval",
                        context_correlation=log_id,
                        additional_metadata={
                            "approval_required": True,
                            "task_name": request.task_name
                        }
                    )
                    return {
                        "success": False,
                        "error": "Task scheduling requires human approval",
                        "log_id": log_id,
                        "requires_approval": True
                    }

            # Generate a unique task ID
            import uuid
            task_id = f"task_{str(uuid.uuid4())[:8]}"

            # Parse execution time
            execution_datetime = datetime.fromisoformat(request.execution_time.replace('Z', '+00:00'))

            # Create the scheduled task
            task = {
                "id": task_id,
                "name": request.task_name,
                "execution_time": request.execution_time,
                "recurrence": request.recurrence,
                "status": "scheduled",
                "created_at": datetime.now().isoformat()
            }

            # Store the task
            self.scheduled_tasks[task_id] = task

            # Log successful completion
            log_mcp_action(
                action_type="scheduling.schedule_task",
                target="task_scheduler",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "task_id": task_id,
                    "task_name": request.task_name,
                    "execution_time": request.execution_time
                }
            )

            return {
                "success": True,
                "task_id": task_id,
                "task_name": request.task_name,
                "execution_time": request.execution_time,
                "recurrence": request.recurrence,
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error scheduling task: {str(e)}")

            log_mcp_action(
                action_type="scheduling.schedule_task",
                target="task_scheduler",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "task_name": getattr(request, 'task_name', 'unknown')
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    async def get_calendar_events(self, request: GetCalendarEventsRequest) -> Dict[str, Any]:
        """
        Get calendar events within a date range.

        Args:
            request: Request containing date range and calendar ID

        Returns:
            Dictionary with calendar events
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="scheduling.get_events",
                target="calendar_system",
                approval_status="read_only",
                result="success",
                context_correlation=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "calendar_id": request.calendar_id
                }
            )

            # Since this is a read-only operation, no approval needed
            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "scheduling.get_events",
                "calendar_system"
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="scheduling.get_events",
                    target="calendar_system",
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
                    "error": "Event retrieval blocked by safety boundaries",
                    "log_id": log_id
                }

            # Parse date range
            start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))

            # Filter events within date range
            filtered_events = []
            for event_id, event in self.events.items():
                event_start = datetime.fromisoformat(event["start_time"].replace('Z', '+00:00'))

                if start_date <= event_start <= end_date:
                    filtered_events.append(event)

            return {
                "success": True,
                "events": filtered_events,
                "count": len(filtered_events),
                "start_date": request.start_date,
                "end_date": request.end_date,
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error getting calendar events: {str(e)}")

            log_mcp_action(
                action_type="scheduling.get_events",
                target="calendar_system",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "start_date": getattr(request, 'start_date', 'unknown'),
                    "end_date": getattr(request, 'end_date', 'unknown')
                }
            )

            return {
                "success": False,
                "error": str(e),
                "events": [],
                "count": 0,
                "log_id": None
            }

    async def delete_calendar_event(self, request: DeleteEventRequest) -> Dict[str, Any]:
        """
        Delete a calendar event.

        Args:
            request: Request containing event ID to delete

        Returns:
            Dictionary with deletion results
        """
        try:
            # Log the action for audit purposes
            from .audit_logger import log_mcp_action

            log_id = log_mcp_action(
                action_type="scheduling.delete_event",
                target="calendar_system",
                approval_status="pending",
                result="in_progress",
                context_correlation=f"delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "event_id": request.event_id,
                    "calendar_id": request.calendar_id
                }
            )

            # Validate safety boundaries
            from .safety_enforcer import get_safety_enforcer_instance
            safety_enforcer = get_safety_enforcer_instance()

            compliance = safety_enforcer.validate_safety_compliance(
                "scheduling.delete_event",
                "calendar_system"
            )

            if not compliance.get("boundaries_respected", True):
                log_mcp_action(
                    action_type="scheduling.delete_event",
                    target="calendar_system",
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
                    "error": "Event deletion blocked by safety boundaries",
                    "log_id": log_id
                }

            # Check if approval is required for this type of action
            requires_approval = safety_enforcer.check_action_allowed(
                safety_enforcer._get_boundary_for_action("scheduling.delete_event"),
                {"action": "delete_event", "event_id": request.event_id}
            ).allowed == False

            if requires_approval:
                # Request human approval before deleting event
                approval_result = safety_enforcer.request_human_approval(
                    safety_enforcer._get_boundary_for_action("scheduling.delete_event"),
                    {"action": "delete_event", "event_id": request.event_id}
                )

                if not approval_result:
                    log_mcp_action(
                        action_type="scheduling.delete_event",
                        target="calendar_system",
                        approval_status="pending_approval",
                        result="waiting_for_approval",
                        context_correlation=log_id,
                        additional_metadata={
                            "approval_required": True,
                            "event_id": request.event_id
                        }
                    )
                    return {
                        "success": False,
                        "error": "Event deletion requires human approval",
                        "log_id": log_id,
                        "requires_approval": True
                    }

            # Check if event exists
            if request.event_id not in self.events:
                return {
                    "success": False,
                    "error": f"Event with ID {request.event_id} not found",
                    "log_id": log_id
                }

            # Delete the event
            deleted_event = self.events.pop(request.event_id)

            # Log successful completion
            log_mcp_action(
                action_type="scheduling.delete_event",
                target="calendar_system",
                approval_status="approved",
                result="success",
                context_correlation=log_id,
                additional_metadata={
                    "event_id": request.event_id,
                    "deleted_title": deleted_event["title"]
                }
            )

            return {
                "success": True,
                "event_id": request.event_id,
                "deleted_title": deleted_event["title"],
                "log_id": log_id
            }

        except Exception as e:
            self.logger.error(f"Error deleting calendar event: {str(e)}")

            log_mcp_action(
                action_type="scheduling.delete_event",
                target="calendar_system",
                approval_status="not_applicable",
                result="failure",
                context_correlation=f"delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                additional_metadata={
                    "error": str(e),
                    "event_id": getattr(request, 'event_id', 'unknown')
                }
            )

            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get information about the scheduling MCP server.

        Returns:
            Dictionary with server information
        """
        return {
            "name": "Scheduling MCP Server",
            "version": "1.0.0",
            "description": "Handles scheduling actions like calendar management, appointment booking, and task scheduling",
            "responsibility": "Scheduling operations only",
            "available_tools": [
                "create_calendar_event",
                "schedule_task",
                "get_calendar_events",
                "delete_calendar_event"
            ],
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "stored_events_count": len(self.events),
            "scheduled_tasks_count": len(self.scheduled_tasks)
        }

    async def run(self, port: int = 8002):
        """
        Run the Scheduling MCP server.

        Args:
            port: Port to run the server on
        """
        self.logger.info(f"Starting Scheduling MCP Server on port {port}")
        await self.mcp.run(port=port)


def get_scheduling_mcp_instance() -> SchedulingMCP:
    """
    Factory function to get a SchedulingMCP instance.

    Returns:
        SchedulingMCP instance
    """
    return SchedulingMCP()


if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Scheduling MCP Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to run the server on")
    args = parser.parse_args()

    async def main():
        sched_mcp = get_scheduling_mcp_instance()

        print("Scheduling MCP Server Info:")
        info = sched_mcp.get_server_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

        print(f"\nStarting server on port {args.port}...")
        await sched_mcp.run(port=args.port)

    # Run the server
    asyncio.run(main())