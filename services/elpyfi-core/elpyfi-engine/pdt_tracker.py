"""
PDT (Pattern Day Trading) Tracker

Tracks day trades to ensure compliance with the 3 trades per 5 business days rule.
"""

from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from events import event_bus, EventType
from allocator import PDTAllocator, RISK_RULES


@dataclass
class DayTrade:
    """Record of a day trade"""
    symbol: str
    open_time: datetime
    close_time: datetime
    strategy: str


class PDTTracker:
    """Tracks and enforces PDT rules"""
    
    def __init__(self):
        self.day_trades: List[DayTrade] = []
        self.week_start = self._get_week_start()
        self.allocator = PDTAllocator()
        self._setup_listeners()
    
    def _setup_listeners(self):
        """Listen for trade events"""
        event_bus.subscribe(EventType.DAY_TRADE_REQUESTED, self.handle_day_trade_request)
        event_bus.subscribe(EventType.POSITION_CLOSED, self.record_day_trade)
    
    def _get_week_start(self) -> datetime:
        """Get the start of the current trading week (Monday)"""
        today = datetime.now()
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday)
    
    def get_trades_this_week(self) -> int:
        """Count day trades in the current week"""
        current_week_start = self._get_week_start()
        
        # Reset if new week
        if current_week_start > self.week_start:
            self.week_start = current_week_start
            self.day_trades = [t for t in self.day_trades if t.open_time >= current_week_start]
        
        return len([t for t in self.day_trades if t.open_time >= self.week_start])
    
    def get_remaining_trades(self) -> int:
        """Get remaining day trades for the week"""
        return max(0, 3 - self.get_trades_this_week())
    
    def can_day_trade(self) -> bool:
        """Check if we can make another day trade"""
        return self.get_remaining_trades() > 0
    
    def handle_day_trade_request(self, request_event):
        """Process day trade requests with allocator"""
        if request_event.is_day_trade:
            # Check for emergency trades (stop losses)
            if self.allocator.use_emergency_trade(request_event):
                self._approve_trade(request_event, "Emergency stop-loss exit")
                return
            
            can_trade = self.can_day_trade()
            
            if can_trade:
                # Immediate approval
                self._approve_trade(request_event, "Day trade slot available")
            else:
                # Add to allocator queue
                self.allocator.request_allocation(request_event)
                self._reject_trade(request_event, 
                    f"PDT limit reached: {self.get_trades_this_week()}/3 trades used. "
                    "Request queued for weekly allocation.")
        else:
            # Not a day trade, auto-approve
            self._approve_trade(request_event, "Swing trade - no PDT restrictions")
    
    def _approve_trade(self, request_event, reason: str):
        """Approve and record a trade"""
        from events import TradeApprovalEvent
        approval = TradeApprovalEvent(
            trade_request=request_event,
            approved=True,
            reason=reason
        )
        event_bus.emit(EventType.DAY_TRADE_APPROVED, approval)
        
        if request_event.is_day_trade:
            # Record the day trade
            self.day_trades.append(DayTrade(
                symbol=request_event.signal_event.symbol,
                open_time=datetime.now(),
                close_time=datetime.now(),  # Will update when closed
                strategy=request_event.signal_event.strategy
            ))
    
    def _reject_trade(self, request_event, reason: str):
        """Reject a trade request"""
        from events import TradeApprovalEvent
        approval = TradeApprovalEvent(
            trade_request=request_event,
            approved=False,
            reason=reason
        )
        event_bus.emit(EventType.DAY_TRADE_APPROVED, approval)
    
    def record_day_trade(self, position_event):
        """Record when a day trade is closed"""
        # Update close time for matching trades
        for trade in self.day_trades:
            if (trade.symbol == position_event.symbol and 
                trade.close_time == trade.open_time):  # Not yet closed
                trade.close_time = position_event.timestamp
                break
    
    def get_status(self) -> Dict:
        """Get current PDT and risk status"""
        return {
            "trades_used": self.get_trades_this_week(),
            "trades_remaining": self.get_remaining_trades(),
            "can_day_trade": self.can_day_trade(),
            "week_start": self.week_start.isoformat(),
            "recent_trades": [
                {
                    "symbol": t.symbol,
                    "strategy": t.strategy,
                    "time": t.open_time.isoformat()
                }
                for t in self.day_trades[-5:]  # Last 5 trades
            ],
            "risk_rules": RISK_RULES,
            "pending_allocations": len(self.allocator.pending_requests),
            "emergency_trades_reserved": self.allocator.emergency_reserve
        }


# Global PDT tracker instance
pdt_tracker = PDTTracker()