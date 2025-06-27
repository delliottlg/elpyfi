#!/usr/bin/env python3
"""
Unit tests for the EventBus system
Tests pub/sub functionality, event emission, and edge cases
"""

import unittest
from unittest.mock import Mock, call
import threading
import time
from events import EventBus, EventType, SignalEvent, TradeApprovalEvent


class TestEventBus(unittest.TestCase):
    def setUp(self):
        """Create fresh EventBus for each test"""
        self.bus = EventBus()
        
    def test_subscribe_and_emit(self):
        """Test basic subscription and event emission"""
        handler = Mock()
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        signal = SignalEvent(
            strategy="test",
            symbol="AAPL",
            action="buy",
            confidence=0.8,
            expected_profit=100
        )
        
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        handler.assert_called_once_with(signal)
        
    def test_multiple_handlers(self):
        """Test multiple handlers for same event type"""
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()
        
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler1)
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler2)
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler3)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        handler1.assert_called_once_with(signal)
        handler2.assert_called_once_with(signal)
        handler3.assert_called_once_with(signal)
        
    def test_unsubscribe(self):
        """Test handler unsubscription"""
        handler1 = Mock()
        handler2 = Mock()
        
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler1)
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler2)
        
        # Unsubscribe handler1
        self.bus.unsubscribe(EventType.SIGNAL_GENERATED, handler1)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        handler1.assert_not_called()
        handler2.assert_called_once_with(signal)
        
    def test_no_handlers(self):
        """Test emitting event with no handlers"""
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        # Should not raise exception
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        
    def test_handler_exception(self):
        """Test that handler exceptions don't break event bus"""
        def bad_handler(event):
            raise ValueError("Handler error")
            
        good_handler = Mock()
        
        self.bus.subscribe(EventType.SIGNAL_GENERATED, bad_handler)
        self.bus.subscribe(EventType.SIGNAL_GENERATED, good_handler)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        # Good handler should still be called
        good_handler.assert_called_once_with(signal)
        
    def test_concurrent_emit(self):
        """Test thread safety of event emission"""
        results = []
        lock = threading.Lock()
        
        def handler(event):
            with lock:
                results.append(event.symbol)
                
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        # Create multiple threads emitting events
        threads = []
        for i in range(10):
            signal = SignalEvent("test", f"STOCK{i}", "buy", 0.8, 100)
            t = threading.Thread(
                target=lambda s=signal: self.bus.emit(EventType.SIGNAL_GENERATED, s)
            )
            threads.append(t)
            t.start()
            
        # Wait for all threads
        for t in threads:
            t.join()
            
        # Should have all 10 events
        self.assertEqual(len(results), 10)
        self.assertEqual(set(results), {f"STOCK{i}" for i in range(10)})
        
    def test_event_type_isolation(self):
        """Test that events only go to correct handlers"""
        signal_handler = Mock()
        trade_handler = Mock()
        
        self.bus.subscribe(EventType.SIGNAL_GENERATED, signal_handler)
        self.bus.subscribe(EventType.DAY_TRADE_APPROVED, trade_handler)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        approval = TradeApprovalEvent("AAPL", True, "Under PDT limit")
        
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        self.bus.emit(EventType.DAY_TRADE_APPROVED, approval)
        
        signal_handler.assert_called_once_with(signal)
        trade_handler.assert_called_once_with(approval)
        
        # Cross-check: handlers shouldn't receive wrong events
        signal_handler.assert_called_once()  # Only the signal
        trade_handler.assert_called_once()   # Only the approval
        
    def test_duplicate_subscription(self):
        """Test that duplicate subscriptions are handled"""
        handler = Mock()
        
        # Subscribe same handler twice
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        self.bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        self.bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        # Should only be called once (implementation dependent)
        # Most event buses prevent duplicate subscriptions
        self.assertEqual(handler.call_count, 1)


if __name__ == "__main__":
    unittest.main()