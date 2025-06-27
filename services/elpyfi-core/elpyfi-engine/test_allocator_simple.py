#!/usr/bin/env python3
"""
Simplified unit tests for PDT Allocator that match actual implementation
"""

import unittest
from allocator import PDTAllocator, AllocationRequest, get_position_size, RISK_RULES
from events import TradeRequestEvent, SignalEvent


class TestPDTAllocatorSimple(unittest.TestCase):
    def setUp(self):
        """Create fresh allocator for each test"""
        self.allocator = PDTAllocator()
        
    def test_request_allocation(self):
        """Test request allocation adds to pending queue"""
        # Create a signal and trade request
        signal = SignalEvent("test_strat", "AAPL", "buy", 0.8, 1000)
        trade_request = TradeRequestEvent(signal)
        
        # Request allocation
        result = self.allocator.request_allocation(trade_request)
        
        # Should return False (queued for batch)
        self.assertFalse(result)
        
        # Should be in pending requests
        self.assertEqual(len(self.allocator.pending_requests), 1)
        self.assertEqual(self.allocator.pending_requests[0].trade_request, trade_request)
        
    def test_allocation_scoring(self):
        """Test allocation request scoring"""
        signal = SignalEvent("test_strat", "AAPL", "buy", 0.8, 1000)
        trade_request = TradeRequestEvent(signal)
        
        allocation = AllocationRequest(trade_request)
        score = allocation.calculate_score(historical_success=0.9)
        
        # Score = confidence × profit × history
        expected_score = 0.8 * 1000 * 0.9
        self.assertEqual(score, expected_score)
        self.assertEqual(allocation.score, expected_score)
        
    def test_weekly_allocations(self):
        """Test weekly batch allocation"""
        # Create multiple requests with different scores
        requests = []
        for i in range(5):
            signal = SignalEvent(
                f"strat{i}", 
                f"STOCK{i}", 
                "buy", 
                0.5 + i * 0.1,  # Increasing confidence
                100 + i * 200   # Increasing profit
            )
            trade_request = TradeRequestEvent(signal)
            self.allocator.request_allocation(trade_request)
            requests.append(trade_request)
            
        # Get allocations with 3 available trades
        approved = self.allocator.get_weekly_allocations(available_trades=3)
        
        # Should allocate 2 (3 - 1 emergency reserve)
        self.assertEqual(len(approved), 2)
        
        # Should be highest scoring ones (STOCK4 and STOCK3)
        approved_symbols = [req.signal_event.symbol for req in approved]
        self.assertIn("STOCK4", approved_symbols)
        self.assertIn("STOCK3", approved_symbols)
        
        # Pending requests should be cleared
        self.assertEqual(len(self.allocator.pending_requests), 0)
        
    def test_emergency_trade(self):
        """Test emergency trade for stop-loss"""
        # Regular trade - should not use emergency
        signal = SignalEvent("test", "AAPL", "sell", 0.9, -100)
        trade_request = TradeRequestEvent(signal)
        self.assertFalse(self.allocator.use_emergency_trade(trade_request))
        
        # Stop-loss trade - should use emergency
        signal_sl = SignalEvent(
            "test", "AAPL", "sell", 0.9, -100,
            metadata={"stop_loss": True}
        )
        trade_request_sl = TradeRequestEvent(signal_sl)
        self.assertTrue(self.allocator.use_emergency_trade(trade_request_sl))
        
    def test_position_sizing(self):
        """Test position size calculation"""
        portfolio_value = 100000
        position_size = get_position_size(portfolio_value)
        
        # Should be 2% of portfolio
        expected_size = portfolio_value * RISK_RULES["max_position_size"]
        self.assertEqual(position_size, expected_size)
        self.assertEqual(position_size, 2000)  # 2% of 100k
        
    def test_empty_allocation(self):
        """Test allocation with no requests"""
        approved = self.allocator.get_weekly_allocations(available_trades=3)
        self.assertEqual(len(approved), 0)


if __name__ == "__main__":
    unittest.main()