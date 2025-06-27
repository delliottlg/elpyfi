#!/usr/bin/env python3
"""
MCP Server for PM Claude - Fixed version
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server.app import App
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP app
app = App("pm-claude")

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from service_orchestrator import ServiceOrchestrator
from test_runner import ServiceTestRunner

# Global instances
orchestrator = None
test_runner = None


def init_orchestrator():
    """Initialize orchestrator if needed"""
    global orchestrator, test_runner
    if orchestrator is None:
        base_path = Path(__file__).parent.parent
        orchestrator = ServiceOrchestrator(base_path)
        orchestrator.load_config()
        try:
            orchestrator.secrets_manager.load_secrets()
        except Exception as e:
            logger.warning(f"Could not load secrets: {e}")
        test_runner = ServiceTestRunner(base_path)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="start_services",
            description="Start ElPyFi services. Can start all services or specific ones.",
            inputSchema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of services to start. If empty, starts all."
                    }
                }
            }
        ),
        types.Tool(
            name="stop_services",
            description="Stop ElPyFi services",
            inputSchema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of services to stop. If empty, stops all."
                    }
                }
            }
        ),
        types.Tool(
            name="service_status",
            description="Get the current status of all services",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="run_tests",
            description="Run tests for a service or all services",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service to test. If not specified, runs all tests."
                    }
                }
            }
        ),
        types.Tool(
            name="list_services",
            description="List all available services",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls"""
    init_orchestrator()
    
    try:
        if name == "start_services":
            services = arguments.get("services", []) if arguments else []
            
            # Start services in thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, orchestrator.start_all, services)
            
            # Get status
            status = orchestrator.status()
            lines = ["Started services:\n"]
            for service_id, info in status.items():
                if info['status'] == 'running':
                    lines.append(f"✅ {info['name']} (PID: {info['pid']})")
            
            return [types.TextContent(type="text", text="\n".join(lines))]
        
        elif name == "stop_services":
            services = arguments.get("services", []) if arguments else []
            
            if services:
                for service in services:
                    orchestrator.stop_service(service)
                message = f"Stopped services: {', '.join(services)}"
            else:
                orchestrator.stop_all()
                message = "All services stopped"
            
            return [types.TextContent(type="text", text=message)]
        
        elif name == "service_status":
            status = orchestrator.status()
            
            lines = ["Service Status:\n"]
            lines.append(f"{'Service':<25} {'Status':<10} {'PID':<8}")
            lines.append("-" * 50)
            
            for service_id, info in status.items():
                lines.append(
                    f"{info['name']:<25} {info['status']:<10} {info['pid'] or '-':<8}"
                )
            
            return [types.TextContent(type="text", text="\n".join(lines))]
        
        elif name == "run_tests":
            service = arguments.get("service") if arguments else None
            
            if service:
                test_method = getattr(test_runner, f"test_{service.replace('-', '_')}", None)
                if test_method:
                    result = test_method()
                    status = "✅ PASSED" if result['success'] else "❌ FAILED"
                    message = f"{service}: {status}"
                else:
                    message = f"Unknown service: {service}"
            else:
                success = test_runner.run_all_tests()
                message = "Test run complete. All tests passed!" if success else "Some tests failed."
            
            return [types.TextContent(type="text", text=message)]
        
        elif name == "list_services":
            lines = ["Available services:\n"]
            for service_id, service in orchestrator.services.items():
                lines.append(f"- {service_id}: {service.name}")
            
            return [types.TextContent(type="text", text="\n".join(lines))]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


if __name__ == "__main__":
    import mcp.server.stdio
    
    # Run the app using stdio transport
    mcp.server.stdio.run(app)