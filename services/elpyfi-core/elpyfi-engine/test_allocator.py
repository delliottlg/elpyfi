#!/usr/bin/env python3
"""
Unit tests for PDT Allocator
Tests trade prioritization when at PDT limits
"""

import unittest
from datetime import datetime, timedelta
from allocator import PDTAllocator
from events import TradeRequestEventEvent


class TestPDTAllocator(unittest.TestCase):
    def setUp(self):
        """Create fresh allocator for each test"""
        self.allocator = PDTAllocator()
        
    def test_single_request_approval(self):
        """Test single trade request gets approved"""
        request = TradeRequestEventEvent(
            strategy="momentum",
            symbol="AAPL",
            confidence=0.85,
            expected_profit=500
        )
        
        decisions = self.allocator.allocate_trades([request], trades_available=3)
        
        self.assertEqual(len(decisions), 1)
        self.assertTrue(decisions[0].approved)
        self.assertEqual(decisions[0].symbol, "AAPL")
        self.assertIn("trades available", decisions[0].reason)
        
    def test_prioritization_by_score(self):
        """Test trades are prioritized by score (confidence × profit)"""
        requests = [
            TradeRequestEvent("strat1", "LOW", 0.5, 100),      # Score: 50
            TradeRequestEvent("strat2", "HIGH", 0.9, 1000),    # Score: 900
            TradeRequestEvent("strat3", "MED", 0.7, 500),      # Score: 350
        ]
        
        # Only 2 trades available
        decisions = self.allocator.allocate_trades(requests, trades_available=2)
        
        # Should approve HIGH and MED, reject LOW
        approved = [d for d in decisions if d.approved]
        rejected = [d for d in decisions if not d.approved]
        
        self.assertEqual(len(approved), 2)
        self.assertEqual(len(rejected), 1)
        
        # Check correct ones approved
        approved_symbols = [d.symbol for d in approved]
        self.assertIn("HIGH", approved_symbols)
        self.assertIn("MED", approved_symbols)
        self.assertEqual(rejected[0].symbol, "LOW")
        
    def test_no_trades_available(self):
        """Test all trades rejected when no slots available"""
        requests = [
            TradeRequestEvent("strat1", "AAPL", 0.9, 1000),
            TradeRequestEvent("strat2", "GOOGL", 0.8, 800),
        ]
        
        decisions = self.allocator.allocate_trades(requests, trades_available=0)
        
        self.assertEqual(len(decisions), 2)
        self.assertTrue(all(not d.approved for d in decisions))
        self.assertTrue(all("No day trades available" in d.reason for d in decisions))
        
    def test_strategy_history_bonus(self):
        """Test strategies with history get priority"""
        now = datetime.now()
        
        # First, strat1 gets a successful trade
        request1 = TradeRequestEvent("strat1", "AAPL", 0.7, 500)
        self.allocator.allocate_trades([request1], trades_available=3)
        
        # Record it as successful
        self.allocator.record_outcome("AAPL", "strat1", True, 500)
        
        # Now both strategies compete
        requests = [
            TradeRequestEvent("strat1", "MSFT", 0.7, 500),   # Has history
            TradeRequestEvent("strat2", "GOOGL", 0.7, 500),  # No history
        ]
        
        # With only 1 slot, strat1 should win due to history
        decisions = self.allocator.allocate_trades(requests, trades_available=1)
        
        approved = [d for d in decisions if d.approved]
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0].symbol, "MSFT")  # strat1's trade
        
    def test_weekly_batch_mode(self):
        """Test weekly batch allocation mode"""
        # Create 10 requests for the week
        requests = []
        base_time = datetime.now()
        
        for i in range(10):
            requests.append(TradeRequestEvent(
                f"strat{i % 3}",  # 3 different strategies
                f"STOCK{i}",
                0.5 + (i * 0.05),  # Varying confidence
                100 + (i * 100)  # Varying profit
            ))
            
        # Process as weekly batch with 15 trades for the week
        decisions = self.allocator.process_weekly_batch(requests, weekly_limit=15)
        
        # Should approve highest scoring ones
        approved = [d for d in decisions if d.approved]
        rejected = [d for d in decisions if not d.approved]
        
        # Can't approve more than requested
        self.assertLessEqual(len(approved), 10)
        
        # Should prioritize higher scores
        approved_indices = [int(d.symbol.replace("STOCK", "")) for d in approved]
        rejected_indices = [int(d.symbol.replace("STOCK", "")) for d in rejected]
        
        if approved_indices and rejected_indices:
            # Highest approved score should be >= lowest rejected score
            min_approved = min(approved_indices)
            max_rejected = max(rejected_indices)
            self.assertGreaterEqual(min_approved, max_rejected)
            
    def test_record_outcomes(self):
        """Test outcome recording affects future allocations"""
        # Strategy 1: 2 wins
        self.allocator.record_outcome("AAPL", "winner", True, 1000)
        self.allocator.record_outcome("GOOGL", "winner", True, 800)
        
        # Strategy 2: 2 losses  
        self.allocator.record_outcome("MSFT", "loser", False, -500)
        self.allocator.record_outcome("TSLA", "loser", False, -300)
        
        # Now they compete with same confidence/profit
        requests = [
            TradeRequestEvent("winner", "NEW1", 0.7, 500),
            TradeRequestEvent("loser", "NEW2", 0.7, 500),
        ]
        
        # Winner should get priority
        decisions = self.allocator.allocate_trades(requests, trades_available=1)
        approved = [d for d in decisions if d.approved]
        
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0].symbol, "NEW1")  # winner's trade
        
    def test_get_strategy_stats(self):
        """Test strategy statistics calculation"""
        # Record some outcomes
        self.allocator.record_outcome("AAPL", "strat1", True, 1000)
        self.allocator.record_outcome("GOOGL", "strat1", True, 500)
        self.allocator.record_outcome("MSFT", "strat1", False, -200)
        
        stats = self.allocator.get_strategy_stats()
        
        self.assertIn("strat1", stats)
        strat1_stats = stats["strat1"]
        
        self.assertEqual(strat1_stats["total_trades"], 3)
        self.assertEqual(strat1_stats["winning_trades"], 2)
        self.assertEqual(strat1_stats["total_profit"], 1300)
        self.assertAlmostEqual(strat1_stats["win_rate"], 0.667, places=2)
        
    def test_empty_request_list(self):
        """Test handling empty request list"""
        decisions = self.allocator.allocate_trades([], trades_available=3)
        self.assertEqual(len(decisions), 0)
        
    def test_equal_scores_fifo(self):
        """Test FIFO ordering for equal scores"""
        now = datetime.now()
        requests = [
            TradeRequestEvent("strat1", "FIRST", 0.7, 500),
            TradeRequestEvent("strat2", "SECOND", 0.7, 500),
            TradeRequestEvent("strat3", "THIRD", 0.7, 500),
        ]
        
        # Only 2 slots
        decisions = self.allocator.allocate_trades(requests, trades_available=2)
        approved = [d for d in decisions if d.approved]
        
        # Should approve first two (FIFO)
        self.assertEqual(len(approved), 2)
        approved_symbols = [d.symbol for d in approved]
        self.assertIn("FIRST", approved_symbols)
        self.assertIn("SECOND", approved_symbols)


if __name__ == "__main__":
    unittest.main()