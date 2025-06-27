#!/usr/bin/env python3
"""
Simple MCP Server for PM Claude
"""

import sys
import json
import asyncio
from pathlib import Path

# Basic stdio communication
async def read_json_line():
    """Read a line from stdin and parse as JSON"""
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    if not line:
        return None
    return json.loads(line)

def write_json_line(data):
    """Write JSON to stdout"""
    sys.stdout.write(json.dumps(data) + "\n")
    sys.stdout.flush()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from service_orchestrator import ServiceOrchestrator
from test_runner import ServiceTestRunner

# Initialize
base_path = Path(__file__).parent.parent
orchestrator = ServiceOrchestrator(base_path)
orchestrator.load_config()
test_runner = ServiceTestRunner(base_path)

async def handle_request(request):
    """Handle JSON-RPC request"""
    method = request.get("method")
    params = request.get("params", {})
    id = request.get("id")
    
    try:
        if method == "initialize":
            # Return capabilities
            result = {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": True
                },
                "serverInfo": {
                    "name": "pm-claude",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            # List available tools
            result = {
                "tools": [
                    {
                        "name": "start_services",
                        "description": "Start ElPyFi services",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "services": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            }
                        }
                    },
                    {
                        "name": "stop_services",
                        "description": "Stop ElPyFi services",
                        "inputSchema": {"type": "object"}
                    },
                    {
                        "name": "service_status",
                        "description": "Get service status",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        
        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "start_services":
                services = tool_args.get("services", [])
                orchestrator.start_all(services)
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Started services: {', '.join(services) if services else 'all'}"
                        }
                    ]
                }
            
            elif tool_name == "stop_services":
                orchestrator.stop_all()
                result = {
                    "content": [
                        {"type": "text", "text": "All services stopped"}
                    ]
                }
            
            elif tool_name == "service_status":
                status = orchestrator.status()
                lines = []
                for sid, info in status.items():
                    lines.append(f"{info['name']}: {info['status']}")
                result = {
                    "content": [
                        {"type": "text", "text": "\n".join(lines)}
                    ]
                }
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Send response
        response = {
            "jsonrpc": "2.0",
            "id": id,
            "result": result
        }
        
    except Exception as e:
        # Send error
        response = {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
    
    write_json_line(response)

async def main():
    """Main loop"""
    # Load secrets
    try:
        orchestrator.secrets_manager.load_secrets()
    except:
        pass
    
    while True:
        request = await read_json_line()
        if request is None:
            break
        await handle_request(request)

if __name__ == "__main__":
    asyncio.run(main())