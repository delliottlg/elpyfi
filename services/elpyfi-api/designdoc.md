elPyFi API Service - Design Document

  Overview

  Minimal REST/WebSocket API that exposes elPyFi-engine data to
  external consumers (dashboards, AI services, monitoring
  tools). Read-only by design - trading decisions happen in the
  engine, not through API calls.

  Current Status: Implemented and managed by PM Claude
  Port: 9002 (when run via PM Claude)
  Git: Currently part of pm-claude repo (may be separated later)

  Core Principles

  1. Read-Only API

  # NO endpoints like:
  # POST /trades
  # POST /strategies/execute

  # ONLY endpoints like:
  # GET /positions
  # GET /signals
  # WS /stream/events

  2. Event Streaming First

  - REST for snapshots
  - WebSocket for real-time updates
  - No polling needed

  3. Stateless & Lightweight

  - No business logic
  - No trading decisions
  - Just data relay

  File Structure

  elpyfi-api/
  ├── src/
  │   └── elpyfi_api/
  │       ├── server.py      # FastAPI app setup (100 lines max)
  │       ├── auth.py        # Simple API key auth (50 lines)
  │       ├── streams.py     # WebSocket handling (80 lines)
  │       ├── models.py      # Pydantic models (60 lines)
  │       ├── config.py      # Environment config (30 lines)
  │       └── main.py        # Entry point (20 lines)
  ├── tests/             # Test suite
  ├── Documentation/     # Setup guides and docs
  └── CLAUDE.md         # PM Claude integration notes

  Implementation

  server.py

  from fastapi import FastAPI, Depends, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  import asyncpg
  from .auth import verify_api_key
  from .models import Position, Signal, Metrics

  app = FastAPI(title="elPyFi API", version="1.0.0")

  # CORS for web dashboards
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000"],
      allow_methods=["GET"],
      allow_headers=["*"],
  )

  # Database connection pool
  async def get_db():
      return await asyncpg.connect(
          "postgresql://elpyfi:password@localhost/elpyfi"
      )

  # --- REST Endpoints ---

  @app.get("/health")
  async def health():
      return {"status": "healthy", "service": "elpyfi-api"}

  @app.get("/positions", response_model=list[Position])
  async def get_positions(
      db=Depends(get_db), 
      _=Depends(verify_api_key)
  ):
      """Current open positions"""
      rows = await db.fetch("""
          SELECT symbol, quantity, entry_price, current_price, 
                 unrealized_pl, strategy
          FROM positions 
          WHERE status = 'open'
      """)
      return [Position(**row) for row in rows]

  @app.get("/signals/recent", response_model=list[Signal])
  async def get_recent_signals(
      limit: int = 50,
      db=Depends(get_db),
      _=Depends(verify_api_key)
  ):
      """Recent signals from all strategies"""
      rows = await db.fetch("""
          SELECT strategy, symbol, action, confidence, 
                 timestamp, metadata
          FROM signals 
          ORDER BY timestamp DESC 
          LIMIT $1
      """, limit)
      return [Signal(**row) for row in rows]

  @app.get("/metrics/{strategy}")
  async def get_strategy_metrics(
      strategy: str,
      db=Depends(get_db),
      _=Depends(verify_api_key)
  ):
      """Performance metrics for a strategy"""
      row = await db.fetchrow("""
          SELECT * FROM strategy_metrics 
          WHERE strategy = $1 
          AND date = CURRENT_DATE
      """, strategy)
      return dict(row) if row else {}

  @app.get("/pdt/status")
  async def get_pdt_status(
      db=Depends(get_db),
      _=Depends(verify_api_key)
  ):
      """PDT trades remaining this week"""
      row = await db.fetchrow("""
          SELECT trades_used, trades_remaining 
          FROM pdt_tracking 
          WHERE week_start = date_trunc('week', CURRENT_DATE)
      """)
      return {
          "trades_used": row["trades_used"] if row else 0,
          "trades_remaining": row["trades_remaining"] if row
  else 3
      }

  auth.py

  from fastapi import Header, HTTPException
  import secrets
  import os

  # Simple API key auth - upgrade to JWT if needed
  VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(","))

  async def verify_api_key(x_api_key: str = Header()):
      if not VALID_API_KEYS:
          # No auth in dev mode
          return True

      if x_api_key not in VALID_API_KEYS:
          raise HTTPException(
              status_code=403,
              detail="Invalid API key"
          )
      return True

  def generate_api_key() -> str:
      """Generate a new API key"""
      return f"elpyfi_{secrets.token_urlsafe(32)}"

  streams.py

  from fastapi import WebSocket, WebSocketDisconnect
  import asyncio
  import asyncpg
  import json
  from typing import Set

  class ConnectionManager:
      def __init__(self):
          self.active_connections: Set[WebSocket] = set()

      async def connect(self, websocket: WebSocket):
          await websocket.accept()
          self.active_connections.add(websocket)

      def disconnect(self, websocket: WebSocket):
          self.active_connections.remove(websocket)

      async def broadcast(self, message: dict):
          # Send to all connected clients
          disconnected = set()
          for connection in self.active_connections:
              try:
                  await connection.send_json(message)
              except:
                  disconnected.add(connection)

          # Clean up dead connections
          self.active_connections -= disconnected

  manager = ConnectionManager()

  async def event_listener():
      """Listen to PostgreSQL NOTIFY events"""
      conn = await asyncpg.connect(
          "postgresql://elpyfi:password@localhost/elpyfi"
      )

      await conn.add_listener('trading_events', handle_db_event)

      # Keep alive
      while True:
          await asyncio.sleep(1)

  async def handle_db_event(conn, pid, channel, payload):
      """Forward database events to WebSocket clients"""
      event = json.loads(payload)
      await manager.broadcast(event)

  # WebSocket endpoint
  async def websocket_endpoint(websocket: WebSocket):
      await manager.connect(websocket)
      try:
          # Send initial state
          await websocket.send_json({
              "type": "connected",
              "timestamp": datetime.now().isoformat()
          })

          # Keep connection alive
          while True:
              # Wait for client messages (ping/pong)
              data = await websocket.receive_text()
              if data == "ping":
                  await websocket.send_text("pong")

      except WebSocketDisconnect:
          manager.disconnect(websocket)

  models.py

  from pydantic import BaseModel
  from datetime import datetime
  from typing import Optional, Dict

  class Position(BaseModel):
      symbol: str
      quantity: float
      entry_price: float
      current_price: float
      unrealized_pl: float
      strategy: str

  class Signal(BaseModel):
      strategy: str
      symbol: str
      action: str  # "buy", "sell", "hold", "proposed" (for AI)
      confidence: float
      timestamp: datetime
      metadata: Optional[Dict] = {}  # Can include ai_model, risk_score

  class Metrics(BaseModel):
      strategy: str
      total_trades: int
      win_rate: float
      profit_loss: float
      sharpe_ratio: float
      max_drawdown: float

  config.py

  from pydantic_settings import BaseSettings  # Updated import

  class Settings(BaseSettings):
      database_url: str =
  "postgresql://elpyfi:password@localhost/elpyfi"
      api_keys: str = ""  # Comma-separated
      cors_origins: str = "http://localhost:3000"
      port: int = 9002  # Updated port for PM Claude

      class Config:
          env_prefix = "ELPYFI_"
          env_file = ".env"
          extra = "ignore"  # Handle extra env vars from PM Claude

  settings = Settings()

  main.py

  import uvicorn
  import asyncio
  from .server import app
  from .streams import event_listener

  async def startup():
      # Start PostgreSQL listener in background
      asyncio.create_task(event_listener())

  app.add_event_handler("startup", startup)

  if __name__ == "__main__":
      uvicorn.run(
          "src.elpyfi_api.main:app",  # Updated module path
          host="0.0.0.0",
          port=9002,  # Updated port
          reload=True
      )

  API Endpoints

  REST Endpoints

  GET /health                 # Service health
  GET /positions              # Current positions
  GET /signals/recent         # Recent signals (limit param)
  GET /metrics/{strategy}     # Strategy performance
  GET /pdt/status            # PDT trades remaining
  GET /strategies            # List active strategies

  WebSocket Streams

  WS /ws                     # All events
  WS /ws/signals            # Just signals
  WS /ws/trades             # Just trades

  Event Types

  // Position opened
  {
      "type": "position.opened",
      "data": {
          "strategy": "ma_crossover",
          "symbol": "AAPL",
          "quantity": 10,
          "price": 150.25
      },
      "timestamp": "2024-01-15T10:30:00Z"
  }

  // Signal generated
  {
      "type": "signal.generated",
      "data": {
          "strategy": "rsi_divergence",
          "symbol": "TSLA",
          "action": "buy",
          "confidence": 0.85
      },
      "timestamp": "2024-01-15T10:31:00Z"
  }

  // PDT trade used
  {
      "type": "pdt.trade_used",
      "data": {
          "trades_remaining": 2,
          "strategy": "momentum_scalp"
      },
      "timestamp": "2024-01-15T10:32:00Z"
  }

  Security

  1. API Key Authentication - Simple but effective
  2. Read-Only - No dangerous operations
  3. Rate Limiting - Via nginx/cloudflare
  4. CORS - Restricted origins

  Deployment

  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["python", "-m", "elpyfi_api.main"]

  Database Schema Updates (AI Integration)

  -- Support for AI-generated signals
  ALTER TABLE signals 
  ADD CONSTRAINT check_valid_action 
  CHECK (action IN ('buy', 'sell', 'hold', 'proposed'));

  -- Index for filtering proposed signals
  CREATE INDEX idx_signals_proposed 
  ON signals(action, timestamp) 
  WHERE action = 'proposed';

  -- View for AI service to fetch pending proposals
  CREATE VIEW pending_ai_proposals AS
  SELECT * FROM signals 
  WHERE action = 'proposed' 
  AND timestamp > NOW() - INTERVAL '1 hour';

  PM Claude Integration

  When running under PM Claude:
  - Service definition in config/services.yaml
  - Secrets managed in config/secrets.yaml
  - Health monitored automatically
  - Logs aggregated by PM Claude
  - Shared Python 3.11 venv
  - Git repository will be separated (pending)

  Why This Design Works

  1. Minimal - ~300 lines total
  2. Stateless - Can run multiple instances
  3. Real-time - WebSocket for instant updates
  4. Database-driven - Single source of truth
  5. Claude-friendly - Each file has one clear purpose
  6. PM Claude ready - Integrates with orchestrator

  The API is just a window into the engine's data - no logic, no
   decisions, just clean data access.