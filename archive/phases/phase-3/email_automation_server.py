#!/usr/bin/env python3
"""
Production-ready email automation server
"""
import asyncio
import signal
import sys
from communication_mcp import get_communication_mcp_instance


class EmailAutomationServer:
    def __init__(self):
        self.comm_mcp = None
        self.shutdown_event = asyncio.Event()

    def signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.shutdown_event.set()

    async def run_server(self, port=8000):
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        print("Starting Communication MCP Server for Email Automation...")
        print(f"Port: {port}")

        self.comm_mcp = get_communication_mcp_instance()

        print("Communication MCP Server Info:")
        info = self.comm_mcp.get_server_info()
        for key, value in info.items():
            print(f"  {key}: {value}")

        print(f"\nStarting server on port {port}...")
        print("Server is now ready to handle email requests...")
        print("Press Ctrl+C to stop the server")

        # Create a task to run the server
        server_task = asyncio.create_task(self.comm_mcp.run(port=port))

        # Wait for shutdown event
        await self.shutdown_event.wait()

        print("Shutting down server...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

        print("Server stopped.")


async def main():
    server = EmailAutomationServer()
    await server.run_server(port=8000)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer interrupted by user.")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)