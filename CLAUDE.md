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
1. **elpyfi-core**: Core trading engine ✓ (moved to services/)
2. **elpyfi-ai**: AI signal analysis ✓ (moved to services/)
3. **elpyfi-api**: REST/WebSocket API ✓ (moved to services/)
4. **elpyfi-dashboard**: Web UI ✓ (moved to services/)

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