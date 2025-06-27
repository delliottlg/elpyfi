"""
PDT Allocator - Decides which strategies get precious day trades

Simple scoring system: confidence × expected_profit × historical_success
"""

from typing import List, Optional
from dataclasses import dataclass
from events import TradeRequestEvent


@dataclass
class AllocationRequest:
    """Request for day trade allocation"""
    trade_request: TradeRequestEvent
    score: float = 0.0
    
    def calculate_score(self, historical_success: float = 0.8):
        """Score = confidence × profit × history"""
        signal = self.trade_request.signal_event
        self.score = (
            signal.confidence * 
            signal.estimated_profit * 
            historical_success
        )
        return self.score


class PDTAllocator:
    """Manages day trade allocation when multiple strategies compete"""
    
    def __init__(self):
        self.pending_requests: List[AllocationRequest] = []
        self.emergency_reserve = 1  # Keep 1 trade for emergencies
    
    def request_allocation(self, trade_request: TradeRequestEvent) -> bool:
        """Request a day trade allocation"""
        allocation = AllocationRequest(trade_request)
        allocation.calculate_score()
        self.pending_requests.append(allocation)
        return False  # Always queue for weekly batch
    
    def get_weekly_allocations(self, available_trades: int) -> List[TradeRequestEvent]:
        """Get top N requests for the week"""
        # Keep emergency reserve
        trades_to_allocate = max(0, available_trades - self.emergency_reserve)
        
        # Sort by score
        self.pending_requests.sort(key=lambda x: x.score, reverse=True)
        
        # Get top requests
        approved = []
        for i in range(min(trades_to_allocate, len(self.pending_requests))):
            approved.append(self.pending_requests[i].trade_request)
        
        # Clear old requests
        self.pending_requests = []
        
        return approved
    
    def use_emergency_trade(self, trade_request: TradeRequestEvent) -> bool:
        """Use emergency reserve for stop-loss exits"""
        # Only for closing positions at a loss
        signal = trade_request.signal_event
        if signal.action == "sell" and signal.metadata and signal.metadata.get("stop_loss"):
            return True
        return False


# Risk rules configuration
RISK_RULES = {
    "max_position_size": 0.02,  # 2% of portfolio
    "max_daily_loss": 0.05,     # 5% daily stop
    "max_open_positions": 10,
}

def get_position_size(portfolio_value: float) -> float:
    """Calculate position size based on risk rules"""
    return portfolio_value * RISK_RULES["max_position_size"]