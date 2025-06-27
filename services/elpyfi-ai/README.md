# elpyfi-ai

AI-powered trading signal analysis and explanation service that provides intelligent insights for trading decisions.

## Overview

elpyfi-ai is a microservice designed to:
- Analyze trading signals using rule-based logic (V1) with plans for LLM integration (V2)
- Provide human-readable explanations for trading decisions
- Assess risk levels and suggest position sizing
- Respect Pattern Day Trading (PDT) constraints
- Offer alternative trading strategies

## Features

- **Signal Analysis**: Processes technical indicators (RSI, MACD, Volume, etc.) to generate trading recommendations
- **Risk Assessment**: Calculates stop-loss, take-profit levels, and position sizing
- **PDT Awareness**: Automatically adjusts recommendations based on day trading limits
- **Human-Readable Output**: Converts technical analysis into clear, actionable insights
- **RESTful API**: Easy integration with trading systems via FastAPI

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd elpyfi-ai
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Starting the Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:9000`

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:9000/docs`
- ReDoc: `http://localhost:9000/redoc`

### Example API Calls

#### Analyze a Trading Signal

```bash
curl -X POST "http://localhost:9000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "signal": {
      "symbol": "AAPL",
      "type": "buy",
      "price": 150.0,
      "indicators": [
        {"name": "RSI", "value": 25, "timeframe": "1h"},
        {"name": "MACD", "value": 0.5, "timeframe": "1h"},
        {"name": "VOLUME", "value": 1.8, "timeframe": "1h"}
      ],
      "market_conditions": {
        "trend": "bullish",
        "volatility": 0.3,
        "volume": 1000000
      }
    },
    "constraints": {
      "pdt_trades_remaining": 3,
      "account_balance": 10000,
      "buying_power": 5000
    }
  }'
```

#### Health Check

```bash
curl http://localhost:9000/health
```

## Running Tests

```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=html
```

## API Endpoints

- `GET /` - Service info and available endpoints
- `GET /health` - Health check endpoint
- `POST /analyze` - Analyze trading signal and get recommendations
- `POST /backtest-decision` - Submit historical decisions for analysis
- `GET /metrics` - Get service metrics and analysis statistics

## Architecture

```
elpyfi-ai/
├── models.py       # Pydantic data models
├── analyzer.py     # Core signal analysis logic
├── explainer.py    # Human-readable output generation
├── main.py         # FastAPI application
├── tests/          # Test suite
└── requirements.txt
```

## Configuration

Key environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 9000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ANTHROPIC_API_KEY`: For future LLM integration
- `MAX_POSITION_SIZE`: Maximum position size recommendation
- `DEFAULT_STOP_LOSS_PCT`: Default stop loss percentage
- `DEFAULT_TAKE_PROFIT_PCT`: Default take profit percentage

## Development Roadmap

- [x] V1: Rule-based signal analysis
- [ ] V2: LLM integration (Claude/GPT)
- [ ] V3: Custom ML models
- [ ] WebSocket support for real-time analysis
- [ ] Database integration for decision history
- [ ] Performance analytics dashboard

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.