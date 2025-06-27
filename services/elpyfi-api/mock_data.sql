-- ===================================================================
-- MOCK DATA FOR DEVELOPMENT ONLY - DELETE THIS FILE BEFORE PRODUCTION
-- ===================================================================
-- To insert: psql -d elpyfi -f mock_data.sql
-- To clean: psql -d elpyfi -f clean_mock_data.sql
-- ===================================================================

-- Clear existing mock data first
TRUNCATE positions, signals, strategy_metrics, pdt_tracking RESTART IDENTITY CASCADE;

-- Insert mock positions
INSERT INTO positions (symbol, quantity, entry_price, current_price, unrealized_pl, strategy, status) VALUES
('AAPL', 100, 175.50, 178.25, 275.00, 'momentum_scalp', 'open'),
('TSLA', 50, 245.00, 240.50, -225.00, 'mean_reversion', 'open'),
('NVDA', 25, 485.00, 495.75, 268.75, 'breakout_rider', 'open'),
('SPY', 200, 450.25, 452.10, 370.00, 'trend_follower', 'open'),
('MSFT', 75, 380.00, 382.50, 187.50, 'momentum_scalp', 'open');

-- Insert mock signals (recent)
INSERT INTO signals (strategy, symbol, action, confidence, timestamp, metadata) VALUES
('momentum_scalp', 'AAPL', 'buy', 0.85, NOW() - INTERVAL '5 minutes', '{"rsi": 65, "volume_spike": true}'),
('mean_reversion', 'TSLA', 'sell', 0.72, NOW() - INTERVAL '10 minutes', '{"oversold": false, "resistance": 250}'),
('breakout_rider', 'NVDA', 'buy', 0.91, NOW() - INTERVAL '15 minutes', '{"breakout_level": 490, "volume": "high"}'),
('trend_follower', 'SPY', 'hold', 0.68, NOW() - INTERVAL '20 minutes', '{"trend": "bullish", "strength": "moderate"}'),
('momentum_scalp', 'MSFT', 'buy', 0.79, NOW() - INTERVAL '25 minutes', '{"momentum": "strong", "macd_cross": true}'),
('mean_reversion', 'GOOGL', 'buy', 0.83, NOW() - INTERVAL '30 minutes', '{"support_bounce": true, "rsi": 32}'),
('breakout_rider', 'AMZN', 'sell', 0.66, NOW() - INTERVAL '35 minutes', '{"failed_breakout": true}'),
('trend_follower', 'QQQ', 'buy', 0.77, NOW() - INTERVAL '40 minutes', '{"trend": "strong_up", "pullback": false}');

-- Insert mock strategy metrics for today
INSERT INTO strategy_metrics (strategy, date, total_trades, win_rate, profit_loss, sharpe_ratio, max_drawdown) VALUES
('momentum_scalp', CURRENT_DATE, 24, 0.67, 1250.50, 1.85, 0.08),
('mean_reversion', CURRENT_DATE, 18, 0.61, -325.00, 0.92, 0.12),
('breakout_rider', CURRENT_DATE, 12, 0.75, 890.25, 2.10, 0.06),
('trend_follower', CURRENT_DATE, 8, 0.63, 445.00, 1.45, 0.10);

-- Insert mock PDT tracking
INSERT INTO pdt_tracking (week_start, trades_used, trades_remaining) VALUES
(date_trunc('week', CURRENT_DATE), 1, 2);

-- Show what was inserted
SELECT 'Mock data inserted successfully!' as status;
SELECT COUNT(*) as position_count FROM positions WHERE status = 'open';
SELECT COUNT(*) as signal_count FROM signals;
SELECT COUNT(*) as strategies_with_metrics FROM strategy_metrics WHERE date = CURRENT_DATE;