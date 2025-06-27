# AI-Core Integration Guide

## Signal Flow Architecture

```
AI Service → Proposes signals (action='proposed') → Database
     ↓
Core Engine → Reads proposals → Validates → Updates to 'buy'/'sell' or rejects
     ↓
elPyFi API → Broadcasts all signals via WebSocket
```

## For AI Service

### Writing Proposed Signals
```python
import psycopg2
import json
from datetime import datetime

conn = psycopg2.connect("postgresql://d@localhost/elpyfi")
conn.autocommit = True
cur = conn.cursor()

# Insert AI-generated signal proposal
cur.execute("""
    INSERT INTO signals (strategy, symbol, action, confidence, timestamp, metadata)
    VALUES (%s, %s, 'proposed', %s, NOW(), %s)
""", (
    'ai_pattern_recognition',  # Always prefix with 'ai_'
    'AAPL',
    0.85,
    json.dumps({
        "ai_model": "pattern_v2",
        "rationale": "Cup and handle pattern with volume confirmation",
        "risk_score": 0.3,
        "supporting_indicators": ["volume_breakout", "rsi_60"],
        "expected_move": 0.05
    })
))

# Notify API of new AI signal
cur.execute("SELECT pg_notify('trading_events', %s)", (json.dumps({
    "type": "signal.ai_generated",
    "data": {
        "strategy": "ai_pattern_recognition",
        "symbol": "AAPL",
        "action": "proposed",
        "confidence": 0.85
    },
    "timestamp": datetime.now().isoformat()
}),))
```

## For Core Engine

### Reading AI Proposals
```python
# Check for pending AI proposals
cur.execute("""
    SELECT * FROM signals 
    WHERE action = 'proposed' 
    AND timestamp > NOW() - INTERVAL '5 minutes'
    ORDER BY confidence DESC
""")

proposals = cur.fetchall()
for proposal in proposals:
    # Your validation logic here
    if validate_proposal(proposal):
        # Accept: Update to actionable signal
        cur.execute("""
            UPDATE signals 
            SET action = %s 
            WHERE id = %s
        """, ('buy', proposal['id']))
    else:
        # Reject: Update metadata with rejection reason
        cur.execute("""
            UPDATE signals 
            SET metadata = metadata || %s 
            WHERE id = %s
        """, (
            json.dumps({"rejected": True, "reason": "Insufficient capital"}),
            proposal['id']
        ))
```

## Event Types

### AI Generates:
- `signal.ai_generated` - New AI proposal created

### Core Generates:
- `signal.validated` - AI proposal accepted and updated
- `signal.rejected` - AI proposal rejected
- `position.opened` - Position opened (may be from AI signal)
- `position.closed` - Position closed

## Best Practices

1. **AI Service**: Always use 'proposed' action for new signals
2. **Core Engine**: Process proposals within 5 minutes
3. **Both**: Include rich metadata for debugging/analysis
4. **Both**: Use consistent strategy naming (ai_* for AI, others for Core)

## Database Schema Reference

```sql
-- Signals table accepts these actions:
-- 'buy', 'sell', 'hold', 'proposed'

-- View for pending proposals:
SELECT * FROM pending_ai_proposals;
```