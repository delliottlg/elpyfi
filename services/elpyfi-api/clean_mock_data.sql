-- =====================================================
-- CLEAN UP MOCK DATA - RUN THIS BEFORE REAL TRADING
-- =====================================================
-- To run: psql -d elpyfi -f clean_mock_data.sql
-- =====================================================

-- Clear all data from all tables
TRUNCATE positions, signals, strategy_metrics, pdt_tracking RESTART IDENTITY CASCADE;

-- Verify cleanup
SELECT 'All mock data cleaned!' as status;
SELECT 
    (SELECT COUNT(*) FROM positions) as positions,
    (SELECT COUNT(*) FROM signals) as signals,
    (SELECT COUNT(*) FROM strategy_metrics) as metrics,
    (SELECT COUNT(*) FROM pdt_tracking) as pdt_tracking;