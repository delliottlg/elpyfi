#!/usr/bin/env python3
"""
Unit tests for PDT (Pattern Day Trading) Tracker
Tests trade tracking, limit enforcement, and week transitions
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from pdt_tracker import PDTTracker


class TestPDTTracker(unittest.TestCase):
    def setUp(self):
        """Create fresh tracker for each test"""
        self.tracker = PDTTracker()
        
    def test_initial_state(self):
        """Test tracker starts with correct initial state"""
        status = self.tracker.get_status()
        self.assertEqual(status['trades_used'], 0)
        self.assertEqual(status['trades_remaining'], 3)
        self.assertTrue(status['can_day_trade'])
        self.assertEqual(status['emergency_trades_reserved'], 1)
        
    def test_record_trade(self):
        """Test recording trades updates counts"""
        self.tracker.record_day_trade("AAPL")
        status = self.tracker.get_status()
        
        self.assertEqual(status['trades_used'], 1)
        self.assertEqual(status['trades_remaining'], 2)
        self.assertTrue(status['can_day_trade'])
        
        # Record more trades
        self.tracker.record_day_trade("GOOGL")
        self.tracker.record_day_trade("MSFT")
        
        status = self.tracker.get_status()
        self.assertEqual(status['trades_used'], 3)
        self.assertEqual(status['trades_remaining'], 0)
        self.assertFalse(status['can_day_trade'])  # At limit
        
    def test_emergency_trade(self):
        """Test emergency trade functionality"""
        # Use up regular trades
        self.tracker.record_day_trade("AAPL")
        self.tracker.record_day_trade("GOOGL")
        self.tracker.record_day_trade("MSFT")
        
        # Should not be able to day trade normally
        self.assertFalse(self.tracker.can_day_trade())
        
        # But emergency should work
        self.assertTrue(self.tracker.can_emergency_trade("TSLA"))
        self.tracker.record_emergency_trade("TSLA")
        
        # Now fully at limit
        self.assertFalse(self.tracker.can_emergency_trade("AMD"))
        
    def test_week_transition(self):
        """Test trades reset after 5 business days"""
        # Record trades on Monday
        monday = datetime(2024, 1, 1, 10, 0)  # A Monday
        with patch('pdt_tracker.datetime') as mock_dt:
            mock_dt.now.return_value = monday
            self.tracker.record_day_trade("AAPL")
            self.tracker.record_day_trade("GOOGL")
            self.tracker.record_day_trade("MSFT")
            
        # Check we're at limit
        self.assertEqual(self.tracker.get_status()['trades_used'], 3)
        self.assertFalse(self.tracker.can_day_trade())
        
        # Move to next Monday (5 business days later)
        next_monday = monday + timedelta(days=7)
        with patch('pdt_tracker.datetime') as mock_dt:
            mock_dt.now.return_value = next_monday
            
            # Should have reset
            status = self.tracker.get_status()
            self.assertEqual(status['trades_used'], 0)
            self.assertEqual(status['trades_remaining'], 3)
            self.assertTrue(status['can_day_trade'])
            
    def test_trade_within_week(self):
        """Test trades don't reset within same week"""
        # Record trade on Monday
        monday = datetime(2024, 1, 1, 10, 0)
        with patch('pdt_tracker.datetime') as mock_dt:
            mock_dt.now.return_value = monday
            self.tracker.record_day_trade("AAPL")
            
        # Check on Wednesday (same week)
        wednesday = monday + timedelta(days=2)
        with patch('pdt_tracker.datetime') as mock_dt:
            mock_dt.now.return_value = wednesday
            
            # Should still have the trade recorded
            status = self.tracker.get_status()
            self.assertEqual(status['trades_used'], 1)
            self.assertEqual(status['trades_remaining'], 2)
            
    def test_get_recent_trades(self):
        """Test retrieving recent trade history"""
        # Record some trades
        self.tracker.record_day_trade("AAPL")
        self.tracker.record_day_trade("GOOGL")
        
        trades = self.tracker.get_recent_trades()
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0]['symbol'], "AAPL")
        self.assertEqual(trades[1]['symbol'], "GOOGL")
        
        # Check trade details
        for trade in trades:
            self.assertIn('timestamp', trade)
            self.assertIn('symbol', trade)
            self.assertIn('type', trade)
            self.assertEqual(trade['type'], 'day_trade')
            
    def test_reset_for_testing(self):
        """Test manual reset functionality"""
        # Add some trades
        self.tracker.record_day_trade("AAPL")
        self.tracker.record_day_trade("GOOGL")
        
        # Reset
        self.tracker.reset_for_testing()
        
        # Should be back to initial state
        status = self.tracker.get_status()
        self.assertEqual(status['trades_used'], 0)
        self.assertEqual(status['trades_remaining'], 3)
        self.assertTrue(status['can_day_trade'])
        self.assertEqual(len(self.tracker.get_recent_trades()), 0)
        
    def test_concurrent_trades(self):
        """Test handling of concurrent trade requests"""
        # This would test thread safety if implemented
        # For now, just verify sequential behavior
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMD"]
        
        for symbol in symbols[:3]:
            self.assertTrue(self.tracker.can_day_trade())
            self.tracker.record_day_trade(symbol)
            
        # Should be at limit
        self.assertFalse(self.tracker.can_day_trade())
        
        # Additional trades should not be recorded
        status_before = self.tracker.get_status()['trades_used']
        
        # Try to record when at limit (should be prevented by caller)
        # Tracker itself doesn't enforce, relies on can_day_trade check
        
        self.assertEqual(status_before, 3)


if __name__ == "__main__":
    unittest.main()