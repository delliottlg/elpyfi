"""
Solar Flare Momentum Strategy

Theory: Solar activity disrupts HFT algorithms, creating momentum opportunities.
We ride the electromagnetic waves to tendie town! 🌞⚡💰
"""

from datetime import datetime
from strategies.base import Strategy
from strategies.models import StrategyConfig, Signal, MarketData
import random  # Fallback if API fails
import requests
import logging

logger = logging.getLogger(__name__)


class SolarFlareStrategy(Strategy):
    """Trade momentum during geomagnetic storms"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fibonacci_levels = [0.236, 0.382, 0.618, 0.786, 1.0]
        self.solar_prime_hours = range(10, 15)  # 10 AM - 2 PM EST
        self.test_mode = kwargs.get('test_mode', False)  # Override for testing
        
    @property
    def config(self) -> StrategyConfig:
        return StrategyConfig(
            day_trade_budget=0.33,  # Wants 1 of 3 weekly day trades
            min_hold_period="0 days",  # Day trading the solar waves
            preferred_timeframe="5min",  # Need quick data for storm surfing
            max_position_size=0.05,  # 5% - electromagnetic interference is risky
            stop_loss=0.015  # Tight 1.5% stop - solar flares are unpredictable
        )
    
    def analyze(self, data: MarketData) -> Signal:
        # Check if we're in solar prime time (skip in test mode)
        if not self.test_mode:
            current_hour = data.timestamp.hour
            if current_hour not in self.solar_prime_hours:
                return Signal("hold", 0.0, data.symbol)
        
        # Get "K-index" (fake for demo - would call space weather API)
        k_index = self._get_solar_k_index()
        
        # Need geomagnetic storm conditions (K-index > 5)
        if k_index < 5:
            return Signal("hold", 0.0, data.symbol)
        
        # Check VWAP deviation
        vwap = data.indicators.get('vwap', data.current_price) if data.indicators else data.current_price
        vwap_deviation = (data.current_price - vwap) / vwap
        
        # Look for breakout with volume during solar storm
        if (vwap_deviation > 0.002 and  # Price above VWAP by 0.2%
            data.volume > data.indicators.get('avg_volume', data.volume) * 1.5):  # Volume spike
            
            # Calculate cosmic confidence
            base_confidence = 0.75
            solar_multiplier = min(k_index / 9.0, 1.0)  # Max out at K=9
            aurora_bonus = 0.1 if k_index >= 7 else 0  # Aurora borealis visible!
            
            confidence = base_confidence * solar_multiplier + aurora_bonus
            
            # Set Fibonacci targets
            target_price = data.current_price * (1 + self.fibonacci_levels[1])  # 38.2% target
            stop_price = data.current_price * 0.985  # 1.5% stop
            
            return Signal(
                action="buy",
                confidence=min(confidence, 0.95),  # Cap at 95%
                symbol=data.symbol,
                target_price=target_price,
                stop_price=stop_price,
                metadata={
                    "k_index": k_index,
                    "solar_status": self._get_solar_status(k_index),
                    "electromagnetic_level": "MAXIMUM TENDIES" if k_index >= 8 else "Charged"
                }
            )
        
        # Check for short opportunity during solar reversal
        elif (vwap_deviation < -0.002 and 
              data.volume > data.indicators.get('avg_volume', data.volume) * 1.5):
            
            confidence = 0.65 * (k_index / 9.0)  # Lower confidence for shorts
            
            return Signal(
                action="sell",
                confidence=confidence,
                symbol=data.symbol,
                target_price=data.current_price * (1 - self.fibonacci_levels[0]),  # 23.6% target
                stop_price=data.current_price * 1.015,
                metadata={"k_index": k_index, "solar_status": "Magnetic Reversal"}
            )
        
        return Signal("hold", 0.0, data.symbol)
    
    def estimate_profit(self, signal: Signal) -> float:
        if signal.action == "buy":
            # Higher K-index = higher profit potential (more HFT disruption)
            k_index = signal.metadata.get("k_index", 5) if signal.metadata else 5
            base_profit = 0.015  # 1.5% base
            solar_boost = (k_index - 5) * 0.002  # +0.2% per K point above 5
            return min(base_profit + solar_boost, 0.03)  # Cap at 3%
        elif signal.action == "sell":
            return 0.01  # Conservative 1% for shorts
        return 0.0
    
    def _get_solar_k_index(self) -> int:
        """Get current planetary K-index from NOAA Space Weather API"""
        # Test mode: always return high K-index
        if self.test_mode:
            logger.info("🌞 Test mode: Using K-index 7 (Aurora level!)")
            return 7
            
        try:
            # Real space weather data!
            response = requests.get(
                "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
                timeout=2
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                # Get the latest K-index (last item in array)
                latest_k = int(data[-1]['k_index'])
                logger.info(f"🌞 Real K-index from NOAA: {latest_k}")
                return max(1, min(9, latest_k))  # Ensure 1-9 range
                
        except Exception as e:
            logger.warning(f"Failed to get solar data: {e}, using random")
        
        # Fallback to weighted random if API fails
        weights = [30, 25, 20, 10, 8, 4, 2, 0.8, 0.2]  # K-index 1-9 weights
        return random.choices(range(1, 10), weights=weights)[0]
    
    def _get_solar_status(self, k_index: int) -> str:
        """Convert K-index to fun status"""
        statuses = {
            1: "Solar Snooze 😴",
            2: "Cosmic Calm",
            3: "Electromagnetic Whispers",
            4: "Solar Stirring",
            5: "STORM DETECTED! 🌩️",
            6: "Major Electromagnetic Event!",
            7: "AURORA TRADING ZONE! 🌈",
            8: "MAXIMUM SOLAR CHAOS! ⚡⚡",
            9: "CARRINGTON EVENT 2.0!!! 🌞💥"
        }
        return statuses.get(k_index, "Unknown Solar Status")