# PM Claude

Service orchestrator that dispatches Claude agents to fix issues.

## Commands

```bash
# Service management
./pm-claude start|stop|status|restart [service-name]

# Issue tracking  
./pm-issue list                                    # List all issues
./pm-issue add <service> <title> -d <description>  # Add new issue
./pm-issue update <id> --status resolved           # Update issue

# Agent dispatching
./pm-agent dispatch <service> <task>               # Dispatch single agent
./pm-agent status                                  # Show active agents
./pm-agent logs <agent-id>                        # View agent logs
```

## Services

- **elpyfi-core**: Trading engine
- **elpyfi-api**: REST/WebSocket API  
- **elpyfi-ai**: AI analysis
- **elpyfi-dashboard**: Web UI

## Quick Start

```bash
# Check what needs fixing
./pm-issue list

# Dispatch agent to fix issue
./pm-agent dispatch elpyfi-api "Fix connection pooling"

# Monitor progress
./pm-agent status
```