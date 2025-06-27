from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class Indicator(BaseModel):
    name: str
    value: float
    timeframe: TimeFrame
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MarketCondition(BaseModel):
    trend: str = Field(..., description="Overall market trend: bullish, bearish, or neutral")
    volatility: float = Field(..., ge=0, le=1, description="Volatility level from 0 to 1")
    volume: float = Field(..., description="Trading volume")
    support_levels: List[float] = Field(default_factory=list)
    resistance_levels: List[float] = Field(default_factory=list)


class Signal(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, BTC-USD)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: SignalType
    price: float = Field(..., gt=0)
    indicators: List[Indicator] = Field(default_factory=list)
    market_conditions: Optional[MarketCondition] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="low, medium, high")
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    position_size_recommendation: Optional[float] = Field(None, ge=0, le=1)
    max_loss_amount: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


class TradingConstraints(BaseModel):
    pdt_trades_remaining: Optional[int] = Field(None, description="Remaining day trades for PDT")
    account_balance: Optional[float] = None
    buying_power: Optional[float] = None
    existing_positions: List[str] = Field(default_factory=list)


class Decision(BaseModel):
    signal_id: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recommendation: SignalType
    confidence: float = Field(..., ge=0, le=1, description="Confidence level from 0 to 1")
    explanation: str = Field(..., description="Human-readable explanation of the decision")
    factors: List[str] = Field(..., description="Key factors that influenced the decision")
    risk_assessment: RiskAssessment
    alternative_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    signal: Signal
    constraints: Optional[TradingConstraints] = None
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User trading preferences (risk tolerance, strategy type, etc.)"
    )


class BacktestDecision(BaseModel):
    signal: Signal
    decision: Decision
    actual_outcome: Optional[Dict[str, Any]] = Field(
        None,
        description="What actually happened after this signal"
    )
    performance_metrics: Optional[Dict[str, float]] = Field(
        None,
        description="P&L, accuracy, etc."
    )