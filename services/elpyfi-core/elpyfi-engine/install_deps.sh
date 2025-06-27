#!/bin/bash
# Install dependencies in virtual environment

cd "$(dirname "$0")"
source venv/bin/activate
pip install -r requirements.txt