#!/usr/bin/env python3
"""
Railway build router - directs to appropriate service
"""
import os
import sys

service = os.environ.get('RAILWAY_SERVICE_NAME', '')

if service == 'core':
    os.chdir('services/elpyfi-core/elpyfi-engine')
    os.system('python engine.py')
elif service == 'ai':
    os.chdir('services/elpyfi-ai')
    os.system('python main.py')
elif service == 'api':
    os.chdir('services/elpyfi-api')
    os.system('python -m src.elpyfi_api.main')
else:
    print(f"Unknown service: {service}")
    print("Set RAILWAY_SERVICE_NAME to: core, ai, or api")
    sys.exit(1)