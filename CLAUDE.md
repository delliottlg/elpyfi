# PM Claude System Context

*Last Updated: 2025-06-25 18:26:24*

## System Status
- **Services Running**: 0/4
- **Overall Health**: ✅ Healthy
- **Environment**: development
- **Python Version**: 3.11.13
- **Shared venv**: /Users/d/Documents/projects/elpyfi-pm-claude/venv

## Services Overview

| Service | Status | PID | Uptime | Memory | Health |
|---------|--------|-----|--------|--------|--------|
| Core Trading Engine | stopped | - | - | - | ✅ |
| AI Analysis Service | stopped | - | - | - | ✅ |
| REST/WebSocket API | stopped | - | - | - | ✅ |
| Web Dashboard | stopped | - | - | - | ✅ |

## Recent Events
- System initialized
- Services configured with shared Python 3.11 environment
- MCP server available for natural language control

## Configuration
- **Config Directory**: `config/`
- **Services Config**: `config/services.yaml`
- **Secrets**: `config/secrets.yaml` (git-ignored)

## Available Commands

### CLI:
```bash
./pm-claude start|stop|status|restart [services]
./src/test_runner.py  # Run all tests
```

### MCP (Natural Language):
- "Start the trading system"
- "Show me service status"
- "Run tests for the AI service"
- "Stop all services"

## Architecture
```
PM Claude
├── Service Orchestrator (process management)
├── Secrets Manager (config distribution)
├── Health Monitor (auto-recovery)
├── Test Runner (unified testing)
├── MCP Server (natural language)
└── CLAUDE.md Updater (context maintenance)
```

## Repository Information
- **Current Branch**: main
- **Last Commit**: e0489327 - Implement MCP server for natural language control

- Created MCP server with 7 tools:
  - start_services: Start all or specific services
  - stop_services: Stop all or specific services
  - service_status: Get status, PID, uptime, memory
  - run_tests: Run tests for services
  - view_logs: View service logs (placeholder)
  - reload_config: Reload configuration files
  - list_services: Show available services

- Added mcp-pm-claude launcher script
- Created mcp.json configuration
- Added comprehensive MCP usage documentation
- Total: ~280 lines of clean, async MCP code

Now PM Claude can be controlled via natural language in Claude Desktop/CLI\!

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
- **Modified Files**: 1