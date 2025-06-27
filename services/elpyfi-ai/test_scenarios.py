#!/usr/bin/env python3
"""
Scenario runner for testing various trading situations
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

API_URL = "http://localhost:9000"

@dataclass
class TestScenario:
    name: str
    description: str
    signal_data: Dict[str, Any]
    expected_outcome: str
    
scenarios = [
    TestScenario(
        name="🎯 Perfect Buy Setup",
        description="All indicators align for strong buy",
        signal_data={
            "signal": {
                "symbol": "AAPL",
                "type": "buy",
                "price": 175.00,
                "indicators": [
                    {"name": "RSI", "value": 25, "timeframe": "1h"},
                    {"name": "MACD", "value": 1.5, "timeframe": "1h"},
                    {"name": "VOLUME", "value": 2.5, "timeframe": "1h"},
                    {"name": "MA", "value": 170, "timeframe": "1h"}
                ],
                "market_conditions": {
                    "trend": "bullish",
                    "volatility": 0.2,
                    "volume": 25000000
                }
            }
        },
        expected_outcome="Strong BUY with high confidence"
    ),
    
    TestScenario(
        name="⚠️ Mixed Signals",
        description="Conflicting indicators",
        signal_data={
            "signal": {
                "symbol": "MSFT",
                "type": "buy",
                "price": 380.00,
                "indicators": [
                    {"name": "RSI", "value": 65, "timeframe": "1h"},  # Neutral-bearish
                    {"name": "MACD", "value": 0.5, "timeframe": "1h"},  # Bullish
                    {"name": "VOLUME", "value": 0.6, "timeframe": "1h"}  # Low
                ]
            }
        },
        expected_outcome="HOLD or weak signal"
    ),
    
    TestScenario(
        name="🔥 Overheated Market",
        description="Extreme overbought conditions",
        signal_data={
            "signal": {
                "symbol": "NVDA",
                "type": "buy",
                "price": 950.00,
                "indicators": [
                    {"name": "RSI", "value": 85, "timeframe": "1h"},
                    {"name": "MACD", "value": -0.5, "timeframe": "1h"}
                ],
                "market_conditions": {
                    "trend": "bullish",
                    "volatility": 0.8,
                    "volume": 50000000
                }
            }
        },
        expected_outcome="SELL or strong warning"
    ),
    
    TestScenario(
        name="💎 Diamond Hands Test",
        description="Testing stop loss trigger",
        signal_data={
            "signal": {
                "symbol": "GME",
                "type": "stop_loss",
                "price": 15.00,
                "indicators": [
                    {"name": "RSI", "value": 20, "timeframe": "5m"},
                ]
            }
        },
        expected_outcome="STOP_LOSS execution"
    ),
    
    TestScenario(
        name="🏦 Small Account PDT",
        description="Account under 25k with no day trades left",
        signal_data={
            "signal": {
                "symbol": "SPY",
                "type": "buy",
                "price": 580.00,
                "indicators": [
                    {"name": "RSI", "value": 30, "timeframe": "5m"},
                    {"name": "MACD", "value": 2.0, "timeframe": "5m"}
                ]
            },
            "constraints": {
                "pdt_trades_remaining": 0,
                "account_balance": 5000,
                "buying_power": 2500
            }
        },
        expected_outcome="HOLD due to PDT"
    ),
    
    TestScenario(
        name="🌙 After Hours Thin Volume",
        description="Low volume after-hours trading",
        signal_data={
            "signal": {
                "symbol": "AMZN",
                "type": "buy",
                "price": 185.00,
                "indicators": [
                    {"name": "VOLUME", "value": 0.2, "timeframe": "5m"},
                    {"name": "RSI", "value": 45, "timeframe": "5m"}
                ],
                "market_conditions": {
                    "trend": "neutral",
                    "volatility": 0.1,
                    "volume": 100000  # Very low
                }
            }
        },
        expected_outcome="Weak signal due to low volume"
    ),
    
    TestScenario(
        name="🚀 Meme Stock Frenzy",
        description="High volatility meme stock",
        signal_data={
            "signal": {
                "symbol": "AMC",
                "type": "buy",
                "price": 8.50,
                "indicators": [
                    {"name": "RSI", "value": 55, "timeframe": "1m"},
                    {"name": "VOLUME", "value": 5.0, "timeframe": "1m"}  # Massive volume
                ],
                "market_conditions": {
                    "trend": "neutral",
                    "volatility": 0.95,  # Extreme volatility
                    "volume": 500000000
                }
            }
        },
        expected_outcome="High risk warning"
    ),
    
    TestScenario(
        name="📈 Breakout Confirmation",
        description="Price breaking resistance with volume",
        signal_data={
            "signal": {
                "symbol": "META",
                "type": "buy",
                "price": 520.00,
                "indicators": [
                    {"name": "RSI", "value": 62, "timeframe": "1h"},
                    {"name": "MACD", "value": 3.2, "timeframe": "1h"},
                    {"name": "VOLUME", "value": 3.5, "timeframe": "1h"},
                    {"name": "BB_UPPER", "value": 518, "timeframe": "1h"}
                ],
                "market_conditions": {
                    "trend": "bullish",
                    "volatility": 0.4,
                    "volume": 30000000,
                    "resistance_levels": [515, 525, 535]
                }
            }
        },
        expected_outcome="BUY on breakout"
    )
]

async def test_scenario(session: aiohttp.ClientSession, scenario: TestScenario) -> Dict[str, Any]:
    """Run a single test scenario"""
    try:
        async with session.post(f"{API_URL}/analyze", json=scenario.signal_data) as response:
            result = await response.json()
            return {
                "scenario": scenario.name,
                "success": response.status == 200,
                "recommendation": result.get("recommendation", "ERROR"),
                "confidence": result.get("confidence", 0),
                "expected": scenario.expected_outcome,
                "response": result
            }
    except Exception as e:
        return {
            "scenario": scenario.name,
            "success": False,
            "error": str(e),
            "expected": scenario.expected_outcome
        }

async def run_all_scenarios():
    """Run all test scenarios concurrently"""
    console.print("[bold cyan]🧪 Running Test Scenarios...[/bold cyan]\n")
    
    async with aiohttp.ClientSession() as session:
        tasks = [test_scenario(session, scenario) for scenario in scenarios]
        results = []
        
        for task in track(asyncio.as_completed(tasks), total=len(tasks), description="Testing..."):
            result = await task
            results.append(result)
    
    return results

def display_results(results: List[Dict[str, Any]]):
    """Display test results in a nice table"""
    table = Table(title="📊 Test Results", show_header=True)
    table.add_column("Scenario", style="cyan", width=25)
    table.add_column("Expected", style="yellow", width=20)
    table.add_column("Got", style="white", width=15)
    table.add_column("Confidence", style="magenta", width=10)
    table.add_column("Status", style="white", width=10)
    
    passed = 0
    for result in results:
        if result["success"]:
            rec = result["recommendation"].upper()
            conf = f"{result['confidence']:.0%}"
            
            # Simple pass/fail logic
            status_icon = "✅" if result["confidence"] > 0.3 else "⚠️"
            if "PDT" in result["expected"] and rec == "HOLD":
                status_icon = "✅"
                passed += 1
            elif rec in result["expected"].upper():
                status_icon = "✅"
                passed += 1
            
            table.add_row(
                result["scenario"],
                result["expected"],
                rec,
                conf,
                status_icon
            )
        else:
            table.add_row(
                result["scenario"],
                result["expected"],
                "ERROR",
                "-",
                "❌"
            )
    
    console.print("\n", table)
    console.print(f"\n[bold]Summary:[/bold] {passed}/{len(results)} scenarios passed")
    
    # Show detailed output for interesting cases
    console.print("\n[bold]Interesting Results:[/bold]")
    for result in results:
        if result["success"] and "response" in result:
            resp = result["response"]
            if resp["confidence"] > 0.8 or resp["confidence"] < 0.3:
                console.print(f"\n[cyan]{result['scenario']}[/cyan]")
                console.print(f"Factors: {', '.join(resp['factors'][:3])}")

def main():
    """Run the scenario test suite"""
    # Check health first
    import requests
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code != 200:
            raise Exception("API not healthy")
    except:
        console.print("[bold red]❌ API is not running![/bold red]")
        console.print("Please start the server with: python main.py")
        return
    
    # Run scenarios
    results = asyncio.run(run_all_scenarios())
    display_results(results)
    
    # Show metrics
    try:
        metrics = requests.get(f"{API_URL}/metrics").json()
        console.print(f"\n[bold]API Metrics:[/bold]")
        console.print(f"Total analyses: {metrics.get('total_analyses', 0)}")
        console.print(f"Average confidence: {metrics.get('average_confidence', 0):.0%}")
    except:
        pass

if __name__ == "__main__":
    main()