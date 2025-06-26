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

### Command Line Interface
```bash
# Start all services
./pm-claude start

# Start specific services
./pm-claude start elpyfi-core elpyfi-ai

# Check status
./pm-claude status

# Stop all services
./pm-claude stop

# Restart services
./pm-claude restart
```

### MCP Integration (Natural Language)

Configure PM Claude as an MCP server in Claude Desktop or CLI (see docs/mcp-usage.md), then use natural language:

- "Start the trading system"
- "Show me the current status of all services"
- "Run tests for the AI service"
- "Stop everything"
- "Which services are currently running?"

## Services Managed

- **elpyfi-core**: Core trading engine
- **elpyfi-ai**: AI signal analysis
- **elpyfi-api**: REST/WebSocket API
- **elpyfi-dashboard**: Web UI

## Configuration

See `config/services.yaml.example` for service configuration format.