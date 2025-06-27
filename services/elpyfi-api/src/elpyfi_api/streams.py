from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import asyncpg
import json
from typing import Set
from datetime import datetime
from .config import settings


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up dead connections
        self.active_connections -= disconnected


manager = ConnectionManager()


async def event_listener(pool):
    """Listen to PostgreSQL NOTIFY events"""
    # Get a dedicated connection for listening
    conn = await pool.acquire()
    
    try:
        await conn.add_listener("trading_events", handle_db_event)

        # Keep alive
        while True:
            await asyncio.sleep(1)
    finally:
        # Clean up on shutdown
        await pool.release(conn)


async def handle_db_event(conn, pid, channel, payload):
    """Forward database events to WebSocket clients"""
    event = json.loads(payload)
    await manager.broadcast(event)


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json(
            {"type": "connected", "timestamp": datetime.now().isoformat()}
        )

        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
