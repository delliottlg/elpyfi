#!/usr/bin/env python3
"""
Test script to compare V1 (rule-based) vs V2 (AI-enhanced) analysis
"""

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
import json

console = Console()

API_URL = "http://localhost:9000"

# Test signals with interesting patterns
test_signals = [
    {
        "name": "📈 Hidden Bullish Divergence",
        "signal": {
            "symbol": "AAPL",
            "type": "buy",
            "price": 175.50,
            "indicators": [
                {"name": "RSI", "value": 32, "timeframe": "1h"},  # Oversold
                {"name": "MACD", "value": -0.5, "timeframe": "1h"},  # Still negative
                {"name": "VOLUME", "value": 0.8, "timeframe": "1h"}  # Low volume
            ],
            "market_conditions": {
                "trend": "bearish",  # Bearish trend but RSI oversold
                "volatility": 0.3,
                "volume": 12000000
            }
        },
        "description": "Price trending down but RSI showing oversold - potential reversal"
    },
    
    {
        "name": "🎯 Breakout with Volume",
        "signal": {
            "symbol": "NVDA",
            "type": "buy",
            "price": 890.00,
            "indicators": [
                {"name": "RSI", "value": 65, "timeframe": "4h"},  # Strong but not overbought
                {"name": "MACD", "value": 5.2, "timeframe": "4h"},  # Strong positive
                {"name": "VOLUME", "value": 3.5, "timeframe": "4h"},  # Huge volume spike
                {"name": "BB_UPPER", "value": 885, "timeframe": "4h"}  # Breaking bands
            ],
            "market_conditions": {
                "trend": "bullish",
                "volatility": 0.45,
                "volume": 45000000,
                "resistance_levels": [885, 900, 920]
            }
        },
        "description": "Breaking resistance on high volume - momentum play"
    },
    
    {
        "name": "⚠️ Conflicting Signals",
        "signal": {
            "symbol": "TSLA",
            "type": "sell",
            "price": 245.00,
            "indicators": [
                {"name": "RSI", "value": 68, "timeframe": "1h"},  # Near overbought
                {"name": "MACD", "value": 2.1, "timeframe": "1h"},  # Bullish
                {"name": "VOLUME", "value": 1.2, "timeframe": "1h"}  # Normal
            ],
            "market_conditions": {
                "trend": "neutral",
                "volatility": 0.7,  # High volatility
                "volume": 25000000
            }
        },
        "description": "Mixed signals with high volatility - requires nuanced analysis"
    }
]

def check_api_mode():
    """Check which mode the API is running in"""
    try:
        response = requests.get(f"{API_URL}/")
        data = response.json()
        mode = data.get("mode", "Unknown")
        version = data.get("version", "Unknown")
        
        color = "green" if "AI" in mode else "yellow"
        console.print(Panel(
            f"[bold {color}]{mode}[/bold {color}]\nVersion: {version}",
            title="🤖 API Mode",
            border_style=color
        ))
        
        return "AI" in mode
    except:
        console.print("[red]Failed to connect to API[/red]")
        return False

def analyze_signal(signal_data: dict) -> dict:
    """Send signal to API for analysis"""
    try:
        response = requests.post(f"{API_URL}/analyze", json=signal_data)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def compare_analyses(signal_info: dict):
    """Display analysis results"""
    console.print(f"\n[bold cyan]{signal_info['name']}[/bold cyan]")
    console.print(f"[italic]{signal_info['description']}[/italic]\n")
    
    # Analyze the signal
    result = analyze_signal(signal_info['signal'])
    
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    # Display recommendation
    rec = result['recommendation'].upper()
    conf = result['confidence']
    
    rec_color = "green" if rec == "BUY" else "red" if rec == "SELL" else "yellow"
    console.print(f"[bold {rec_color}]Recommendation: {rec} ({conf:.0%} confidence)[/bold {rec_color}]")
    
    # Display factors
    console.print("\n[bold]Key Factors:[/bold]")
    for factor in result.get('factors', []):
        if factor.startswith("AI:"):
            console.print(f"  🤖 {factor}")
        elif factor.startswith("Pattern:"):
            console.print(f"  🔍 {factor}")
        elif factor.startswith("Sentiment:"):
            console.print(f"  💭 {factor}")
        else:
            console.print(f"  • {factor}")
    
    # Show metadata if AI is enabled
    metadata = result.get('metadata', {})
    if metadata.get('ai_enabled'):
        console.print(f"\n[dim]AI Analysis: {metadata.get('ai_recommendation', 'N/A')} "
                     f"({metadata.get('ai_confidence', 0):.0%})[/dim]")

def test_mock_ai():
    """Test with mock AI analyzer"""
    console.print("\n[bold magenta]🧪 Testing Mock AI Mode[/bold magenta]")
    console.print("This simulates AI enhancement without actual API calls\n")
    
    from ai_analyzer import MockAIAnalyzer
    mock_analyzer = MockAIAnalyzer()
    
    # Test one signal with mock AI
    test_signal = test_signals[0]
    signal_obj = Signal(**test_signal['signal'])
    
    decision = mock_analyzer.analyze(signal_obj)
    
    console.print(f"[bold]Mock AI Analysis for {test_signal['name']}[/bold]")
    console.print(f"Recommendation: {decision.recommendation.value.upper()}")
    console.print(f"Confidence: {decision.confidence:.0%}")
    console.print("\nFactors:")
    for factor in decision.factors:
        console.print(f"  • {factor}")

def main():
    console.print(Panel.fit(
        "[bold]🤖 AI Mode Testing for elpyfi-ai[/bold]\n"
        "Compare rule-based vs AI-enhanced analysis",
        border_style="blue"
    ))
    
    # Check API mode
    is_ai_mode = check_api_mode()
    
    if not is_ai_mode:
        console.print("\n[yellow]ℹ️  API is running in rule-based mode (V1)[/yellow]")
        console.print("To enable AI mode, set in your .env file:")
        console.print("[cyan]USE_LLM=true[/cyan]")
        console.print("[cyan]ANTHROPIC_API_KEY=your_key_here[/cyan]\n")
    
    # Run analyses
    for signal_info in test_signals:
        compare_analyses(signal_info)
        console.print("\n" + "─" * 60 + "\n")
    
    # Offer to test mock AI
    if not is_ai_mode:
        console.print("[yellow]Would you like to see a mock AI analysis demo?[/yellow]")
        if input("Test mock AI? (y/N): ").lower() == 'y':
            # Need to import here to show the mock functionality
            from models import Signal
            test_mock_ai()

if __name__ == "__main__":
    main()