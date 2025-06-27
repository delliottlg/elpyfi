#!/usr/bin/env python3
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

# Create server
server = Server("test-pm-claude")

@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="test",
            description="Test tool",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    return [TextContent(type="text", text=f"Tool {name} called")]

async def main():
    async with server.run():
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())