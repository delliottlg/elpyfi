#!/usr/bin/env python3
"""
Simple test to see Claude's plain English thoughts on trading signals
"""

import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()
API_URL = "http://localhost:9000"

# A few interesting test cases
test_cases = [
    {
        "title": "🚀 Obvious Buy Signal",
        "signal": {
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
    },
    {
        "title": "🚀 AI Hype Stock (Palantir)",
        "signal": {
            "signal": {
                "symbol": "PLTR",
                "type": "buy",
                "price": 85.00,
                "indicators": [
                    {"name": "RSI", "value": 78, "timeframe": "1h"},  # Overbought
                    {"name": "MACD", "value": 3.2, "timeframe": "1h"},  # Strong momentum
                    {"name": "VOLUME", "value": 4.5, "timeframe": "1h"}  # Huge volume
                ],
                "market_conditions": {
                    "trend": "bullish",
                    "volatility": 0.65,
                    "volume": 95000000  # AI stocks seeing massive volume
                }
            }
        }
    },
    {
        "title": "🎢 Volatile Data Center Play (SMCI)",
        "signal": {
            "signal": {
                "symbol": "SMCI",
                "type": "sell",
                "price": 42.50,
                "indicators": [
                    {"name": "RSI", "value": 35, "timeframe": "1h"},  # Oversold but in downtrend
                    {"name": "MACD", "value": -2.8, "timeframe": "1h"},  # Strong negative
                    {"name": "VOLUME", "value": 2.1, "timeframe": "1h"},  # High selling volume
                    {"name": "BB_LOWER", "value": 45, "timeframe": "1h"}  # Below lower band
                ],
                "market_conditions": {
                    "trend": "bearish",  # Accounting concerns + competition
                    "volatility": 0.85,  # Super volatile
                    "volume": 25000000,
                    "support_levels": [40, 38, 35]
                }
            }
        }
    }
]

def test_signal(test_case):
    """Send a signal and display Claude's thoughts"""
    console.print(f"\n[bold cyan]{test_case['title']}[/bold cyan]")
    console.print(f"Symbol: {test_case['signal']['signal']['symbol']} @ ${test_case['signal']['signal']['price']}")
    
    try:
        response = requests.post(f"{API_URL}/analyze", json=test_case['signal'])
        result = response.json()
        
        # Debug removed - we found the format!
        
        # Extract the key info
        rec = result.get('recommendation', 'ERROR').upper()
        conf = result.get('confidence', 0)
        
        # Look for Claude's thoughts in different places
        formatted_explanation = result.get('formatted_explanation', '')
        plain_explanation = result.get('explanation', '')
        
        # Show Claude's thoughts prominently
        claude_found = False
        
        # Check for Claude's thoughts with the 💭 emoji format
        if "💭 **Claude says:" in formatted_explanation:
            # Extract Claude's paragraph
            start = formatted_explanation.find("💭 **Claude says:")
            if start != -1:
                # Find where Claude's thoughts end (look for the next section marker)
                claude_section = formatted_explanation[start:]
                # Extract just the thought text
                thought_start = claude_section.find("says:") + 5
                thought_end = claude_section.find("**\n", thought_start)
                if thought_end != -1:
                    claude_thoughts = claude_section[thought_start:thought_end].strip()
                    console.print(Panel(
                        f"[italic]{claude_thoughts}[/italic]",
                        title="🤖 Claude's Thoughts",
                        border_style="green",
                        width=100,
                        padding=(1, 2)
                    ))
                    claude_found = True
        
        # If not in formatted, check plain explanation
        if not claude_found and "Claude says:" in plain_explanation:
            claude_thoughts = plain_explanation.split("Claude says:")[1].split("|")[0].strip()
            console.print(Panel(
                f"[italic]{claude_thoughts}[/italic]",
                title="🤖 Claude's Thoughts",
                border_style="green",
                width=80
            ))
            claude_found = True
        
        # If not found, check metadata for the raw AI response
        if not claude_found:
            metadata = result.get('metadata', {})
            # The AI analyzer stores plain_english_thoughts in metadata (potentially)
            # But more likely it's just in the explanation but without "Claude says:"
            # Let's extract it from the explanation if it starts with certain patterns
            for explanation in [plain_explanation, formatted_explanation]:
                if explanation and len(explanation) > 100:  # Long enough to be Claude's paragraph
                    # Check if this looks like Claude's detailed thoughts
                    if any(phrase in explanation.lower() for phrase in ['looks like', 'this is', 'i think', 'what i see']):
                        # Extract the first sentence or two before technical details
                        thoughts = explanation.split('Recommendation:')[0].strip()
                        if thoughts and len(thoughts) > 50:
                            console.print(Panel(
                                f"[italic]\"{thoughts}\"[/italic]",
                                title="🤖 Claude's Thoughts", 
                                border_style="green"
                            ))
                            claude_found = True
                            break
        
        # If Claude's thoughts weren't found, it might be V1 mode
        if not claude_found:
            pass  # Claude's thoughts only appear in V2 mode
        
        # Show the decision
        color = "green" if rec == "BUY" else "red" if rec == "SELL" else "yellow"
        console.print(f"\n[bold {color}]Decision: {rec} ({conf:.0%} confidence)[/bold {color}]")
        
        # Show key factors
        factors = result.get('factors', [])
        if factors:
            console.print("\nKey factors:")
            for factor in factors[:5]:
                console.print(f"  • {factor}")
                
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

def main():
    console.print(Panel(
        "[bold]🤖 Claude's Trading Thoughts[/bold]\n"
        "See what Claude really thinks about these signals!",
        border_style="blue"
    ))
    
    # Check if API is running
    try:
        response = requests.get(f"{API_URL}/")
        api_info = response.json()
        mode = api_info.get('mode', 'Unknown')
        
        if "AI" not in mode:
            console.print("\n[red]⚠️  API is not in AI mode![/red]")
            console.print("Make sure USE_LLM=true in your .env file")
            return
            
        console.print(f"\n✅ API Mode: {mode}")
        
    except:
        console.print("[red]❌ Cannot connect to API on port 9000[/red]")
        return
    
    # Test each case
    for test_case in test_cases:
        test_signal(test_case)
        console.print("\n" + "─" * 50)
    
    console.print("\n[green]✨ That's what Claude thinks![/green]")

if __name__ == "__main__":
    main()