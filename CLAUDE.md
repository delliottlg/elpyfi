# PM Claude

Service orchestrator and agent dispatcher for the ElPyFi trading system.

## Available Commands

```bash
# Service management
./pm-claude start|stop|status|restart [services]

# Issue tracking
./pm-issue list                                    # List all issues
./pm-issue add <service> <title> -d <description>  # Add new issue  
./pm-issue update <id> --status resolved           # Update issue

# Agent dispatching
./pm-agent dispatch <service> <task>               # Dispatch single agent
./pm-agent status                                  # Show active agents
./pm-agent logs <agent-id>                        # View agent logs
```

## Architecture
```
PM Claude
├── Service Orchestrator (process management)
├── Issue Tracker (tracks problems to fix)
├── Agent Orchestrator (dispatches Claude instances)
└── Test Runner (unified testing)
```

## Services

- **elpyfi-core**: Trading engine at `services/elpyfi-core/`
- **elpyfi-api**: REST/WebSocket API at `services/elpyfi-api/`
- **elpyfi-ai**: AI analysis at `services/elpyfi-ai/`
- **elpyfi-dashboard**: Web UI at `services/elpyfi-dashboard/`

## Known Issues
- Services require PostgreSQL database 'elpyfi' to run
- Each service needs its own venv (currently using shared)