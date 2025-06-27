#!/bin/bash

echo "🛑 Stopping all elpyfi services..."

# Kill specific known PIDs
echo "Stopping API service (PID 38188)..."
kill -TERM 38188 2>/dev/null || true

echo "Stopping Dashboard (PID 35826)..."
kill -TERM 35826 2>/dev/null || true

echo "Stopping Core Engine (PID 87914)..."
kill -TERM 87914 2>/dev/null || true

# Also kill by pattern to catch any we missed
echo "Stopping any remaining elpyfi processes..."
pkill -f "elpyfi" 2>/dev/null || true
pkill -f "engine.py" 2>/dev/null || true
pkill -f "main.py.*elpyfi" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Force kill if needed
echo "Force killing any stubborn processes..."
pkill -9 -f "elpyfi" 2>/dev/null || true
pkill -9 -f "engine.py" 2>/dev/null || true

echo "✅ All services stopped"

# Check if ports are free
echo ""
echo "Checking port status:"
lsof -i :9000 -i :9001 -i :9002 -i :9003 | grep LISTEN || echo "All ports are free!"