# Strategy Framework - LLM Context

## Module Structure
```
strategies/
├── __init__.py      # Module exports
├── base.py          # Abstract Strategy class
├── models.py        # StrategyConfig, Signal, MarketData
└── [strategies].py  # Individual strategy implementations
```

## File: strategies/base.py

### Abstract Base Class
```python
from abc import ABC, abstractmethod
from .models import StrategyConfig, Signal, MarketData

class Strategy(ABC):
    """Base class for all trading strategies"""
    
    @property
    @abstractmethod
    def config(self) -> StrategyConfig:
        """Strategy configuration and constraints"""
        pass
    
    @abstractmethod
    def analyze(self, data: MarketData) -> Signal:
        """Analyze market data and generate signal"""
        pass
    
    @abstractmethod
    def estimate_profit(self, signal: Signal) -> float:
        """Estimate profit potential (0.01 = 1%)"""
        pass
```

## File: strategies/models.py

### Data Models
```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class StrategyConfig:
    day_trade_budget: float      # 0.0-1.0 portion of weekly 3 trades
    min_hold_period: str         # "0 days", "1 day", "1 week"
    preferred_timeframe: str     # "1min", "5min", "1hour", "1day"
    max_position_size: float = 0.1  # Max 10% of portfolio per trade
    stop_loss: float = 0.02         # 2% default stop loss
    
@dataclass
class Signal:
    action: str              # "buy", "sell", "hold"
    confidence: float        # 0.0-1.0 confidence score
    symbol: str             # Trading symbol
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    metadata: Optional[Dict] = None

@dataclass  
class MarketData:
    symbol: str
    timestamp: datetime
    current_price: float
    volume: float
    high: float
    low: float
    open: float
    close: float
    indicators: Optional[Dict[str, float]] = None  # RSI, MA, etc
```

## Strategy Implementation Pattern

### Day Trade Strategy Template
```python
class OpeningRangeBreakout(Strategy):
    """High-confidence day trading strategy"""
    
    @property
    def config(self) -> StrategyConfig:
        return StrategyConfig(
            day_trade_budget=0.33,  # Wants 1 of 3 weekly trades
            min_hold_period="0 days",
            preferred_timeframe="1min",
            max_position_size=0.05,  # 5% positions for day trades
            stop_loss=0.01  # Tight 1% stop for day trades
        )
    
    def analyze(self, data: MarketData) -> Signal:
        # Only trade first 30 minutes
        if not self._is_opening_range(data.timestamp):
            return Signal("hold", 0.0, data.symbol)
            
        # Check for breakout conditions
        if self._detect_breakout(data):
            return Signal(
                action="buy",
                confidence=0.91,  # High confidence required
                symbol=data.symbol,
                target_price=data.current_price * 1.015,  # 1.5% target
                stop_price=data.current_price * 0.99      # 1% stop
            )
        
        return Signal("hold", 0.0, data.symbol)
    
    def estimate_profit(self, signal: Signal) -> float:
        if signal.action == "buy" and signal.target_price:
            return 0.015  # 1.5% expected
        return 0.0
```

### Swing Strategy Template  
```python
class TrendFollowing(Strategy):
    """Multi-day trend following, no PDT limits"""
    
    @property
    def config(self) -> StrategyConfig:
        return StrategyConfig(
            day_trade_budget=0.0,  # Never day trades
            min_hold_period="2 days",
            preferred_timeframe="1hour",
            max_position_size=0.2,  # Larger positions for swings
            stop_loss=0.05  # Wider 5% stop for swings
        )
    
    def analyze(self, data: MarketData) -> Signal:
        # Check trend indicators
        if self._is_uptrend(data):
            return Signal(
                action="buy",
                confidence=0.75,  # Lower confidence OK for swings
                symbol=data.symbol,
                metadata={"trend_strength": 0.8}
            )
        elif self._is_downtrend(data):
            return Signal("sell", 0.75, data.symbol)
            
        return Signal("hold", 0.0, data.symbol)
    
    def estimate_profit(self, signal: Signal) -> float:
        # Swing trades target larger moves
        return 0.05  # 5% expected over multiple days
```

## PDT Budget Allocation Rules

1. **Total Budget Check**:
   ```python
   total_budget = sum(s.config.day_trade_budget for s in strategies)
   assert total_budget <= 1.0  # Can't exceed 100% of 3 trades
   ```

2. **Confidence Thresholds**:
   - Day trades: confidence >= 0.85
   - Swing trades: confidence >= 0.60

3. **Allocation Priority**:
   ```python
   score = confidence * estimated_profit * historical_win_rate
   ```

## Strategy Registration Pattern
```python
# In strategies/__init__.py
from .base import Strategy
from .opening_range import OpeningRangeBreakout
from .trend_following import TrendFollowing

AVAILABLE_STRATEGIES = {
    "opening_range": OpeningRangeBreakout,
    "trend_following": TrendFollowing,
}

def load_strategies(config: Dict) -> List[Strategy]:
    """Load strategies based on configuration"""
    strategies = []
    for name, settings in config.items():
        if name in AVAILABLE_STRATEGIES:
            strategy_class = AVAILABLE_STRATEGIES[name]
            strategies.append(strategy_class(**settings))
    return strategies
```

## Integration with Events
```python
# Strategy emitting signal via event bus
from ..events import event_bus, EventType, SignalEvent

class StrategyRunner:
    def run_strategy(self, strategy: Strategy, data: MarketData):
        signal = strategy.analyze(data)
        
        if signal.confidence > 0.0 and signal.action != "hold":
            event = SignalEvent(
                strategy=strategy.__class__.__name__,
                symbol=signal.symbol,
                action=signal.action,
                confidence=signal.confidence,
                estimated_profit=strategy.estimate_profit(signal),
                timestamp=datetime.now()
            )
            event_bus.emit(EventType.SIGNAL_GENERATED, event)
```