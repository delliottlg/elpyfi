#!/usr/bin/env python3
"""
MCP Server for PM Claude
Provides natural language interface to service orchestration
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, LoggingLevel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from service_orchestrator import ServiceOrchestrator
from secrets_manager import SecretsManager
from test_runner import ServiceTestRunner


# Initialize server
server = Server("pm-claude")

# Global instances
orchestrator: Optional[ServiceOrchestrator] = None
test_runner: Optional[ServiceTestRunner] = None


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="start_services",
            description="Start ElPyFi services. Can start all services or specific ones.",
            inputSchema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of services to start (e.g., ['elpyfi-core', 'elpyfi-ai']). If empty, starts all services."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="stop_services",
            description="Stop ElPyFi services. Can stop all services or specific ones.",
            inputSchema={
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of services to stop. If empty, stops all services."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="service_status",
            description="Get the current status of all services including PID, uptime, and memory usage.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="run_tests",
            description="Run tests for a specific service or all services.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service to test (e.g., 'elpyfi-ai'). If not specified, runs all tests."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="view_logs",
            description="View recent logs from a service's output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service to view logs for (e.g., 'elpyfi-core')"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of recent lines to show (default: 50)"
                    }
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="reload_config",
            description="Reload configuration files (services.yaml and secrets.yaml).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_services",
            description="List all available services and their configuration.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[TextContent]:
    """Handle tool calls"""
    global orchestrator, test_runner
    
    # Initialize if needed
    if orchestrator is None:
        base_path = Path(__file__).parent.parent
        orchestrator = ServiceOrchestrator(base_path)
        orchestrator.load_config()
        orchestrator.secrets_manager.load_secrets()
        test_runner = ServiceTestRunner(base_path)
    
    try:
        if name == "start_services":
            services = arguments.get("services", []) if arguments else []
            
            # Start services
            await asyncio.get_event_loop().run_in_executor(
                None, orchestrator.start_all, services
            )
            
            # Get status
            status = orchestrator.status()
            
            # Format response
            lines = ["Started services:\n"]
            for service_id, info in status.items():
                if info['status'] == 'running':
                    lines.append(f"✅ {info['name']} (PID: {info['pid']})")
            
            return [TextContent(type="text", text="\n".join(lines))]
        
        elif name == "stop_services":
            services = arguments.get("services", []) if arguments else []
            
            if services:
                # Stop specific services
                for service in services:
                    await asyncio.get_event_loop().run_in_executor(
                        None, orchestrator.stop_service, service
                    )
                message = f"Stopped services: {', '.join(services)}"
            else:
                # Stop all
                await asyncio.get_event_loop().run_in_executor(
                    None, orchestrator.stop_all
                )
                message = "All services stopped"
            
            return [TextContent(type="text", text=message)]
        
        elif name == "service_status":
            status = orchestrator.status()
            
            lines = ["Service Status:\n"]
            lines.append(f"{'Service':<25} {'Status':<10} {'PID':<8} {'Uptime':<10} {'Memory':<10}")
            lines.append("-" * 70)
            
            for service_id, info in status.items():
                status_emoji = {
                    'running': '✅',
                    'stopped': '⏹️',
                    'failed': '❌'
                }.get(info['status'], '❓')
                
                lines.append(
                    f"{info['name']:<25} {status_emoji} {info['status']:<8} "
                    f"{info['pid'] or '-':<8} {info['uptime'] or '-':<10} "
                    f"{info['memory'] or '-':<10}"
                )
            
            return [TextContent(type="text", text="\n".join(lines))]
        
        elif name == "run_tests":
            service = arguments.get("service") if arguments else None
            
            # Run tests
            if service:
                # Run specific service test
                test_method = getattr(test_runner, f"test_{service.replace('-', '_')}", None)
                if test_method:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, test_method
                    )
                    status = "✅ PASSED" if result['success'] else "❌ FAILED"
                    message = f"{service}: {status}\n"
                    if not result['success']:
                        message += f"Error: {result['error'][:200]}..."
                else:
                    message = f"Unknown service: {service}"
            else:
                # Run all tests
                success = await asyncio.get_event_loop().run_in_executor(
                    None, test_runner.run_all_tests
                )
                message = "Test run complete. See output above."
            
            return [TextContent(type="text", text=message)]
        
        elif name == "view_logs":
            service = arguments["service"]
            lines = arguments.get("lines", 50)
            
            # This is a placeholder - in real implementation, 
            # we'd capture service output or read from log files
            return [TextContent(
                type="text", 
                text=f"Log viewing for {service} not yet implemented. "
                     f"Would show last {lines} lines of output."
            )]
        
        elif name == "reload_config":
            orchestrator.load_config()
            orchestrator.secrets_manager.load_secrets()
            return [TextContent(type="text", text="Configuration reloaded successfully")]
        
        elif name == "list_services":
            lines = ["Available services:\n"]
            
            for service_id, service in orchestrator.services.items():
                lines.append(f"\n{service_id}:")
                lines.append(f"  Name: {service.name}")
                lines.append(f"  Path: {service.path}")
                lines.append(f"  Command: {' '.join(service.command)}")
                lines.append(f"  Dependencies: {', '.join(service.depends_on) or 'none'}")
            
            return [TextContent(type="text", text="\n".join(lines))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    # Run the server using stdin/stdout streams
    async with server.run(
        connection_type="stdio",
        initialization_options=InitializationOptions(
            server_name="pm-claude",
            server_version="1.0.0",
            logging_level=LoggingLevel.INFO
        )
    ) as _:
        # Server will run until terminated
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())