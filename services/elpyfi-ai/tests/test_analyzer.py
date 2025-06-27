import pytest
from datetime import datetime
from models import (
    Signal, SignalType, Indicator, TimeFrame, 
    MarketCondition, TradingConstraints
)
from analyzer import SignalAnalyzer


@pytest.fixture
def analyzer():
    return SignalAnalyzer()


@pytest.fixture
def basic_buy_signal():
    return Signal(
        symbol="AAPL",
        type=SignalType.BUY,
        price=150.0,
        indicators=[
            Indicator(name="RSI", value=25, timeframe=TimeFrame.H1),
            Indicator(name="MACD", value=0.5, timeframe=TimeFrame.H1),
            Indicator(name="VOLUME", value=1.8, timeframe=TimeFrame.H1)
        ],
        market_conditions=MarketCondition(
            trend="bullish",
            volatility=0.3,
            volume=1000000
        )
    )


@pytest.fixture
def basic_sell_signal():
    return Signal(
        symbol="AAPL",
        type=SignalType.SELL,
        price=160.0,
        indicators=[
            Indicator(name="RSI", value=75, timeframe=TimeFrame.H1),
            Indicator(name="MACD", value=-0.5, timeframe=TimeFrame.H1),
            Indicator(name="VOLUME", value=0.8, timeframe=TimeFrame.H1)
        ],
        market_conditions=MarketCondition(
            trend="bearish",
            volatility=0.5,
            volume=800000
        )
    )


def test_analyzer_buy_signal_high_confidence(analyzer, basic_buy_signal):
    decision = analyzer.analyze(basic_buy_signal)
    
    assert decision.recommendation == SignalType.BUY
    assert decision.confidence > 0.7
    assert len(decision.factors) > 0
    assert decision.risk_assessment is not None
    assert decision.risk_assessment.stop_loss_price < basic_buy_signal.price
    assert decision.risk_assessment.take_profit_price > basic_buy_signal.price


def test_analyzer_sell_signal_high_confidence(analyzer, basic_sell_signal):
    decision = analyzer.analyze(basic_sell_signal)
    
    assert decision.recommendation == SignalType.SELL
    assert decision.confidence > 0.7
    assert len(decision.factors) > 0
    assert decision.risk_assessment is not None
    assert decision.risk_assessment.stop_loss_price > basic_sell_signal.price
    assert decision.risk_assessment.take_profit_price < basic_sell_signal.price


def test_analyzer_pdt_constraint_override(analyzer, basic_buy_signal):
    constraints = TradingConstraints(
        pdt_trades_remaining=0,
        account_balance=10000
    )
    
    decision = analyzer.analyze(basic_buy_signal, constraints=constraints)
    
    assert decision.recommendation == SignalType.HOLD
    assert "PDT" in decision.explanation
    assert any("PDT" in factor for factor in decision.factors)


def test_analyzer_weak_signal_hold_recommendation(analyzer):
    weak_signal = Signal(
        symbol="AAPL",
        type=SignalType.BUY,
        price=150.0,
        indicators=[
            Indicator(name="RSI", value=50, timeframe=TimeFrame.H1),
            Indicator(name="MACD", value=0, timeframe=TimeFrame.H1),
        ]
    )
    
    decision = analyzer.analyze(weak_signal)
    
    assert decision.confidence < 0.6
    assert len(decision.alternative_actions) > 0


def test_analyzer_high_volatility_risk_assessment(analyzer):
    volatile_signal = Signal(
        symbol="BTC-USD",
        type=SignalType.BUY,
        price=50000.0,
        market_conditions=MarketCondition(
            trend="neutral",
            volatility=0.9,
            volume=1000000000
        )
    )
    
    decision = analyzer.analyze(volatile_signal)
    
    assert decision.risk_assessment.risk_level == "high"
    assert decision.risk_assessment.position_size_recommendation <= 0.25