# ElPyFi Engine - LLM Context

## System Purpose
Algorithmic trading engine with PDT restrictions (3 day trades/week for <$25k accounts).

## Architecture Pattern
Event-driven pub/sub messaging between decoupled components.

## Key Constraints
- MAX_DAY_TRADES_PER_WEEK = 3
- MAX_FILE_LINES = 200  
- SINGLE_RESPONSIBILITY = True

## Component Map
```python
components = {
    "events.py": "Event bus for inter-component communication",
    "engine.py": "Main event loop, ~50 lines, coordinates flow",
    "strategies/base.py": "ABC for Strategy interface",
    "strategies/models.py": "Signal, StrategyConfig dataclasses",
    "execution/": "Order management, broker API integration"
}
```

## Event Flow
```
MarketData -> Strategy.analyze() -> SignalEvent -> DayTradeRequest? -> Execution -> PositionEvent
```

## Critical Interfaces
```python
# Strategy must implement:
class Strategy(ABC):
    @property
    @abstractmethod 
    def config(self) -> StrategyConfig: pass
    
    @abstractmethod
    def analyze(self, data: MarketData) -> Signal: pass
    
    @abstractmethod
    def estimate_profit(self, signal: Signal) -> float: pass

# StrategyConfig must contain:
class StrategyConfig:
    day_trade_budget: float  # 0-1 portion of weekly 3 trades
    min_hold_period: str     # "0 days" = day trade capable
    preferred_timeframe: str # data granularity needed
```

## PDT Logic
- Strategies REQUEST day trades via events
- PDT Allocator (external service) APPROVES based on:
  - signal.confidence * signal.estimated_profit * strategy.historical_success
- Only top 3 requests per week get approved

## Implementation Status
- [x] Event system (events.py)
- [ ] Strategy framework (strategies/)
- [ ] Main engine loop (engine.py)
- [ ] Execution module (execution/)

## Integration Points
- External: pyfi-api (REST/WebSocket), pyfi-arbiter (PDT allocator), pyfi-ai (decision layer)
- Database: PostgreSQL for signals, trades, pdt_tracking tables
- Broker: Via execution module (Alpaca, IBKR, etc.)