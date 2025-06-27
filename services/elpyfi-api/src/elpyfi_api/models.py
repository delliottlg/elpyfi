from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class Position(BaseModel):
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pl: float
    strategy: str


class Signal(BaseModel):
    strategy: str
    symbol: str
    action: str  # "buy", "sell", "hold", "proposed"
    confidence: float
    timestamp: datetime
    metadata: Optional[Dict] = {}


class Metrics(BaseModel):
    strategy: str
    total_trades: int
    win_rate: float
    profit_loss: float
    sharpe_ratio: float
    max_drawdown: float
