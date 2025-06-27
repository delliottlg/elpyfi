#!/usr/bin/env python3
"""
Interactive test script for elpyfi-ai API
Run this while your server is running to test different scenarios
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any
import random
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

console = Console()

API_URL = "http://localhost:9000"

def print_signal_analysis(response: Dict[str, Any]):
    """Pretty print the analysis response"""
    
    # Create a panel with the recommendation
    rec = response['recommendation'].upper()
    confidence = response['confidence']
    
    color = "green" if rec == "BUY" else "red" if rec == "SELL" else "yellow"
    
    console.print(Panel(
        f"[bold {color}]{rec}[/bold {color}] @ ${response['price']:.2f}\n"
        f"Confidence: {confidence:.0%}",
        title=f"📊 {response['symbol']} Analysis",
        border_style=color
    ))
    
    # Print formatted explanation
    console.print("\n[bold]Analysis Summary:[/bold]")
    console.print(response['formatted_explanation'])
    
    # Risk Assessment Table
    risk = response['risk_assessment']
    table = Table(title="Risk Assessment", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Risk Level", risk['level'].upper())
    if risk['stop_loss']:
        table.add_row("Stop Loss", f"${risk['stop_loss']:.2f}")
    if risk['take_profit']:
        table.add_row("Take Profit", f"${risk['take_profit']:.2f}")
    if risk['position_size']:
        table.add_row("Position Size", f"{risk['position_size']:.0%}")
    if risk['risk_reward_ratio']:
        table.add_row("Risk/Reward", f"1:{risk['risk_reward_ratio']:.1f}")
    
    console.print("\n", table)

def test_bullish_scenario():
    """Test a strong bullish signal"""
    console.print("\n[bold cyan]🐂 Testing Bullish Scenario...[/bold cyan]")
    
    signal = {
        "signal": {
            "symbol": "AAPL",
            "type": "buy",
            "price": 185.50,
            "indicators": [
                {"name": "RSI", "value": 28, "timeframe": "1h"},
                {"name": "MACD", "value": 0.8, "timeframe": "1h"},
                {"name": "VOLUME", "value": 2.1, "timeframe": "1h"}
            ],
            "market_conditions": {
                "trend": "bullish",
                "volatility": 0.25,
                "volume": 15000000
            }
        }
    }
    
    response = requests.post(f"{API_URL}/analyze", json=signal)
    print_signal_analysis(response.json())

def test_bearish_scenario():
    """Test a strong bearish signal"""
    console.print("\n[bold red]🐻 Testing Bearish Scenario...[/bold red]")
    
    signal = {
        "signal": {
            "symbol": "TSLA",
            "type": "sell",
            "price": 245.00,
            "indicators": [
                {"name": "RSI", "value": 78, "timeframe": "4h"},
                {"name": "MACD", "value": -1.2, "timeframe": "4h"},
                {"name": "VOLUME", "value": 0.7, "timeframe": "4h"}
            ],
            "market_conditions": {
                "trend": "bearish",
                "volatility": 0.65,
                "volume": 25000000
            }
        }
    }
    
    response = requests.post(f"{API_URL}/analyze", json=signal)
    print_signal_analysis(response.json())

def test_pdt_constraint():
    """Test PDT constraint handling"""
    console.print("\n[bold yellow]🚫 Testing PDT Constraint...[/bold yellow]")
    
    signal = {
        "signal": {
            "symbol": "NVDA",
            "type": "buy",
            "price": 875.00,
            "indicators": [
                {"name": "RSI", "value": 22, "timeframe": "15m"},
                {"name": "MACD", "value": 2.5, "timeframe": "15m"}
            ]
        },
        "constraints": {
            "pdt_trades_remaining": 0,
            "account_balance": 25000,
            "buying_power": 10000
        }
    }
    
    response = requests.post(f"{API_URL}/analyze", json=signal)
    print_signal_analysis(response.json())

def test_high_volatility():
    """Test high volatility crypto scenario"""
    console.print("\n[bold magenta]🌊 Testing High Volatility (Crypto)...[/bold magenta]")
    
    signal = {
        "signal": {
            "symbol": "BTC-USD",
            "type": "buy",
            "price": 95750.00,
            "indicators": [
                {"name": "RSI", "value": 45, "timeframe": "1h"},
                {"name": "MACD", "value": 150, "timeframe": "1h"},
                {"name": "BB", "value": 1.8, "timeframe": "1h"}
            ],
            "market_conditions": {
                "trend": "neutral",
                "volatility": 0.85,
                "volume": 5000000000
            }
        }
    }
    
    response = requests.post(f"{API_URL}/analyze", json=signal)
    print_signal_analysis(response.json())

def test_random_signal():
    """Generate and test a random signal"""
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "TSLA", "NVDA", "AMD"]
    symbol = random.choice(symbols)
    price = random.uniform(50, 500)
    
    console.print(f"\n[bold blue]🎲 Testing Random Signal for {symbol}...[/bold blue]")
    
    signal = {
        "signal": {
            "symbol": symbol,
            "type": random.choice(["buy", "sell"]),
            "price": round(price, 2),
            "indicators": [
                {"name": "RSI", "value": random.uniform(20, 80), "timeframe": "1h"},
                {"name": "MACD", "value": random.uniform(-2, 2), "timeframe": "1h"},
                {"name": "VOLUME", "value": random.uniform(0.5, 2.5), "timeframe": "1h"}
            ],
            "market_conditions": {
                "trend": random.choice(["bullish", "bearish", "neutral"]),
                "volatility": random.uniform(0.1, 0.9),
                "volume": random.randint(1000000, 50000000)
            }
        }
    }
    
    response = requests.post(f"{API_URL}/analyze", json=signal)
    print_signal_analysis(response.json())

def check_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            console.print("[bold green]✅ API is healthy![/bold green]")
            return True
    except:
        console.print("[bold red]❌ API is not running on port 9000[/bold red]")
        console.print("Please start the server with: python main.py")
        return False

def main():
    console.print(Panel.fit(
        "[bold]🚀 elpyfi-ai Interactive Test Suite[/bold]\n"
        "Testing your AI trading signal analyzer",
        border_style="blue"
    ))
    
    if not check_health():
        return
    
    while True:
        console.print("\n[bold]Choose a test scenario:[/bold]")
        console.print("1. 🐂 Bullish Signal (Strong Buy)")
        console.print("2. 🐻 Bearish Signal (Strong Sell)")
        console.print("3. 🚫 PDT Constraint Test")
        console.print("4. 🌊 High Volatility (Crypto)")
        console.print("5. 🎲 Random Signal")
        console.print("6. 🔄 Run All Tests")
        console.print("0. 🚪 Exit")
        
        choice = input("\nEnter choice (0-6): ")
        
        if choice == "0":
            console.print("[bold]👋 Goodbye![/bold]")
            break
        elif choice == "1":
            test_bullish_scenario()
        elif choice == "2":
            test_bearish_scenario()
        elif choice == "3":
            test_pdt_constraint()
        elif choice == "4":
            test_high_volatility()
        elif choice == "5":
            test_random_signal()
        elif choice == "6":
            test_bullish_scenario()
            test_bearish_scenario()
            test_pdt_constraint()
            test_high_volatility()
            console.print("\n[bold green]✅ All tests completed![/bold green]")
        else:
            console.print("[red]Invalid choice![/red]")

if __name__ == "__main__":
    main()