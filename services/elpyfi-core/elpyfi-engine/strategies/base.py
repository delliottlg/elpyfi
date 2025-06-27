from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from strategies.models import StrategyConfig, Signal, MarketData


class Strategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, **kwargs):
        """Initialize strategy with optional parameters"""
        self.params = kwargs
        self._validate_config()
    
    def _validate_config(self):
        """Validate strategy configuration"""
        config = self.config
        # Config validation happens in StrategyConfig.__post_init__
        # This is where we'd add strategy-specific validation
    
    @property
    @abstractmethod
    def config(self) -> StrategyConfig:
        """
        Strategy configuration and constraints.
        
        Returns:
            StrategyConfig: Configuration including PDT budget, hold period, etc.
        """
        pass
    
    @abstractmethod
    def analyze(self, data: MarketData) -> Signal:
        """
        Analyze market data and generate trading signal.
        
        Args:
            data: Current market data including price, volume, indicators
            
        Returns:
            Signal: Trading signal with action, confidence, and targets
        """
        pass
    
    @abstractmethod
    def estimate_profit(self, signal: Signal) -> float:
        """
        Estimate potential profit for PDT allocation decisions.
        
        Args:
            signal: The signal to estimate profit for
            
        Returns:
            float: Expected profit as decimal (0.01 = 1%)
        """
        pass
    
    @property
    def name(self) -> str:
        """Get strategy name (defaults to class name)"""
        return self.__class__.__name__
    
    @property
    def is_day_trade_capable(self) -> bool:
        """Check if strategy can day trade"""
        return self.config.min_hold_period == "0 days"
    
    @property
    def uses_day_trades(self) -> bool:
        """Check if strategy wants day trade allocation"""
        return self.config.day_trade_budget > 0.0
    
    def should_emit_signal(self, signal: Signal) -> bool:
        """
        Determine if a signal should be emitted.
        Override to add custom filtering logic.
        
        Args:
            signal: The signal to check
            
        Returns:
            bool: True if signal should be emitted
        """
        return signal.action != "hold" and signal.confidence > 0.0