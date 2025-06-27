"""Basic tests for elPyFi API"""

import pytest
from fastapi.testclient import TestClient
from src.elpyfi_api.server import app
from unittest.mock import MagicMock, AsyncMock
import asyncpg


@pytest.fixture
def client(monkeypatch):
    """Create test client with mocked database pool"""
    # Mock the database pool
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    
    # Mock pool.acquire() to return an async context manager
    class MockAcquire:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    mock_pool.acquire = MagicMock(return_value=MockAcquire())
    mock_pool.close = AsyncMock()
    
    # Mock connection methods
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=1)
    
    # Set the mock pool
    import src.elpyfi_api.server
    monkeypatch.setattr(src.elpyfi_api.server, 'pool', mock_pool)
    
    # Create client without lifespan to avoid database connection
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health_endpoint(client, monkeypatch):
    """Test health endpoint"""
    # Mock the database check
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    
    class MockContextManager:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    import src.elpyfi_api.server
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=MockContextManager())
    monkeypatch.setattr(src.elpyfi_api.server, 'pool', mock_pool)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "elpyfi-api"
    assert data["database"] == "connected"


def test_health_endpoint_db_error(client, monkeypatch):
    """Test health endpoint when database is unavailable"""
    # Mock the database check to fail
    class MockContextManager:
        async def __aenter__(self):
            raise Exception("Database connection failed")
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    import src.elpyfi_api.server
    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=MockContextManager())
    monkeypatch.setattr(src.elpyfi_api.server, 'pool', mock_pool)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["service"] == "elpyfi-api"
    assert "error" in data["database"]


def test_positions_endpoint(client):
    """Test positions endpoint (dev mode allows no auth)"""
    response = client.get("/positions")
    # In dev mode (no API keys configured), should return 200
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_signals_endpoint(client):
    """Test signals endpoint"""
    response = client.get("/signals/recent")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_signals_with_limit(client):
    """Test signals endpoint with limit parameter"""
    response = client.get("/signals/recent?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


def test_signals_limit_validation(client):
    """Test signals endpoint limit parameter validation"""
    # Test with negative limit - should default to 1
    response = client.get("/signals/recent?limit=-5")
    assert response.status_code == 200
    
    # Test with limit > 1000 - should cap at 1000
    response = client.get("/signals/recent?limit=2000")
    assert response.status_code == 200
    
    # Test with limit = 0 - should default to 1
    response = client.get("/signals/recent?limit=0")
    assert response.status_code == 200


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics/test_strategy")
    assert response.status_code == 200
    # Returns empty dict if no data
    assert isinstance(response.json(), dict)


def test_pdt_status_endpoint(client):
    """Test PDT status endpoint"""
    response = client.get("/pdt/status")
    assert response.status_code == 200
    data = response.json()
    assert "trades_used" in data
    assert "trades_remaining" in data


def test_root_endpoint(client):
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "elPyFi API"
    assert "version" in data