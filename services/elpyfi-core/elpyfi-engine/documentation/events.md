# Event System Documentation

## Overview

The event system is the communication backbone of ElPyFi Engine. It allows different components (strategies, execution, metrics) to communicate without knowing about each other directly.

## How It Works

Think of it like a bulletin board system:
- Components can **post messages** (emit events) 
- Components can **subscribe to updates** (listen for events)
- The EventBus delivers messages to all interested parties

## Core Components

### EventBus Class

The main messaging system with three methods:

```python
event_bus.subscribe("signal_generated", my_handler)  # Start listening
event_bus.emit("signal_generated", signal_data)      # Send a message
event_bus.unsubscribe("signal_generated", my_handler) # Stop listening
```

### Event Types

We have 6 main event types:

1. **SIGNAL_GENERATED** - A strategy found a trading opportunity
2. **DAY_TRADE_REQUESTED** - A strategy wants to use a day trade
3. **DAY_TRADE_APPROVED** - The PDT allocator approved the request
4. **POSITION_OPENED** - A trade was executed
5. **POSITION_CLOSED** - A position was exited
6. **METRICS_UPDATED** - Performance metrics changed

### Event Data Classes

Each event carries structured data:

- **SignalEvent**: Strategy name, symbol, action (buy/sell), confidence (0-1), profit estimate
- **TradeRequestEvent**: The signal plus whether it needs a day trade
- **TradeApprovalEvent**: Whether the request was approved and why
- **PositionEvent**: Details about opened/closed positions
- **MetricsEvent**: Performance metrics and metadata

## Usage Example

```python
from events import event_bus, EventType, SignalEvent
from datetime import datetime

# A strategy emitting a signal
def emit_trading_signal():
    signal = SignalEvent(
        strategy="momentum_scanner",
        symbol="AAPL",
        action="buy",
        confidence=0.85,
        estimated_profit=0.02,  # 2%
        timestamp=datetime.now()
    )
    event_bus.emit(EventType.SIGNAL_GENERATED, signal)

# Execution module listening for signals
def handle_signal(signal_event):
    if signal_event.confidence > 0.8:
        print(f"High confidence signal for {signal_event.symbol}")
        # Execute trade...

event_bus.subscribe(EventType.SIGNAL_GENERATED, handle_signal)
```

## Best Practices

1. **Always use EventType constants** - Don't hardcode strings
2. **Use the data classes** - They ensure consistent event structure
3. **Handle events quickly** - Don't block the event loop
4. **Unsubscribe when done** - Prevent memory leaks

## Benefits

- **Decoupling**: Strategies don't need to know about execution
- **Flexibility**: Easy to add new components that listen to events
- **Testability**: Can test components in isolation
- **Debugging**: Easy to log all events for analysis