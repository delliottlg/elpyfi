#!/usr/bin/env python3
"""
Simplified unit tests for the EventBus system
"""

import unittest
from unittest.mock import Mock
from events import event_bus, EventType, SignalEvent


class TestEventBusSimple(unittest.TestCase):
    def setUp(self):
        """Clear event bus for each test"""
        # Clear existing handlers
        event_bus._handlers.clear()
        
    def test_subscribe_and_emit(self):
        """Test basic subscription and event emission"""
        handler = Mock()
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        signal = SignalEvent(
            strategy="test",
            symbol="AAPL",
            action="buy",
            confidence=0.8,
            estimated_profit=100
        )
        
        event_bus.emit(EventType.SIGNAL_GENERATED, signal)
        handler.assert_called_once_with(signal)
        
    def test_multiple_handlers(self):
        """Test multiple handlers for same event type"""
        handler1 = Mock()
        handler2 = Mock()
        
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler1)
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler2)
        
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        event_bus.emit(EventType.SIGNAL_GENERATED, signal)
        
        handler1.assert_called_once_with(signal)
        handler2.assert_called_once_with(signal)
        
    def test_no_handlers(self):
        """Test emitting event with no handlers"""
        signal = SignalEvent("test", "AAPL", "buy", 0.8, 100)
        # Should not raise exception
        event_bus.emit(EventType.SIGNAL_GENERATED, signal)
        
    def test_handler_count(self):
        """Test handler registration"""
        # Initially no handlers
        self.assertEqual(len(event_bus._handlers.get(EventType.SIGNAL_GENERATED, [])), 0)
        
        # Add handler
        handler = Mock()
        event_bus.subscribe(EventType.SIGNAL_GENERATED, handler)
        
        # Should have one handler
        self.assertEqual(len(event_bus._handlers.get(EventType.SIGNAL_GENERATED, [])), 1)


if __name__ == "__main__":
    unittest.main()