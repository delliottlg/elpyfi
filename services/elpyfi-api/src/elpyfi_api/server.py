from fastapi import FastAPI, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import asyncio
import json
from typing import List, Optional
from contextlib import asynccontextmanager
from .auth import verify_api_key
from .models import Position, Signal
from .config import settings
from .streams import websocket_endpoint, manager, event_listener


# Global connection pool
pool: Optional[asyncpg.Pool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create connection pool
    global pool
    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )
    
    # Start PostgreSQL listener in background
    listener_task = asyncio.create_task(event_listener(pool))
    
    yield
    
    # Shutdown: Cancel listener and close connection pool
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    
    if pool:
        await pool.close()


app = FastAPI(title="elPyFi API", version="1.0.0", lifespan=lifespan)

# CORS for web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


# Database connection from pool
async def get_db():
    async with pool.acquire() as conn:
        yield conn


# --- REST Endpoints ---


@app.get("/")
async def root():
    return {"name": "elPyFi API", "version": "1.0.0", "status": "active"}


@app.get("/health")
async def health():
    # Check database connectivity
    try:
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "elpyfi-api",
        "database": db_status
    }


@app.get("/positions", response_model=List[Position])
async def get_positions(db=Depends(get_db), _=Depends(verify_api_key)):
    """Current open positions"""
    rows = await db.fetch(
        """
        SELECT symbol, quantity, entry_price, current_price, 
               unrealized_pl, strategy
        FROM positions 
        WHERE status = 'open'
    """
    )
    return [Position(**dict(row)) for row in rows]


@app.get("/signals/recent", response_model=List[Signal])
async def get_recent_signals(
    limit: int = 50, db=Depends(get_db), _=Depends(verify_api_key)
):
    """Recent signals from all strategies"""
    # Validate limit parameter
    if limit < 1:
        limit = 1
    elif limit > 1000:
        limit = 1000
    rows = await db.fetch(
        """
        SELECT strategy, symbol, action, confidence, 
               timestamp, metadata
        FROM signals 
        ORDER BY timestamp DESC 
        LIMIT $1
    """,
        limit,
    )
    signals = []
    for row in rows:
        row_dict = dict(row)
        # Handle metadata - parse JSON string if needed
        if row_dict.get('metadata') is None:
            row_dict['metadata'] = {}
        elif isinstance(row_dict['metadata'], str):
            row_dict['metadata'] = json.loads(row_dict['metadata'])
        signals.append(Signal(**row_dict))
    return signals


@app.get("/metrics/{strategy}")
async def get_strategy_metrics(
    strategy: str, db=Depends(get_db), _=Depends(verify_api_key)
):
    """Performance metrics for a strategy"""
    row = await db.fetchrow(
        """
        SELECT * FROM strategy_metrics 
        WHERE strategy = $1 
        AND date = CURRENT_DATE
    """,
        strategy,
    )
    return dict(row) if row else {}


@app.get("/pdt/status")
async def get_pdt_status(db=Depends(get_db), _=Depends(verify_api_key)):
    """PDT trades remaining this week"""
    row = await db.fetchrow(
        """
        SELECT trades_used, trades_remaining 
        FROM pdt_tracking 
        WHERE week_start = date_trunc('week', CURRENT_DATE)
    """
    )
    return {
        "trades_used": row["trades_used"] if row else 0,
        "trades_remaining": row["trades_remaining"] if row else 3,
    }


@app.get("/strategies")
async def get_active_strategies(db=Depends(get_db), _=Depends(verify_api_key)):
    """List active strategies"""
    rows = await db.fetch(
        """
        SELECT DISTINCT strategy, COUNT(*) as position_count 
        FROM positions 
        WHERE status = 'open' 
        GROUP BY strategy
    """
    )
    return [
        {"strategy": row["strategy"], "position_count": row["position_count"]}
        for row in rows
    ]


# --- WebSocket Endpoints ---


@app.websocket("/ws")
async def websocket_all_events(websocket: WebSocket):
    """All events stream"""
    await websocket_endpoint(websocket)


@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    """Just signals stream"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        manager.disconnect(websocket)


@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """Just trades stream"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        manager.disconnect(websocket)
