#!/usr/bin/env python3
"""
Unit tests for Execution Engine
Tests order execution, position tracking, and broker integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
from execution import ExecutionEngine
from events import EventBus, EventType, TradeApprovalEvent, PositionEvent


class TestExecutionEngine(unittest.TestCase):
    def setUp(self):
        """Create fresh execution engine for each test"""
        self.event_bus = EventBus()
        self.engine = ExecutionEngine(self.event_bus)
        self.engine.initialize()
        
        # Track emitted events
        self.positions_opened = []
        self.event_bus.subscribe(EventType.POSITION_OPENED, self.positions_opened.append)
        
    def test_initialization(self):
        """Test engine initializes correctly"""
        # Should be subscribed to trade approvals
        handlers = self.event_bus._handlers.get(EventType.DAY_TRADE_APPROVED, [])
        self.assertTrue(any(h.__self__ == self.engine for h in handlers))
        
    def test_execute_approved_trade(self):
        """Test execution of approved trades"""
        # Mock the database writer
        with patch.object(self.engine, 'db_writer') as mock_db:
            mock_db.write_position = Mock(return_value=True)
            
            # Emit approval event
            approval = TradeApprovalEvent(
                symbol="AAPL",
                approved=True,
                reason="Under PDT limit",
                strategy="momentum",
                action="buy",
                confidence=0.85,
                expected_profit=500
            )
            
            self.event_bus.emit(EventType.DAY_TRADE_APPROVED, approval)
            
            # Should have recorded position
            mock_db.write_position.assert_called_once()
            call_args = mock_db.write_position.call_args[0][0]
            
            self.assertEqual(call_args['symbol'], "AAPL")
            self.assertEqual(call_args['strategy'], "momentum")
            self.assertEqual(call_args['status'], "open")
            
            # Should emit position event
            self.assertEqual(len(self.positions_opened), 1)
            position = self.positions_opened[0]
            self.assertEqual(position.symbol, "AAPL")
            self.assertEqual(position.strategy, "momentum")
            
    def test_reject_unapproved_trade(self):
        """Test rejected trades are not executed"""
        approval = TradeApprovalEvent(
            symbol="AAPL",
            approved=False,
            reason="PDT limit reached",
            strategy="momentum"
        )
        
        self.event_bus.emit(EventType.DAY_TRADE_APPROVED, approval)
        
        # Should not create position
        self.assertEqual(len(self.positions_opened), 0)
        
    def test_execute_trade_generation(self):
        """Test trade execution details"""
        # Test the execute_trade method directly
        position = self.engine.execute_trade("TSLA", "scalping", "buy", 0.9, 1000)
        
        self.assertEqual(position['symbol'], "TSLA")
        self.assertEqual(position['quantity'], Decimal('100'))  # Default quantity
        self.assertEqual(position['strategy'], "scalping")
        self.assertEqual(position['status'], "open")
        self.assertIsNotNone(position['order_id'])
        self.assertIn('entry_price', position)
        self.assertIn('current_price', position)
        self.assertIn('created_at', position)
        
    def test_position_tracking(self):
        """Test internal position tracking"""
        # Execute a trade
        position1 = self.engine.execute_trade("AAPL", "momentum", "buy", 0.8, 500)
        
        # Should track position
        self.assertEqual(len(self.engine._positions), 1)
        self.assertIn("AAPL", self.engine._positions)
        
        # Execute another trade for same symbol
        position2 = self.engine.execute_trade("AAPL", "scalping", "buy", 0.7, 300)
        
        # Should have both positions
        self.assertEqual(len(self.engine._positions["AAPL"]), 2)
        
    def test_get_open_positions(self):
        """Test retrieving open positions"""
        # Create some positions
        self.engine.execute_trade("AAPL", "momentum", "buy", 0.8, 500)
        self.engine.execute_trade("GOOGL", "scalping", "buy", 0.7, 300)
        self.engine.execute_trade("MSFT", "momentum", "buy", 0.9, 700)
        
        # Get all open positions
        positions = self.engine.get_open_positions()
        self.assertEqual(len(positions), 3)
        
        # Get positions for specific symbol
        aapl_positions = self.engine.get_open_positions("AAPL")
        self.assertEqual(len(aapl_positions), 1)
        self.assertEqual(aapl_positions[0]['symbol'], "AAPL")
        
    def test_database_write_failure(self):
        """Test handling of database write failures"""
        with patch.object(self.engine, 'db_writer') as mock_db:
            mock_db.write_position = Mock(side_effect=Exception("DB Error"))
            
            approval = TradeApprovalEvent(
                symbol="AAPL",
                approved=True,
                reason="Under PDT limit",
                strategy="momentum",
                action="buy",
                confidence=0.85,
                expected_profit=500
            )
            
            # Should not crash
            self.event_bus.emit(EventType.DAY_TRADE_APPROVED, approval)
            
            # Position event should still be emitted
            self.assertEqual(len(self.positions_opened), 1)
            
    def test_order_id_generation(self):
        """Test unique order ID generation"""
        order_ids = set()
        
        for i in range(100):
            position = self.engine.execute_trade(f"STOCK{i}", "test", "buy", 0.5, 100)
            order_ids.add(position['order_id'])
            
        # All order IDs should be unique
        self.assertEqual(len(order_ids), 100)
        
        # Should follow expected format
        for order_id in order_ids:
            self.assertTrue(order_id.startswith("ORD-"))
            self.assertEqual(len(order_id), 20)  # ORD- + 16 chars
            
    def test_sell_action(self):
        """Test sell orders (future enhancement)"""
        position = self.engine.execute_trade("AAPL", "momentum", "sell", 0.8, 500)
        
        # For now, sells are treated same as buys
        # In future, this would close existing positions
        self.assertEqual(position['quantity'], Decimal('100'))
        self.assertEqual(position['status'], "open")
        
    def test_decimal_precision(self):
        """Test decimal handling for prices and quantities"""
        position = self.engine.execute_trade("AAPL", "test", "buy", 0.9, 1234.56789)
        
        # Check decimals are used
        self.assertIsInstance(position['quantity'], Decimal)
        self.assertIsInstance(position['entry_price'], Decimal)
        self.assertIsInstance(position['current_price'], Decimal)
        self.assertIsInstance(position['unrealized_pl'], Decimal)
        
        # Check precision is maintained
        self.assertEqual(position['unrealized_pl'], Decimal('0'))
        
    def test_concurrent_executions(self):
        """Test thread safety of execution engine"""
        import threading
        
        def execute_trades(symbol_prefix):
            for i in range(10):
                self.engine.execute_trade(f"{symbol_prefix}{i}", "test", "buy", 0.7, 100)
                
        threads = []
        for prefix in ["A", "B", "C"]:
            t = threading.Thread(target=execute_trades, args=(prefix,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
            
        # Should have all 30 positions
        total_positions = sum(len(positions) for positions in self.engine._positions.values())
        self.assertEqual(total_positions, 30)


if __name__ == "__main__":
    unittest.main()