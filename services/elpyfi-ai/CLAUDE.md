# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

elpyfi-ai is an AI-powered trading signal analysis service designed to interpret and explain trading decisions. The project is currently in the design phase with implementation planned.

## Architecture

The service is designed as a separate microservice that:
- Receives trading signals from the main trading engine
- Analyzes signals using rule-based logic (V1), LLMs (V2), or custom ML models (V3)
- Returns human-readable explanations and confidence scores
- Never directly executes trades (advisory role only)

Planned structure:
- `analyzer.py` - Core signal interpretation logic
- `explainer.py` - Converts analysis into human-readable explanations
- `models.py` - Pydantic models for Signal, Decision, and related data types
- `main.py` - FastAPI server with `/analyze` and `/backtest-decision` endpoints

## Development Setup

Since the project is in early stages, when implementing:

1. Create a `requirements.txt` with core dependencies:
   ```
   fastapi
   uvicorn
   pydantic
   anthropic  # for Claude API
   python-dotenv  # for environment variables
   ```

2. Use Python 3.11 (shared PM Claude venv)

3. Follow the API design from `designidea.md`:
   - `POST /analyze` - accepts Signal, returns Decision
   - `POST /backtest-decision` - for historical analysis

## Key Design Constraints

1. **Pattern Day Trading (PDT) Awareness**: The system must consider PDT rules when making recommendations
2. **Safety First**: AI provides recommendations only, never direct trade execution
3. **Resource Separation**: Designed to run on separate infrastructure from the trading engine
4. **Stateless Design**: Each analysis request should be independent

## Implementation Guidelines

When implementing features:
- Start with V1 (rule-based) implementation before adding LLM capabilities
- Use Pydantic for all data models to ensure type safety
- Keep signal analysis logic separate from explanation generation
- Design for testability - pure functions where possible
- Consider mock trading data for development/testing

## Environment Variables

When setting up configuration:
- `ANTHROPIC_API_KEY` - for Claude API access (V2)
- `OPENAI_API_KEY` - optional, for GPT models (V2)
- `TRADING_ENGINE_URL` - URL of the main trading system (if needed)

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
- [RESOLVED] [8ede2843] Add proper logging configuration instead of print statements
  - Replace any print() statements with proper logging using Python's logging module. Configure appropriate log levels (DEBUG, INFO, ERROR) for better production debugging and monitoring.
- [OPEN] [d2926233] Add environment variable validation on startup
  - Add validation for required env vars like ANTHROPIC_API_KEY in ai_analyzer.py. Should fail fast with clear error message if API keys missing rather than runtime failures. ~10 lines.
- [OPEN] [59520bf4] Update Pydantic .dict() to .model_dump() for v2 compatibility
  - In main.py lines 157-158, using deprecated .dict() method. Update to .model_dump() to avoid deprecation warnings and prepare for Pydantic v2. Simple 2-line change.
- [OPEN] [bae0c1a4] Remove old local venv and use PM Claude's shared environment
  - Delete the local venv/ directory. When running Python, use /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/python or activate the shared venv with: source /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/activate
