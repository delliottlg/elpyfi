"""
Execution module for order management and broker integration.

This module handles:
- Receiving approved trading signals
- Placing orders with brokers
- Tracking order status
- Emitting position events
"""

from events import event_bus, EventType, SignalEvent, PositionEvent, TradeRequestEvent
from datetime import datetime
import logging
import os
from decimal import Decimal
from db_writer import get_db_writer

# Alpaca imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockLatestQuoteRequest

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Handles order execution and position management"""
    
    def __init__(self):
        self.pending_orders = {}
        self.positions = {}
        self.alpaca_client = None
        self.portfolio_value = 100000  # Default, will be updated from account
        self._initialize_alpaca()
        self._setup_listeners()
    
    def _initialize_alpaca(self):
        """Initialize Alpaca trading client"""
        try:
            # Get API keys from environment or use paper trading defaults
            api_key = os.environ.get('ALPACA_API_KEY')
            secret_key = os.environ.get('ALPACA_SECRET_KEY')
            paper = os.environ.get('ALPACA_PAPER', 'true').lower() == 'true'
            
            if not api_key or not secret_key:
                logger.warning("Alpaca API keys not found in environment")
                logger.warning("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
                logger.warning("Continuing with stub execution mode")
                return
                
            # Initialize Alpaca client
            self.alpaca_client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper
            )
            
            # Get account info to update portfolio value
            try:
                account = self.alpaca_client.get_account()
                self.portfolio_value = float(account.portfolio_value)
                logger.info(f"Connected to Alpaca ({'Paper' if paper else 'Live'} trading)")
                logger.info(f"Account portfolio value: ${self.portfolio_value:,.2f}")
            except Exception as e:
                logger.error(f"Failed to get Alpaca account info: {e}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            logger.warning("Continuing with stub execution mode")
    
    def _setup_listeners(self):
        """Subscribe to relevant events"""
        event_bus.subscribe(EventType.SIGNAL_GENERATED, self.handle_signal)
        event_bus.subscribe(EventType.DAY_TRADE_APPROVED, self.handle_approved_trade)
    
    def handle_signal(self, signal_event: SignalEvent):
        """Process trading signals"""
        logger.info(f"Received signal: {signal_event.action} {signal_event.symbol} "
                   f"@ {signal_event.confidence:.2f} confidence")
        
        # Determine if this would be a day trade
        # (In reality, would check if we have open position in this symbol)
        is_day_trade = signal_event.estimated_profit < 0.03  # Quick trades are usually day trades
        
        # Create trade request
        trade_request = TradeRequestEvent(
            signal_event=signal_event,
            is_day_trade=is_day_trade,
            requested_size=0.05  # 5% of portfolio
        )
        
        # Request approval (PDT tracker will handle)
        event_bus.emit(EventType.DAY_TRADE_REQUESTED, trade_request)
    
    def handle_approved_trade(self, approval_event):
        """Execute approved trades"""
        if approval_event.approved:
            self.execute_trade(approval_event.trade_request.signal_event)
    
    def execute_trade(self, signal: SignalEvent):
        """Execute a trade via Alpaca and record in database"""
        try:
            # Use Alpaca if available, otherwise fall back to stub
            if self.alpaca_client:
                order_result = self._execute_alpaca_trade(signal)
                if order_result:
                    order_id = order_result['order_id']
                    quantity = order_result['quantity']
                    price = order_result['price']
                else:
                    # Alpaca execution failed, use stub
                    order_id, quantity, price = self._execute_stub_trade(signal)
            else:
                # No Alpaca client, use stub
                order_id, quantity, price = self._execute_stub_trade(signal)
            
            # Write to database and notify
            db = get_db_writer()
            position_id = db.write_position_opened(
                symbol=signal.symbol,
                quantity=quantity,
                entry_price=price,
                strategy=signal.strategy,
                order_id=order_id
            )
            
            # Emit position event
            position_event = PositionEvent(
                symbol=signal.symbol,
                action="opened",
                size=quantity,
                price=price,
                timestamp=datetime.now(),
                order_id=order_id
            )
            event_bus.emit(EventType.POSITION_OPENED, position_event)
            
            logger.info(f"Executed trade: {order_id} - {quantity} shares @ ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            
    def _execute_stub_trade(self, signal: SignalEvent):
        """Fallback stub execution when Alpaca is not available"""
        order_id = f"STUB_{signal.symbol}_{int(datetime.now().timestamp())}"
        quantity = 100.0
        price = 100.0
        logger.warning(f"Using stub execution for {signal.symbol}")
        return order_id, quantity, price
        
    def _execute_alpaca_trade(self, signal: SignalEvent):
        """Execute trade via Alpaca API"""
        try:
            # Calculate position size (2% of portfolio per trade)
            position_value = self.portfolio_value * 0.02
            
            # Get current market price
            from alpaca.data.historical import StockHistoricalDataClient
            data_client = StockHistoricalDataClient(
                api_key=self.alpaca_client._api_key,
                secret_key=self.alpaca_client._secret_key
            )
            
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[signal.symbol])
            quotes = data_client.get_stock_latest_quote(quote_request)
            current_price = float(quotes[signal.symbol].ask_price)
            
            # Calculate shares to buy
            quantity = int(position_value / current_price)
            if quantity < 1:
                logger.warning(f"Position size too small for {signal.symbol} at ${current_price}")
                return None
                
            # Determine order side
            order_side = OrderSide.BUY if signal.action == "buy" else OrderSide.SELL
            
            # Create market order
            market_order_data = MarketOrderRequest(
                symbol=signal.symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            market_order = self.alpaca_client.submit_order(
                order_data=market_order_data
            )
            
            logger.info(f"Alpaca order submitted: {market_order.id} - {quantity} shares of {signal.symbol}")
            
            # Track pending order
            self.pending_orders[market_order.id] = {
                'signal': signal,
                'order': market_order,
                'submitted_at': datetime.now()
            }
            
            return {
                'order_id': market_order.id,
                'quantity': float(quantity),
                'price': current_price  # Using ask price as estimate
            }
            
        except Exception as e:
            logger.error(f"Alpaca execution failed: {e}")
            return None
            
    def get_order_status(self, order_id: str):
        """Check order status from Alpaca"""
        if not self.alpaca_client:
            return None
            
        try:
            order = self.alpaca_client.get_order_by_id(order_id)
            return {
                'status': order.status,
                'filled_qty': order.filled_qty,
                'filled_avg_price': order.filled_avg_price
            }
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return None


# Global execution instance
execution_engine = ExecutionEngine()