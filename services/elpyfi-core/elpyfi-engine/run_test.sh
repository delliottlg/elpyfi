#!/bin/bash
# Run test with shared PM Claude venv

# Change to script directory
cd "$(dirname "$0")"

# Use shared venv python
../../../venv/bin/python test_engine.py