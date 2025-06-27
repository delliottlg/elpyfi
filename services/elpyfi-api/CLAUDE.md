# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
elPyFi API is a minimal, read-only REST/WebSocket API service that provides real-time access to trading data from the elPyFi trading engine. The API is designed to be stateless, lightweight (~300 lines total), and focuses on data relay without business logic.

## Virtual Environment Setup
**IMPORTANT**: Always work within the virtual environment:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
```

## Development Commands

### Running the API
```bash
# Development mode with auto-reload
uvicorn src.elpyfi_api.main:app --reload --host 0.0.0.0 --port 9002

# Or using Python module
python -m src.elpyfi_api.main
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/elpyfi_api
```

### Documentation
```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Architecture

### Core Modules
- **server.py**: FastAPI application setup and middleware configuration
- **auth.py**: API key authentication middleware
- **streams.py**: WebSocket connection handling and event streaming
- **models.py**: Pydantic models for API responses and events
- **config.py**: Environment configuration using python-dotenv
- **main.py**: Application entry point with Uvicorn server

### Database Integration
- Uses PostgreSQL with asyncpg for async operations
- Implements NOTIFY/LISTEN for real-time event streaming
- Read-only access - no write operations

### API Design Principles
1. **Read-Only**: No POST/PUT/DELETE endpoints for trading operations
2. **Event Streaming First**: REST for snapshots, WebSocket for real-time updates
3. **Stateless**: No session management or caching
4. **Simple Auth**: API key-based authentication via headers

## Key Implementation Notes

### WebSocket Streams
- Main stream at `/ws` for all events
- Filtered streams: `/ws/signals` and `/ws/trades`
- Automatic reconnection handling on client disconnect

### Error Handling
- Use FastAPI's HTTPException for REST endpoints
- WebSocket disconnections should be handled gracefully
- All database errors should return appropriate HTTP status codes

### Performance Considerations
- Use PostgreSQL connection pooling
- Implement backpressure for WebSocket streams
- Keep response payloads minimal

## Documentation Standards
- Use Google-style docstrings for all functions and classes
- Document all API endpoints with OpenAPI schemas
- Keep inline comments minimal - code should be self-documenting

## PM Claude Status
*Updated by PM Claude on 2025-06-25 23:26:53*

- **Service Status**: stopped

### Integration with PM Claude
This service is managed by PM Claude and uses:
- Shared Python 3.11 virtual environment
- Centralized secrets management
- Automated health monitoring
- Unified test runner

### Known Issues
- [RESOLVED] [5f943e8d] Remove old local venv and use PM Claude's shared environment
  - Delete the local venv/ directory. When running Python, use /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/python or activate the shared venv with: source /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/activate
- [OPEN] [d3a61355] Fix asyncpg connection cleanup
  - Ensure database connections are properly closed after each request to prevent connection leaks. Add proper cleanup in get_db() dependency. ~5 lines.
- [RESOLVED] [53e8d644] Add limit parameter validation to /signals/recent endpoint
  - Currently has no bounds checking. Cap at reasonable max (like 1000) to prevent memory issues. 3-line fix.
- [OPEN] [2a39ccce] Add database connectivity check to /health endpoint
  - Currently just returns OK. Should do a simple SELECT 1 query to verify database is actually accessible. ~10 lines.
- [RESOLVED] [64885e18] Fix Pydantic v2 deprecation warning in config.py
  - Update BaseSettings usage to new ConfigDict pattern. Quick 5-line fix.
- [RESOLVED] [54d618c6] Clean up .env file to only include ELPYFI_ prefixed variables
  - Remove all the exposed API keys (OpenAI, Anthropic, Alpaca, etc) that belong to other services. PM Claude's secrets.yaml handles those. Only keep ELPYFI_DATABASE_URL, ELPYFI_API_KEYS, ELPYFI_CORS_ORIGINS, ELPYFI_PORT
