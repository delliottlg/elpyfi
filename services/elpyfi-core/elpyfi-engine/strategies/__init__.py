"""
ElPyFi Strategy Framework

This module provides the base classes and utilities for building
trading strategies that work within PDT restrictions.
"""

from typing import Dict, List, Type

# Base imports
from strategies.base import Strategy
from strategies.models import StrategyConfig, Signal, MarketData

# Import strategies
from strategies.solar_flare import SolarFlareStrategy

# Strategy registry
AVAILABLE_STRATEGIES: Dict[str, Type] = {
    "solar_flare": SolarFlareStrategy
}

def register_strategy(name: str, strategy_class: Type):
    """Register a strategy for use by the engine"""
    AVAILABLE_STRATEGIES[name] = strategy_class

def load_strategies(config: Dict) -> List[Strategy]:
    """Load strategies based on configuration"""
    strategies = []
    for name, settings in config.items():
        if name in AVAILABLE_STRATEGIES:
            strategy_class = AVAILABLE_STRATEGIES[name]
            strategies.append(strategy_class(**settings))
        else:
            raise ValueError(f"Unknown strategy: {name}")
    return strategies