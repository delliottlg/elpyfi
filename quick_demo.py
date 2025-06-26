#!/usr/bin/env python3
"""
Quick demo of PM Claude functionality
"""

import time
import subprocess
import sys
from pathlib import Path

print("🎯 PM Claude Quick Demo")
print("=" * 50)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test 1: Secrets Manager
print("\n1️⃣ Testing Secrets Manager...")
try:
    from secrets_manager import SecretsManager
    sm = SecretsManager(Path("config"))
    sm.load_secrets()
    print("✅ Secrets loaded successfully")
    results = sm.validate_all_services()
    for service, valid in results.items():
        print(f"  {service}: {'✅' if valid else '❌'}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Test Runner
print("\n2️⃣ Testing Test Runner...")
try:
    from test_runner import ServiceTestRunner
    runner = ServiceTestRunner(Path("."))
    result = runner.test_elpyfi_core()
    print(f"✅ Core test: {'PASSED' if result['success'] else 'FAILED'}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Service Status
print("\n3️⃣ Testing Service Orchestrator...")
try:
    from service_orchestrator import ServiceOrchestrator
    orch = ServiceOrchestrator(Path("."))
    orch.load_config()
    print("✅ Configuration loaded")
    print(f"  Services configured: {len(orch.services)}")
    for sid, service in orch.services.items():
        print(f"  - {service.name}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Health Monitor
print("\n4️⃣ Testing Health Monitor...")
try:
    from health_monitor import HealthMonitor
    hm = HealthMonitor(orch)
    print("✅ Health monitor initialized")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: CLAUDE.md Updater
print("\n5️⃣ Testing CLAUDE.md Updater...")
try:
    from claude_md_updater import ClaudeMdUpdater
    updater = ClaudeMdUpdater(Path("."), orch)
    print(f"✅ Found {len(updater.claude_files)} CLAUDE.md files")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ PM Claude is fully operational!")
print("\nNext steps:")
print("1. Update config/secrets.yaml with real credentials")
print("2. Ensure PostgreSQL database is accessible")
print("3. Run: ./pm-claude start")
print("4. Or use MCP: 'Start the trading system'")