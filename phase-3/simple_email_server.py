#!/usr/bin/env python3
"""
Simple script to start the email automation server
"""
import asyncio
from communication_mcp import get_communication_mcp_instance


async def main():
    print("Starting Communication MCP Server for Email Automation...")
    print("Port: 8000")

    comm_mcp = get_communication_mcp_instance()

    print("Communication MCP Server Info:")
    info = comm_mcp.get_server_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print(f"\nStarting server on port 8000...")
    print("Server is now ready to handle email requests...")
    print("Press Ctrl+C to stop the server")

    # Run the server
    await comm_mcp.run(port=8000)


if __name__ == "__main__":
    # Run the server directly without nested asyncio
    import sys
    if sys.platform.startswith('win'):
        # Windows event loop policy
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        loop.close()