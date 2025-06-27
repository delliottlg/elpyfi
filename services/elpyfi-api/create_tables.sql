-- Create tables for elPyFi API

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    quantity NUMERIC(10,2) NOT NULL,
    entry_price NUMERIC(10,2) NOT NULL,
    current_price NUMERIC(10,2) NOT NULL,
    unrealized_pl NUMERIC(10,2) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Signals table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    action VARCHAR(10) NOT NULL,
    confidence NUMERIC(3,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Strategy metrics table
CREATE TABLE IF NOT EXISTS strategy_metrics (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    win_rate NUMERIC(5,2) DEFAULT 0,
    profit_loss NUMERIC(10,2) DEFAULT 0,
    sharpe_ratio NUMERIC(5,2) DEFAULT 0,
    max_drawdown NUMERIC(5,2) DEFAULT 0,
    UNIQUE(strategy, date)
);

-- PDT tracking table
CREATE TABLE IF NOT EXISTS pdt_tracking (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    trades_used INTEGER DEFAULT 0,
    trades_remaining INTEGER DEFAULT 3,
    UNIQUE(week_start)
);

-- Create function for NOTIFY events
CREATE OR REPLACE FUNCTION notify_event() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('trading_events', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for real-time notifications
CREATE TRIGGER positions_notify AFTER INSERT OR UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION notify_event();

CREATE TRIGGER signals_notify AFTER INSERT ON signals
    FOR EACH ROW EXECUTE FUNCTION notify_event();