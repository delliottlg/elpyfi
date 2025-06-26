# PM Claude MCP Server Usage

## Installation

1. Ensure you have Claude Desktop or Claude CLI configured for MCP
2. Add PM Claude to your MCP configuration:

### For Claude Desktop (macOS)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pm-claude": {
      "command": "/path/to/elpyfi-pm-claude/mcp-pm-claude"
    }
  }
}
```

### For Claude CLI

Edit `~/.config/claude/mcp_servers.json`:

```json
{
  "pm-claude": {
    "command": "/path/to/elpyfi-pm-claude/mcp-pm-claude"
  }
}
```

## Available Commands

Once configured, you can use natural language to control your services:

### Service Management
- "Start all services"
- "Start just the AI and API services"
- "Stop everything"
- "Show me the status of all services"
- "Restart the dashboard"

### Testing
- "Run all tests"
- "Test the AI service"
- "Run core engine tests"

### Configuration
- "Reload the configuration"
- "List all available services"

### Monitoring
- "Show me service status with memory usage"
- "Which services are currently running?"

## Example Conversations

**Starting services:**
```
You: Start the trading system
Claude: I'll start all the ElPyFi services for you.

Started services:
✅ Core Trading Engine (PID: 12345)
✅ AI Analysis Service (PID: 12346)
✅ REST/WebSocket API (PID: 12347)
✅ Web Dashboard (PID: 12348)
```

**Checking status:**
```
You: How are my services doing?
Claude: I'll check the status of all services.

Service Status:
Service                   Status     PID      Uptime     Memory    
----------------------------------------------------------------------
Core Trading Engine       ✅ running  12345    2h 15m     125.3 MB  
AI Analysis Service       ✅ running  12346    2h 15m     248.7 MB  
REST/WebSocket API        ✅ running  12347    2h 14m     87.2 MB   
Web Dashboard            ✅ running  12348    2h 14m     156.4 MB  
```

**Running tests:**
```
You: Test the AI service
Claude: I'll run the tests for the AI service.

elpyfi-ai: ✅ PASSED
```

## Troubleshooting

If the MCP server doesn't work:

1. Check that the path in your config is correct
2. Ensure the script is executable: `chmod +x mcp-pm-claude`
3. Test manually: `./mcp-pm-claude` (should wait for input)
4. Check Claude's MCP logs for errors

## Benefits

Using PM Claude through MCP gives you:
- Natural language control over your services
- No need to remember CLI commands
- Context-aware assistance (Claude understands your system)
- Integrated with your Claude workflow