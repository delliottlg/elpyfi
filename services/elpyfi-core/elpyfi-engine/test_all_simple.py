#!/usr/bin/env python3
"""
Comprehensive but simple tests for ElPyFi Engine components
Tests the actual implementation, not assumed functionality
"""

import unittest
from unittest.mock import Mock
from datetime import datetime
from allocator import PDTAllocator, AllocationRequest, get_position_size, RISK_RULES
from events import event_bus, EventType, SignalEvent, TradeRequestEvent
from pdt_tracker import pdt_tracker


class TestEventBus(unittest.TestCase):
    def setUp(self):
        """Clear event bus for each test"""
        event_bus._subscribers.clear()
        
    def test_subscribe_and_emit(self):
        """Test basic pub/sub functionality"""
        handler = Mock()
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        signal = SignalEvent(
            strategy="test",
            symbol="AAPL",
            action="buy",
            confidence=0.8,
            estimated_profit=100,
            timestamp=datetime.now()
        )
        
        event_bus.emit(EventType.SIGNAL_GENERATED, signal)
        handler.assert_called_once_with(signal)
        
    def test_multiple_handlers(self):
        """Test multiple handlers"""
        handler1 = Mock()
        handler2 = Mock()
        
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler1)
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler2)
        
        event_bus.emit(EventType.SIGNAL_GENERATED, "test_data")
        
        handler1.assert_called_once_with("test_data")
        handler2.assert_called_once_with("test_data")


class TestPDTAllocator(unittest.TestCase):
    def setUp(self):
        """Fresh allocator for each test"""
        self.allocator = PDTAllocator()
        
    def test_request_allocation(self):
        """Test allocation request"""
        signal = SignalEvent(
            "test", "AAPL", "buy", 0.8, 1000, datetime.now()
        )
        trade_request = TradeRequestEvent(signal, True, 0.02)  # 2% position size
        
        result = self.allocator.request_allocation(trade_request)
        self.assertFalse(result)  # Always queued
        self.assertEqual(len(self.allocator.pending_requests), 1)
        
    def test_weekly_allocations(self):
        """Test batch allocation"""
        # Add multiple requests
        for i in range(3):
            signal = SignalEvent(
                f"strat{i}", f"STOCK{i}", "buy", 
                0.5 + i * 0.2, 100 + i * 100, datetime.now()
            )
            trade_request = TradeRequestEvent(signal, True, 0.02)  # 2% position size
            self.allocator.request_allocation(trade_request)
            
        # Get allocations
        approved = self.allocator.get_weekly_allocations(available_trades=3)
        
        # Should allocate 2 (keeping 1 emergency)
        self.assertEqual(len(approved), 2)
        
    def test_position_sizing(self):
        """Test risk-based position sizing"""
        size = get_position_size(100000)
        self.assertEqual(size, 2000)  # 2% of 100k


class TestPDTTracker(unittest.TestCase):
    def setUp(self):
        """Reset tracker state"""
        # PDT tracker is a singleton, reset its state
        pdt_tracker._trades_used = 0
        
    def test_initial_state(self):
        """Test initial PDT state"""
        status = pdt_tracker.get_status()
        self.assertEqual(status['trades_used'], 0)
        self.assertEqual(status['trades_remaining'], 3)
        self.assertTrue(status['can_day_trade'])


class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Setup for integration tests"""
        event_bus._subscribers.clear()
        pdt_tracker._trades_used = 0
        
    def test_signal_flow(self):
        """Test signal generation and handling"""
        received_signals = []
        
        def signal_handler(signal):
            received_signals.append(signal)
            
        event_bus.subscribe(EventType.SIGNAL_GENERATED, signal_handler)
        
        # Emit a signal
        signal = SignalEvent(
            "momentum", "TSLA", "buy", 0.85, 500, datetime.now()
        )
        event_bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        # Verify received
        self.assertEqual(len(received_signals), 1)
        self.assertEqual(received_signals[0].symbol, "TSLA")
        self.assertEqual(received_signals[0].confidence, 0.85)


if __name__ == "__main__":
    # Run with higher verbosity
    unittest.main(verbosity=2)