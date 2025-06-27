import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from main import app
from models import SignalType, TimeFrame


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "elpyfi-ai"
    assert "endpoints" in data


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_analyze_endpoint_basic_buy():
    request_data = {
        "signal": {
            "symbol": "AAPL",
            "type": "buy",
            "price": 150.0,
            "indicators": [
                {"name": "RSI", "value": 25, "timeframe": "1h"},
                {"name": "MACD", "value": 0.5, "timeframe": "1h"}
            ]
        }
    }
    
    response = client.post("/analyze", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "recommendation" in data
    assert "confidence" in data
    assert "formatted_explanation" in data
    assert "risk_assessment" in data
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.0


def test_analyze_endpoint_with_constraints():
    request_data = {
        "signal": {
            "symbol": "TSLA",
            "type": "buy",
            "price": 250.0,
            "indicators": [
                {"name": "RSI", "value": 30, "timeframe": "1h"}
            ]
        },
        "constraints": {
            "pdt_trades_remaining": 0,
            "account_balance": 5000
        }
    }
    
    response = client.post("/analyze", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["recommendation"] == "hold"


def test_analyze_endpoint_invalid_data():
    request_data = {
        "signal": {
            "symbol": "AAPL",
            "price": -100
        }
    }
    
    response = client.post("/analyze", json=request_data)
    assert response.status_code == 422


def test_backtest_endpoint():
    backtest_data = {
        "signal": {
            "symbol": "AAPL",
            "type": "buy",
            "price": 150.0,
            "timestamp": datetime.utcnow().isoformat()
        },
        "decision": {
            "recommendation": "buy",
            "confidence": 0.8,
            "explanation": "Test decision",
            "factors": ["RSI oversold"],
            "risk_assessment": {
                "risk_level": "medium",
                "stop_loss_price": 145.0,
                "take_profit_price": 155.0
            }
        },
        "actual_outcome": {
            "profitable": True,
            "price_after_signal": 155.0
        }
    }
    
    response = client.post("/backtest-decision", json=backtest_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "accuracy_assessment" in data
    assert "outcome_analysis" in data


def test_metrics_endpoint_empty():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_after_analysis():
    request_data = {
        "signal": {
            "symbol": "AAPL",
            "type": "buy",
            "price": 150.0
        }
    }
    
    client.post("/analyze", json=request_data)
    
    response = client.get("/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_analyses"] > 0
    assert "recommendation_distribution" in data
    assert "average_confidence" in data