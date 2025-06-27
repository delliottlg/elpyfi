#!/usr/bin/env python3
"""
Performance testing for elpyfi-ai API
Tests throughput, latency, and concurrent request handling
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import random
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.live import Live
from rich.panel import Panel
import matplotlib.pyplot as plt
from datetime import datetime

console = Console()

API_URL = "http://localhost:9000"

def generate_random_signal() -> Dict[str, Any]:
    """Generate a random trading signal for testing"""
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMD", "META", "AMZN"]
    return {
        "signal": {
            "symbol": random.choice(symbols),
            "type": random.choice(["buy", "sell"]),
            "price": round(random.uniform(50, 500), 2),
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

async def measure_single_request(session: aiohttp.ClientSession) -> float:
    """Measure latency of a single request"""
    start = time.perf_counter()
    signal = generate_random_signal()
    
    try:
        async with session.post(f"{API_URL}/analyze", json=signal) as response:
            await response.json()
            end = time.perf_counter()
            return (end - start) * 1000  # Convert to milliseconds
    except:
        return -1

async def latency_test(num_requests: int = 100):
    """Test API latency with sequential requests"""
    console.print(f"\n[bold cyan]⏱️  Latency Test ({num_requests} sequential requests)[/bold cyan]")
    
    latencies = []
    async with aiohttp.ClientSession() as session:
        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Testing latency...", total=num_requests)
            
            for i in range(num_requests):
                latency = await measure_single_request(session)
                if latency > 0:
                    latencies.append(latency)
                progress.update(task, advance=1)
    
    if latencies:
        stats = {
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            "p99": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
        }
        
        table = Table(title="Latency Statistics (ms)")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        for metric, value in stats.items():
            table.add_row(metric.upper(), f"{value:.2f} ms")
        
        console.print(table)
        return latencies
    else:
        console.print("[red]No successful requests![/red]")
        return []

async def throughput_test(duration_seconds: int = 30, concurrent_requests: int = 10):
    """Test API throughput with concurrent requests"""
    console.print(f"\n[bold green]📊 Throughput Test ({concurrent_requests} concurrent requests for {duration_seconds}s)[/bold green]")
    
    start_time = time.time()
    request_count = 0
    errors = 0
    
    async def worker(session: aiohttp.ClientSession):
        nonlocal request_count, errors
        while time.time() - start_time < duration_seconds:
            try:
                signal = generate_random_signal()
                async with session.post(f"{API_URL}/analyze", json=signal) as response:
                    await response.json()
                    request_count += 1
            except:
                errors += 1
    
    async with aiohttp.ClientSession() as session:
        with Live(console=console, refresh_per_second=4) as live:
            # Start workers
            tasks = [asyncio.create_task(worker(session)) for _ in range(concurrent_requests)]
            
            # Update display
            while time.time() - start_time < duration_seconds:
                elapsed = time.time() - start_time
                rps = request_count / elapsed if elapsed > 0 else 0
                
                panel = Panel(
                    f"[bold]Requests:[/bold] {request_count}\n"
                    f"[bold]Errors:[/bold] {errors}\n"
                    f"[bold]RPS:[/bold] {rps:.2f}\n"
                    f"[bold]Time:[/bold] {elapsed:.1f}s / {duration_seconds}s",
                    title="Throughput Test Progress"
                )
                live.update(panel)
                await asyncio.sleep(0.25)
            
            # Cancel remaining tasks
            for task in tasks:
                task.cancel()
    
    total_time = time.time() - start_time
    rps = request_count / total_time
    
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"Total requests: {request_count}")
    console.print(f"Total errors: {errors}")
    console.print(f"Average RPS: {rps:.2f}")
    console.print(f"Success rate: {(request_count / (request_count + errors) * 100):.1f}%")
    
    return rps

async def stress_test(max_concurrent: int = 100, step: int = 10):
    """Gradually increase load to find breaking point"""
    console.print(f"\n[bold red]🔥 Stress Test (up to {max_concurrent} concurrent requests)[/bold red]")
    
    results = []
    
    for concurrent in range(step, max_concurrent + 1, step):
        console.print(f"\nTesting with {concurrent} concurrent requests...")
        
        # Run mini throughput test
        rps = await throughput_test(duration_seconds=10, concurrent_requests=concurrent)
        results.append((concurrent, rps))
        
        # If performance degrades significantly, stop
        if len(results) > 1 and rps < results[-2][1] * 0.8:
            console.print("[yellow]Performance degradation detected, stopping test[/yellow]")
            break
    
    # Display results
    table = Table(title="Stress Test Results")
    table.add_column("Concurrent Requests", style="cyan")
    table.add_column("RPS", style="white")
    
    for concurrent, rps in results:
        table.add_row(str(concurrent), f"{rps:.2f}")
    
    console.print(table)
    
    # Find optimal concurrency
    optimal = max(results, key=lambda x: x[1])
    console.print(f"\n[bold green]Optimal concurrency: {optimal[0]} requests ({optimal[1]:.2f} RPS)[/bold green]")

def plot_latency_distribution(latencies: List[float]):
    """Create a histogram of latency distribution"""
    if not latencies:
        return
    
    plt.figure(figsize=(10, 6))
    plt.hist(latencies, bins=50, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(statistics.mean(latencies), color='red', linestyle='dashed', linewidth=2, label=f'Mean: {statistics.mean(latencies):.2f}ms')
    plt.axvline(statistics.median(latencies), color='green', linestyle='dashed', linewidth=2, label=f'Median: {statistics.median(latencies):.2f}ms')
    
    plt.xlabel('Latency (ms)')
    plt.ylabel('Frequency')
    plt.title('API Latency Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    filename = f"latency_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    console.print(f"\n[green]Latency distribution saved to {filename}[/green]")

async def main():
    """Run all performance tests"""
    console.print(Panel.fit(
        "[bold]🚀 elpyfi-ai Performance Test Suite[/bold]\n"
        "Testing API performance characteristics",
        border_style="blue"
    ))
    
    # Check if API is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/health") as response:
                if response.status != 200:
                    raise Exception("API not healthy")
    except:
        console.print("[bold red]❌ API is not running on port 9000![/bold red]")
        console.print("Please start the server with: python main.py")
        return
    
    # Run tests
    latencies = await latency_test(100)
    
    await throughput_test(30, 10)
    
    # Stress test (optional - can be intensive)
    console.print("\n[yellow]Run stress test? This will send many concurrent requests.[/yellow]")
    if input("Continue? (y/N): ").lower() == 'y':
        await stress_test(50, 5)
    
    # Plot latency distribution if matplotlib is available
    try:
        if latencies:
            plot_latency_distribution(latencies)
    except ImportError:
        console.print("[yellow]Install matplotlib to see latency distribution plots[/yellow]")
    
    console.print("\n[bold green]✅ Performance testing complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())