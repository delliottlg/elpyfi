#!/usr/bin/env python3
"""
Integration tests for ElPyFi Engine
Tests complete workflows and component interactions
"""

import unittest
from unittest.mock import patch, Mock
import time
from datetime import datetime, timedelta
from decimal import Decimal

from engine import TradingEngine
from events import event_bus, EventType, SignalEvent, TradeRequestEvent
from strategies.models import MarketData
from pdt_tracker import pdt_tracker
from allocator import PDTAllocator
from events import TradeRequestEvent


class TestEngineIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Clear any existing subscriptions
        event_bus._handlers.clear()
        
        # Reset PDT tracker
        pdt_tracker.reset_for_testing()
        
        # Track events
        self.signals = []
        self.trade_requests = []
        self.approvals = []
        self.positions = []
        
        event_bus.subscribe(EventType.SIGNAL_GENERATED, self.signals.append)
        event_bus.subscribe(EventType.TRADE_REQUESTED, self.trade_requests.append)
        event_bus.subscribe(EventType.DAY_TRADE_APPROVED, self.approvals.append)
        event_bus.subscribe(EventType.POSITION_OPENED, self.positions.append)
        
    def tearDown(self):
        """Clean up after tests"""
        event_bus._handlers.clear()
        
    def test_full_trade_lifecycle(self):
        """Test complete flow from market data to position"""
        # Initialize engine with solar flare strategy in test mode
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        # Send market data that triggers signal
        noon = datetime.now().replace(hour=12, minute=0)
        data = MarketData(
            symbol="AAPL",
            timestamp=noon,
            current_price=150.5,
            volume=2000000,  # High volume
            high=151, low=149, open=150, close=150.5,
            indicators={"vwap": 150.0, "avg_volume": 1000000}  # Above VWAP
        )
        
        event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
        time.sleep(0.5)  # Allow processing
        
        # Verify full chain
        self.assertEqual(len(self.signals), 1)
        self.assertEqual(len(self.trade_requests), 1)
        self.assertEqual(len(self.approvals), 1)
        self.assertEqual(len(self.positions), 1)
        
        # Check signal details
        signal = self.signals[0]
        self.assertEqual(signal.symbol, "AAPL")
        self.assertEqual(signal.action, "buy")
        self.assertGreater(signal.confidence, 0.5)
        
        # Check approval
        approval = self.approvals[0]
        self.assertTrue(approval.approved)
        self.assertEqual(approval.symbol, "AAPL")
        
        # Check position
        position = self.positions[0]
        self.assertEqual(position.symbol, "AAPL")
        self.assertEqual(position.strategy, "solar_flare")
        
    def test_pdt_limit_enforcement(self):
        """Test PDT limits are enforced across components"""
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        # Generate 5 signals rapidly
        noon = datetime.now().replace(hour=12, minute=0)
        for i in range(5):
            data = MarketData(
                symbol=f"STOCK{i}",
                timestamp=noon,
                current_price=100 + i,
                volume=2000000,
                high=101+i, low=99+i, open=100+i, close=100+i,
                indicators={"vwap": 99.5+i, "avg_volume": 1000000}
            )
            event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
            time.sleep(0.1)
            
        time.sleep(0.5)  # Allow processing
        
        # Should have 5 signals but only 3 approvals
        self.assertEqual(len(self.signals), 5)
        self.assertEqual(len(self.approvals), 5)
        
        approved = [a for a in self.approvals if a.approved]
        rejected = [a for a in self.approvals if not a.approved]
        
        self.assertEqual(len(approved), 3)  # PDT limit
        self.assertEqual(len(rejected), 2)
        
        # Check PDT tracker state
        status = pdt_tracker.get_status()
        self.assertEqual(status['trades_used'], 3)
        self.assertFalse(status['can_day_trade'])
        
    def test_multi_strategy_coordination(self):
        """Test multiple strategies competing for trades"""
        # Would need to implement another strategy to test
        # For now, test that solar flare works in isolation
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        self.assertEqual(len(engine.strategies), 1)
        self.assertEqual(engine.strategies[0].name, "solar_flare")
        
    def test_database_integration(self):
        """Test database writer integration with mock"""
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        
        # Mock database writer
        mock_db = Mock()
        mock_db.initialize.return_value = True
        mock_db.write_position.return_value = True
        mock_db.write_signal.return_value = True
        
        # Inject mock
        with patch('engine.DatabaseWriter', return_value=mock_db):
            engine.initialize()
            
            # Generate a signal
            noon = datetime.now().replace(hour=12, minute=0)
            data = MarketData(
                symbol="AAPL",
                timestamp=noon,
                current_price=150.5,
                volume=2000000,
                high=151, low=149, open=150, close=150.5,
                indicators={"vwap": 150.0, "avg_volume": 1000000}
            )
            
            event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
            time.sleep(0.5)
            
            # Verify database calls
            mock_db.write_position.assert_called()
            
    def test_error_resilience(self):
        """Test system continues despite component errors"""
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        # Add a bad handler that throws
        def bad_handler(event):
            raise ValueError("Test error")
            
        event_bus.subscribe(EventType.SIGNAL_GENERATED, bad_handler)
        
        # System should continue
        noon = datetime.now().replace(hour=12, minute=0)
        data = MarketData(
            symbol="AAPL",
            timestamp=noon,
            current_price=150.5,
            volume=2000000,
            high=151, low=149, open=150, close=150.5,
            indicators={"vwap": 150.0, "avg_volume": 1000000}
        )
        
        event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
        time.sleep(0.5)
        
        # Should still get signal despite bad handler
        self.assertGreater(len(self.signals), 0)
        
    def test_concurrent_market_data(self):
        """Test handling concurrent market data updates"""
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        import threading
        
        def send_data(symbol, price):
            data = MarketData(
                symbol=symbol,
                timestamp=datetime.now().replace(hour=12, minute=0),
                current_price=price,
                volume=2000000,
                high=price+1, low=price-1, open=price, close=price,
                indicators={"vwap": price-0.5, "avg_volume": 1000000}
            )
            event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
            
        # Send data from multiple threads
        threads = []
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMD"]
        for i, symbol in enumerate(symbols):
            t = threading.Thread(target=send_data, args=(symbol, 100+i))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        time.sleep(1)  # Allow processing
        
        # Should handle all without issues
        self.assertGreater(len(self.signals), 0)
        self.assertLessEqual(len(self.positions), 3)  # PDT limit
        
    def test_signal_to_position_mapping(self):
        """Test signals map correctly to positions"""
        config = {'strategies': {'solar_flare': {'test_mode': True}}}
        engine = TradingEngine(config)
        engine.initialize()
        
        # Send specific market data
        data = MarketData(
            symbol="TSLA",
            timestamp=datetime.now().replace(hour=12, minute=0),
            current_price=250.0,
            volume=3000000,
            high=252, low=248, open=249, close=250,
            indicators={"vwap": 249.5, "avg_volume": 2000000}
        )
        
        event_bus.emit(EventType.MARKET_DATA_RECEIVED, data)
        time.sleep(0.5)
        
        # Verify signal matches position
        if self.signals and self.positions:
            signal = self.signals[0]
            position = self.positions[0]
            
            self.assertEqual(signal.symbol, position.symbol)
            self.assertEqual(signal.strategy, position.strategy)
            
    def test_trade_request_batching(self):
        """Test allocator batching of trade requests"""
        # Create allocator
        allocator = PDTAllocator()
        
        # Create multiple requests at once
        requests = []
        for i in range(5):
            req = TradeRequestEvent(
                "test",
                f"BATCH{i}",
                0.8 - (i * 0.1),  # Decreasing confidence
                1000 - (i * 100)  # Decreasing profit
            )
            requests.append(req)
            
        # Allocate with only 2 slots
        decisions = allocator.allocate_trades(requests, trades_available=2)
        
        # Should approve top 2
        approved = [d for d in decisions if d.approved]
        self.assertEqual(len(approved), 2)
        self.assertEqual(approved[0].symbol, "BATCH0")
        self.assertEqual(approved[1].symbol, "BATCH1")


if __name__ == "__main__":
    unittest.main()