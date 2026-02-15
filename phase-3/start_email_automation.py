#!/usr/bin/env python3
"""
Start the email automation server
"""
import asyncio
import argparse
from communication_mcp import get_communication_mcp_instance


async def main():
    parser = argparse.ArgumentParser(description="Communication MCP Server for Email Automation")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()

    print("Starting Communication MCP Server for Email Automation...")
    print(f"Port: {args.port}")

    comm_mcp = get_communication_mcp_instance()

    print("Communication MCP Server Info:")
    info = comm_mcp.get_server_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print(f"\nStarting server on port {args.port}...")
    print("Server is now ready to handle email requests...")

    await comm_mcp.run(port=args.port)


if __name__ == "__main__":
    asyncio.run(main())