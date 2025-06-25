# ElPyFi PM Claude

The project manager and orchestrator for the ElPyFi trading system ecosystem.

## Overview

PM Claude is a centralized control system that manages:
- Configuration distribution across services
- Service orchestration and startup sequences
- Health monitoring and status reporting
- Context maintenance (CLAUDE.md updates)
- Natural language interface for system control

## Architecture

```
elpyfi-pm-claude/
├── config/           # Configuration files
├── src/              # PM Claude source code
├── services/         # Managed service repos (git ignored)
└── mcp/              # MCP server implementation
```

## Quick Start

1. Clone this repository
2. Clone service repositories into `services/` directory:
   ```bash
   cd services
   git clone [elpyfi-core-repo] elpyfi-core
   git clone [elpyfi-ai-repo] elpyfi-ai
   git clone [elpyfi-api-repo] elpyfi-api
   git clone [elpyfi-dashboard-repo] elpyfi-dashboard
   ```

3. Configure services in `config/services.yaml`
4. Add secrets to `config/secrets.yaml` (git ignored)

## Usage

### As MCP Tool
```bash
# Start all services
pm-claude start all

# Check status
pm-claude status

# View logs
pm-claude logs --service=ai
```

### Natural Language Commands
- "Start trading system in dev mode"
- "Show me the current status"
- "Why is the AI service not responding?"
- "Shutdown all services"

## Services Managed

- **elpyfi-core**: Core trading engine
- **elpyfi-ai**: AI signal analysis
- **elpyfi-api**: REST/WebSocket API
- **elpyfi-dashboard**: Web UI

## Configuration

See `config/services.yaml.example` for service configuration format.