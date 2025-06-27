# elPyFi API Setup Guide

## Overview
The elPyFi API service is managed by PM Claude, the orchestrator for the entire elPyFi trading system. This guide covers both standalone development and PM Claude-managed deployment.

## Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- PM Claude (for managed deployment)

## Setup Methods

### Method 1: PM Claude Integration (Recommended)
When running as part of the PM Claude system:

```bash
# The API uses PM Claude's shared virtual environment
# Located at: /Users/d/Documents/projects/elpyfi-pm-claude/venv

# Start the API service via PM Claude
./pm-claude start api

# Or start all services
./pm-claude start

# Check service status
./pm-claude status
```

The API will run on port 9002 when managed by PM Claude.

### Method 2: Standalone Development
For development outside of PM Claude:

```bash
# Use PM Claude's shared virtual environment
# Activate the shared environment:
source /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt
```

## Documentation Tools

We're using MkDocs with Material theme for fancy documentation:
- **MkDocs**: Static site generator for documentation
- **mkdocs-material**: Material Design theme
- **mkdocstrings**: Auto-generate docs from Python docstrings
- **Google style docstrings**: For consistency

## Project Structure
```
elpyfi-api/
├── Documentation/          # All documentation
│   ├── setup-guide.md     # This file
│   └── api/               # API documentation
├── docs/                  # MkDocs source files
│   ├── index.md
│   └── api-reference.md
├── mkdocs.yml            # MkDocs configuration
├── src/                  # Source code
│   └── elpyfi_api/
│       ├── __init__.py
│       ├── main.py
│       ├── server.py
│       ├── auth.py
│       ├── streams.py
│       ├── models.py
│       └── config.py
├── tests/                # Test files
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── Dockerfile           # Container configuration
```

## Configuration

### Environment Variables
Create a `.env` file in the service directory:
```bash
# Database connection
ELPYFI_DATABASE_URL=postgresql://elpyfi:password@localhost/elpyfi

# API configuration
ELPYFI_PORT=9002
ELPYFI_API_KEYS=your_api_key_here
ELPYFI_CORS_ORIGINS=http://localhost:3000

# When using PM Claude, these are managed via config/secrets.yaml
```

### PM Claude Configuration
When using PM Claude, configuration is centralized:
- Service config: `config/services.yaml`
- Secrets: `config/secrets.yaml` (git-ignored)
- PM Claude handles environment variable injection

## Running the API

### Via PM Claude
```bash
# Start just the API
./pm-claude start api

# View logs
./pm-claude logs api

# Restart if needed
./pm-claude restart api
```

### Standalone
```bash
# Development mode with auto-reload
uvicorn src.elpyfi_api.main:app --reload --host 0.0.0.0 --port 9002

# Or using Python module
python -m src.elpyfi_api.main
```

## Testing
```bash
# Run tests (uses PM Claude's shared venv if available)
pytest

# With coverage
pytest --cov=src/elpyfi_api

# Via PM Claude test runner
./src/test_runner.py --service api
```

## API Endpoints
- REST API: `http://localhost:9002`
- WebSocket: `ws://localhost:9002/ws`
- API Docs: `http://localhost:9002/docs`

## Next Steps
1. Configure database connection
2. Set up API keys for authentication
3. Test the endpoints
4. Connect web dashboard or other consumers
5. Monitor via PM Claude's health checks