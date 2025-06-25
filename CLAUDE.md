# PM Claude System Context

## Current Status
- **Last Updated**: 2025-01-25
- **Status**: Initial setup phase
- **Services**: Not yet running

## Project Structure
```
elpyfi-pm-claude/
├── config/              # Service and secrets configuration
├── src/                 # PM Claude implementation
├── services/            # Managed service repositories
└── mcp/                 # MCP server implementation
```

## Managed Services
1. **elpyfi-core**: Core trading engine (not cloned)
2. **elpyfi-ai**: AI signal analysis (not cloned)
3. **elpyfi-api**: REST/WebSocket API (not cloned)
4. **elpyfi-dashboard**: Web UI (not cloned)

## Next Steps
1. Implement basic service orchestration
2. Create MCP server structure
3. Build health monitoring system
4. Implement secrets distribution

## Configuration Files
- `config/services.yaml`: Service definitions and dependencies
- `config/secrets.yaml`: Sensitive configuration (git-ignored)
- `.gitignore`: Excludes service repos and secrets

## Key Design Decisions
- Using Option C: Independent repos with PM config
- Services live in `services/` subdirectory for Claude Code access
- Git ignores all service repositories
- MCP server implementation for natural language control