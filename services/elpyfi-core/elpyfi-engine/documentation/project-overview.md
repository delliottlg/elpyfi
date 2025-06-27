# ElPyFi Engine Documentation

## Overview

ElPyFi Engine is the core trading logic component of the ElPyFi Trading System. It's designed to be a minimal, event-driven algorithmic trading engine that works within PDT (Pattern Day Trading) restrictions for accounts under $25k.

## Key Features

- **Event-Driven Architecture**: All components communicate through events, not direct calls
- **PDT-Aware**: Built from the ground up to respect the 3 day trades per week limit
- **Strategy Agnostic**: Supports multiple trading strategies running in parallel
- **AI-Ready**: Clean interfaces designed for AI integration and decision making

## Project Structure

```
elpyfi-engine/
├── engine.py          # Main event loop (entry point)
├── events.py          # Event bus and event types
├── strategies/        # Trading strategy implementations
│   ├── base.py       # Abstract base class for all strategies
│   └── models.py     # Data structures (Signal, StrategyConfig)
└── execution/        # Order management and broker integration
```

## Design Philosophy

1. **Minimal Complexity**: Each file under 200 lines, single responsibility
2. **Event-First**: Components are decoupled through events
3. **PDT as a Feature**: The 3-trade limit forces better strategy selection
4. **Testable**: Clean interfaces make backtesting straightforward

## How It Works

1. The engine starts and initializes the event bus
2. Strategies subscribe to market data events
3. When market data arrives, strategies analyze and emit signals
4. The execution module listens for approved signals
5. Trades are executed and results are broadcast back

## PDT Management

The system tracks day trades carefully:
- Each strategy declares if it needs day trades
- Strategies compete for the weekly allocation of 3 trades
- Only highest confidence signals get approved for day trading
- Swing trades (held overnight) have no limits

## Next Steps

See individual component documentation:
- [Event System](./events.md)
- [Strategy Framework](./strategies.md)
- [Execution Module](./execution.md)