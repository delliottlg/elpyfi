-- =====================================================
-- UPDATE SCHEMA FOR AI INTEGRATION SUPPORT
-- =====================================================
-- Run: psql -d elpyfi -f update_schema_ai_support.sql
-- =====================================================

-- Extend the action types to include 'proposed' for AI suggestions
ALTER TABLE signals 
DROP CONSTRAINT IF EXISTS signals_action_check;

-- Note: PostgreSQL doesn't have a direct way to modify column constraints
-- So we'll document that 'action' now accepts: 'buy', 'sell', 'hold', 'proposed'

-- Add an index for filtering proposed signals efficiently
CREATE INDEX IF NOT EXISTS idx_signals_action_proposed 
ON signals(action, timestamp DESC) 
WHERE action = 'proposed';

-- Add a view for Core to easily see pending AI proposals
CREATE OR REPLACE VIEW pending_ai_proposals AS
SELECT 
    id,
    strategy,
    symbol,
    action,
    confidence,
    timestamp,
    metadata,
    metadata->>'ai_model' as ai_model,
    metadata->>'risk_score' as risk_score
FROM signals
WHERE action = 'proposed'
  AND timestamp > NOW() - INTERVAL '1 hour'  -- Only recent proposals
ORDER BY timestamp DESC;

-- Verify the changes
SELECT 'Schema updated for AI integration support!' as status;