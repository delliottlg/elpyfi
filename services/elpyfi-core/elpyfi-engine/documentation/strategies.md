# Strategy Framework Documentation

## Overview

The strategy framework provides a standardized way to build trading strategies that work within PDT restrictions. All strategies follow the same pattern, making them easy to understand, test, and compare.

## Core Concepts

### What is a Strategy?

A strategy is a self-contained trading algorithm that:
- Analyzes market data
- Generates trading signals with confidence scores
- Estimates potential profits
- Declares its trading style (day trade vs swing)

### Strategy Categories

1. **Day Trade Strategies** - Close positions same day
   - Limited to 3 per week across ALL strategies
   - Must have very high confidence (>0.85)
   - Examples: Opening range breakout, momentum scalping

2. **Swing Strategies** - Hold positions overnight
   - No PDT limits!
   - Can trade as much as they want
   - Examples: Trend following, mean reversion

3. **Crypto Strategies** - 24/7 markets
   - No PDT restrictions
   - Can be day trade or swing style

## Strategy Interface

Every strategy must implement three methods:

### 1. Configuration Property
```python
@property
def config(self) -> StrategyConfig:
    """Declares how this strategy trades"""
    return StrategyConfig(
        day_trade_budget=0.5,      # Uses 50% of weekly day trades
        min_hold_period="0 days",  # Can day trade
        preferred_timeframe="5min" # Needs 5-minute candles
    )
```

### 2. Analyze Method
```python
def analyze(self, data: MarketData) -> Signal:
    """Look at market data and decide what to do"""
    # Your algorithm here...
    return Signal(
        action="buy",      # or "sell", "hold"
        confidence=0.92,   # How sure are you? (0-1)
        symbol="AAPL",
        target_price=150.00
    )
```

### 3. Profit Estimation
```python
def estimate_profit(self, signal: Signal) -> float:
    """Estimate potential profit for PDT allocation"""
    # Return expected profit as decimal (0.02 = 2%)
    return 0.02
```

## How PDT Management Works

When multiple strategies want to day trade:

1. Each strategy emits a `DAY_TRADE_REQUESTED` event
2. The PDT Allocator scores each request:
   - Score = confidence × estimated_profit × historical_success
3. Top 3 requests for the week get approved
4. Others must either:
   - Convert to swing trades (hold overnight)
   - Wait for next week

## Creating a New Strategy

1. Create a new file in `strategies/` folder
2. Import the base class: `from .base import Strategy`
3. Implement the three required methods
4. Register it with the engine

Example structure:
```python
from .base import Strategy
from .models import StrategyConfig, Signal
from ..events import event_bus, EventType, SignalEvent
from datetime import datetime

class MyMomentumStrategy(Strategy):
    @property
    def config(self) -> StrategyConfig:
        return StrategyConfig(
            day_trade_budget=0.3,
            min_hold_period="0 days",
            preferred_timeframe="1min"
        )
    
    def analyze(self, data: MarketData) -> Signal:
        # Your analysis logic here
        if momentum_is_strong:
            return Signal(
                action="buy",
                confidence=0.88,
                symbol=data.symbol,
                target_price=data.current_price * 1.01
            )
        return Signal(action="hold", confidence=0.0, symbol=data.symbol)
    
    def estimate_profit(self, signal: Signal) -> float:
        # Conservative estimate
        return 0.01  # 1% expected profit
```

## Best Practices

1. **Be Conservative with Confidence** - Only high confidence for day trades
2. **Accurate Profit Estimates** - The allocator relies on these
3. **Clear Strategy Names** - Make it obvious what the strategy does
4. **Single Responsibility** - Each strategy does ONE thing well
5. **Emit Events** - Let the system know what you're doing

## Testing Strategies

Strategies are easy to test in isolation:

```python
def test_momentum_strategy():
    strategy = MyMomentumStrategy()
    
    # Test configuration
    assert strategy.config.day_trade_budget <= 1.0
    
    # Test analysis
    mock_data = create_mock_market_data()
    signal = strategy.analyze(mock_data)
    assert signal.confidence >= 0.0
    assert signal.action in ["buy", "sell", "hold"]
```