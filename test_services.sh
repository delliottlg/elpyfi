#!/bin/bash
# Quick test of PM Claude services

echo "🧪 Testing PM Claude Services"
echo "============================="

# Test 1: Status
echo -e "\n1️⃣ Checking status..."
./pm-claude status

# Test 2: Start core
echo -e "\n2️⃣ Starting core engine..."
timeout 5 ./pm-claude start elpyfi-core || true

# Test 3: Check if it's running
echo -e "\n3️⃣ Checking processes..."
ps aux | grep -E "engine.py|main.py" | grep -v grep | head -5

# Test 4: Check ports
echo -e "\n4️⃣ Checking ports..."
for port in 9000 9001 9002 9003; do
    if lsof -i:$port > /dev/null 2>&1; then
        echo "✅ Port $port is in use"
    else
        echo "❌ Port $port is free"
    fi
done

# Test 5: Test runner
echo -e "\n5️⃣ Running quick test..."
timeout 10 venv/bin/python -c "
from src.test_runner import ServiceTestRunner
from pathlib import Path
runner = ServiceTestRunner(Path('.'))
result = runner.test_elpyfi_core()
print(f'Core test: {result[\"success\"]}')
"

echo -e "\n✅ Test complete!"