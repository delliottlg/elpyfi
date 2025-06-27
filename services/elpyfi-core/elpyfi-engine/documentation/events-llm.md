# Events System - LLM Context

## File: events.py

### Imports
```python
from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
```

### EventBus Implementation
```python
class EventBus:
    _subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    Methods:
    - subscribe(event_type: str, handler: Callable) -> None
    - emit(event_type: str, data: Any = None) -> None
    - unsubscribe(event_type: str, handler: Callable) -> None
```

### Event Type Constants
```python
class EventType:
    SIGNAL_GENERATED = "signal_generated"      # Strategy -> Execution
    DAY_TRADE_REQUESTED = "day_trade_requested" # Strategy -> PDT Allocator
    DAY_TRADE_APPROVED = "day_trade_approved"   # PDT Allocator -> Strategy
    POSITION_OPENED = "position_opened"        # Execution -> All
    POSITION_CLOSED = "position_closed"        # Execution -> All
    METRICS_UPDATED = "metrics_updated"        # Any -> Monitoring
```

### Event Data Structures
```python
@dataclass
class SignalEvent:
    strategy: str          # Which strategy generated this
    symbol: str           # Trading symbol (AAPL, BTC-USD)
    action: str           # "buy", "sell", "hold"
    confidence: float     # 0.0-1.0 confidence score
    estimated_profit: float # Expected return as decimal
    timestamp: datetime

@dataclass  
class TradeRequestEvent:
    signal_event: SignalEvent
    is_day_trade: bool     # True if closing same day
    requested_size: float  # Position size as portfolio %

@dataclass
class TradeApprovalEvent:
    trade_request: TradeRequestEvent
    approved: bool
    reason: Optional[str] = None  # Why approved/rejected

@dataclass
class PositionEvent:
    symbol: str
    action: str       # "opened" or "closed"
    size: float       # Share count or dollar amount
    price: float      # Execution price
    timestamp: datetime
    order_id: str     # Broker order ID

@dataclass
class MetricsEvent:
    metric_type: str  # "win_rate", "profit", "sharpe", etc
    value: float
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
```

### Global Instance
```python
event_bus = EventBus()  # Singleton for entire engine
```

## Usage Patterns

### Publisher Pattern
```python
# In strategy
signal = SignalEvent(...)
event_bus.emit(EventType.SIGNAL_GENERATED, signal)
```

### Subscriber Pattern  
```python
# In execution module
def handle_signal(signal: SignalEvent):
    # Process signal
    pass

event_bus.subscribe(EventType.SIGNAL_GENERATED, handle_signal)
```

### Event Flow Sequences

1. **Trading Signal Flow**:
   ```
   Strategy.analyze() 
   -> emit(SIGNAL_GENERATED, SignalEvent)
   -> Execution.handle_signal()
   -> emit(POSITION_OPENED, PositionEvent)
   ```

2. **Day Trade Request Flow**:
   ```
   Strategy detects day trade opportunity
   -> emit(DAY_TRADE_REQUESTED, TradeRequestEvent)
   -> PDT Allocator evaluates
   -> emit(DAY_TRADE_APPROVED, TradeApprovalEvent)
   -> Strategy proceeds or aborts
   ```

## Implementation Notes

- EventBus is synchronous (handlers called immediately)
- No event persistence (events are fire-and-forget)
- No built-in error handling (handlers must catch exceptions)
- Thread-safety not implemented (single-threaded assumption)

## Testing Approach
```python
# Can test with mock handlers
mock_handler = Mock()
event_bus.subscribe(EventType.SIGNAL_GENERATED, mock_handler)
event_bus.emit(EventType.SIGNAL_GENERATED, test_signal)
mock_handler.assert_called_once_with(test_signal)
```