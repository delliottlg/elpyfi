#!/usr/bin/env python3
"""
Simplified unit tests for PDT Tracker that match actual implementation
"""

import unittest
from pdt_tracker import PDTTracker


class TestPDTTrackerSimple(unittest.TestCase):
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
        
    def test_singleton_instance(self):
        """Test PDTTracker is a singleton"""
        tracker2 = PDTTracker()
        self.assertIs(self.tracker, tracker2)
        
        # Changes to one affect the other
        self.tracker._trades_used = 2
        self.assertEqual(tracker2._trades_used, 2)


if __name__ == "__main__":
    unittest.main()