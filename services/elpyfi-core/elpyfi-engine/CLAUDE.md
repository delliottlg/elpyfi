# ElPyFi Engine - Future Goals & Notes

## Current Status ✅
- Event-driven trading engine with PDT tracking
- Solar Flare momentum strategy (uses real NOAA space weather data!)
- Database integration for positions with pg_notify
- Test framework for verification
- ~833 lines of clean, modular code

## Known Issues 🔧
- Database schema mismatch: `positions` table missing `order_id` column
  - Engine tries to write it, but table doesn't have it
  - Positions still get recorded (internal events work fine)

## Future Enhancements 🚀

### 1. Signal Database Integration
- Add `write_signal()` calls when signals are generated
- Would enable `/signals/recent` API endpoint
- Not critical for MVP

### 2. PDT Database Persistence  
- Currently PDT tracking is in-memory only
- Could write to `pdt_tracking` table for persistence across restarts
- Would survive engine restarts

### 3. Real Broker Integration ✅
- ✅ Alpaca integration implemented!
- ✅ Real-time market data fetching
- ✅ Dynamic position sizing (2% of portfolio)
- ✅ Paper/live trading modes
- ✅ Order status tracking

### 4. More Strategies
- Opening Range Breakout (mentioned in design doc)
- Mean Reversion 
- Trend Following
- Each ~150 lines following the same pattern

### 5. Production Hardening
- Connection pooling for database
- Retry logic for failed DB writes
- Configuration from environment variables
- Proper secrets management

## Architecture Notes 📝
- EventBus handles internal coordination
- Database writes are "fire and forget" with graceful fallback
- pg_notify enables real-time WebSocket updates via the API
- Strategies are completely isolated from each other
- PDT allocator uses simple scoring: confidence × profit × history

## Configuration

### Alpaca Setup
1. Get API keys from https://alpaca.markets/
2. Copy `.env.example` to `.env`
3. Add your Alpaca credentials:
```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_PAPER=true  # Use paper trading for testing
```

## Testing
```bash
source venv/bin/activate

# Without Alpaca (stub mode)
python test_engine.py

# With Alpaca paper trading
source .env  # Load Alpaca credentials
python test_engine.py
```

## Fun Facts 🌞
- The Solar Flare strategy actually calls NOAA's space weather API
- K-index 7+ means aurora borealis is visible (and HFT algos are disrupted!)
- Test mode forces K-index 7 for consistent results

## PM Claude Status
*Updated by PM Claude on 2025-06-25 23:26:53*

- **Service Status**: stopped

### Integration with PM Claude
This service is managed by PM Claude and uses:
- Shared Python 3.11 virtual environment
- Centralized secrets management
- Automated health monitoring
- Unified test runner

### Known Issues
- [OPEN] [0d682431] Improve database schema mismatch error handling
  - While engine.py handles missing order_id column gracefully, add proper warning logs and fallback behavior. Consider adding column existence check on startup to log clear warnings about schema issues.
- [OPEN] [748fc1fc] Add PM Claude service status check on startup
  - Add code to check if other services are running by looking for PM_CLAUDE_SERVICE_STATUS environment variable or calling PM Claude's status endpoint. This helps coordinate startup dependencies.
- [OPEN] [31298f7b] Remove old local venv and use PM Claude's shared environment
  - Delete the local venv/ directory in elpyfi-engine/. When running Python, use /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/python or activate the shared venv with: source /Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/activate
