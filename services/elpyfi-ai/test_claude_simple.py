#!/usr/bin/env python3
"""
SIMPLE test - just one stock, show me Claude's thoughts!
"""

import requests
import json

API_URL = "http://localhost:9000"

# Just test AAPL
test_signal = {
    "signal": {
        "symbol": "AAPL",
        "type": "buy",
        "price": 175.00,
        "indicators": [
            {"name": "RSI", "value": 25, "timeframe": "1h"},
            {"name": "MACD", "value": 2.5, "timeframe": "1h"},
            {"name": "VOLUME", "value": 3.2, "timeframe": "1h"}
        ],
        "market_conditions": {
            "trend": "bullish",
            "volatility": 0.2,
            "volume": 25000000
        }
    }
}

print("🍎 Testing AAPL signal...\n")

response = requests.post(f"{API_URL}/analyze", json=test_signal)
result = response.json()

print("RAW RESPONSE:")
print(json.dumps(result, indent=2))

# Look for Claude's thoughts in the formatted_explanation
if 'formatted_explanation' in result:
    print("\n" + "="*50)
    print("FORMATTED EXPLANATION:")
    print("="*50)
    print(result['formatted_explanation'])
    
    # Try to extract Claude's thoughts
    if "Claude says:" in result['formatted_explanation']:
        print("\n" + "="*50)
        print("🤖 CLAUDE'S THOUGHTS FOUND!")
        print("="*50)
        # Split and find the Claude part
        parts = result['formatted_explanation'].split("Claude says:")
        if len(parts) > 1:
            # Everything after "Claude says:" until the next section marker
            claude_text = parts[1].split('\n')[0]
            print(claude_text)