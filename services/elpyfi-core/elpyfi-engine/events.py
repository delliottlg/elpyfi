from typing import Dict, List, Callable, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe a handler function to an event type."""
        self._subscribers[event_type].append(handler)
    
    def emit(self, event_type: str, data: Any = None) -> None:
        """Emit an event to all subscribed handlers."""
        for handler in self._subscribers[event_type]:
            handler(data)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a handler from an event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)


# Event types
class EventType:
    SIGNAL_GENERATED = "signal_generated"
    DAY_TRADE_REQUESTED = "day_trade_requested"
    DAY_TRADE_APPROVED = "day_trade_approved"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    METRICS_UPDATED = "metrics_updated"
    MARKET_DATA_RECEIVED = "market_data_received"


# Event data classes
@dataclass
class SignalEvent:
    strategy: str
    symbol: str
    action: str  # "buy", "sell", "hold"
    confidence: float  # 0-1
    estimated_profit: float
    timestamp: datetime

@dataclass
class TradeRequestEvent:
    signal_event: SignalEvent
    is_day_trade: bool
    requested_size: float  # Position size as % of portfolio

@dataclass
class TradeApprovalEvent:
    trade_request: TradeRequestEvent
    approved: bool
    reason: Optional[str] = None

@dataclass
class PositionEvent:
    symbol: str
    action: str  # "opened" or "closed"
    size: float
    price: float
    timestamp: datetime
    order_id: str

@dataclass
class MetricsEvent:
    metric_type: str
    value: float
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


# Global event bus instance
event_bus = EventBus()