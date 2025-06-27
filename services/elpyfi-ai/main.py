from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv

from models import (
    Signal, Decision, AnalysisRequest, BacktestDecision,
    TradingConstraints
)
from analyzer import SignalAnalyzer
from explainer import DecisionExplainer, format_decision_for_api
from logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

# Configuration
USE_AI = os.getenv("USE_LLM", "false").lower() == "true"
AI_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")

# Initialize analyzer based on configuration
def get_analyzer():
    if USE_AI:
        try:
            if AI_PROVIDER == "anthropic":
                from ai_analyzer import AISignalAnalyzer
                logger.info("Using AI-powered analyzer (Claude)")
                return AISignalAnalyzer()
            else:
                logger.warning(f"Unknown AI provider: {AI_PROVIDER}, falling back to rules")
                return SignalAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize AI analyzer: {e}")
            logger.info("Falling back to rule-based analyzer")
            return SignalAnalyzer()
    else:
        logger.info("Using rule-based analyzer (V1)")
        return SignalAnalyzer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting elpyfi-ai service...")
    analyzer_type = "AI-enhanced (V2)" if USE_AI else "Rule-based (V1)"
    logger.info(f"Analyzer mode: {analyzer_type}")
    yield
    logger.info("Shutting down elpyfi-ai service...")


app = FastAPI(
    title="elpyfi-ai",
    description="AI-powered trading signal analysis and explanation service",
    version="2.0.0" if USE_AI else "1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = get_analyzer()
explainer = DecisionExplainer()

analysis_history: List[Dict[str, Any]] = []


@app.get("/")
async def root():
    return {
        "service": "elpyfi-ai",
        "version": "2.0.0" if USE_AI else "1.0.0",
        "mode": "AI-enhanced (V2)" if USE_AI else "Rule-based (V1)",
        "status": "operational",
        "ai_provider": AI_PROVIDER if USE_AI else None,
        "endpoints": ["/analyze", "/backtest-decision", "/health", "/metrics"]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=Dict[str, Any])
async def analyze_signal(request: AnalysisRequest):
    try:
        logger.info(f"Analyzing signal for {request.signal.symbol} at ${request.signal.price}")
        
        decision = analyzer.analyze(
            signal=request.signal,
            constraints=request.constraints,
            user_preferences=request.user_preferences
        )
        
        formatted_response = format_decision_for_api(decision, request.signal)
        
        # Submit high-confidence decisions as proposals
        proposal_id = None
        if os.getenv("ENABLE_PROPOSALS", "false").lower() == "true":
            try:
                from signal_proposer import SignalProposer
                proposer = SignalProposer()
                proposal_id = proposer.submit_proposal(request.signal, decision)
                if proposal_id:
                    logger.info(f"Submitted proposal ID: {proposal_id}")
                    formatted_response["proposal_id"] = proposal_id
            except Exception as e:
                logger.error(f"Failed to submit proposal: {e}")
        
        analysis_history.append({
            "timestamp": datetime.utcnow(),
            "symbol": request.signal.symbol,
            "recommendation": decision.recommendation,
            "confidence": decision.confidence
        })
        
        logger.info(
            f"Analysis complete: {decision.recommendation.value} "
            f"with {decision.confidence:.0%} confidence"
        )
        
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error analyzing signal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/backtest-decision")
async def backtest_decision(backtest_data: BacktestDecision):
    try:
        logger.info(
            f"Backtest analysis for {backtest_data.signal.symbol} "
            f"at {backtest_data.signal.timestamp}"
        )
        
        analysis_result = {
            "signal": backtest_data.signal.dict(),
            "decision": backtest_data.decision.dict(),
            "accuracy_assessment": _assess_decision_accuracy(backtest_data)
        }
        
        if backtest_data.actual_outcome:
            analysis_result["outcome_analysis"] = _analyze_outcome(backtest_data)
            
        if backtest_data.performance_metrics:
            analysis_result["performance_summary"] = backtest_data.performance_metrics
            
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error in backtest analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest analysis failed: {str(e)}"
        )


@app.get("/metrics")
async def get_metrics():
    if not analysis_history:
        return {"message": "No analysis history available"}
        
    recent_analyses = analysis_history[-100:]
    
    recommendation_counts = {}
    total_confidence = 0
    
    for analysis in recent_analyses:
        rec = analysis["recommendation"].value
        recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        total_confidence += analysis["confidence"]
        
    return {
        "total_analyses": len(analysis_history),
        "recent_analyses": len(recent_analyses),
        "recommendation_distribution": recommendation_counts,
        "average_confidence": total_confidence / len(recent_analyses) if recent_analyses else 0,
        "last_analysis": analysis_history[-1] if analysis_history else None
    }


def _assess_decision_accuracy(backtest_data: BacktestDecision) -> Dict[str, Any]:
    if not backtest_data.actual_outcome:
        return {"status": "no_outcome_data"}
        
    decision = backtest_data.decision
    outcome = backtest_data.actual_outcome
    
    was_profitable = outcome.get("profitable", None)
    price_direction = outcome.get("price_direction", None)
    
    accuracy_score = 0.5
    
    if was_profitable is not None:
        if decision.recommendation.value in ["buy", "sell"]:
            accuracy_score = 1.0 if was_profitable else 0.0
        elif decision.recommendation.value == "hold":
            accuracy_score = 0.7 if not was_profitable else 0.3
            
    return {
        "accuracy_score": accuracy_score,
        "decision_was_correct": accuracy_score > 0.5,
        "confidence_calibration": abs(decision.confidence - accuracy_score)
    }


def _analyze_outcome(backtest_data: BacktestDecision) -> Dict[str, Any]:
    outcome = backtest_data.actual_outcome
    decision = backtest_data.decision
    
    analysis = {
        "outcome_summary": outcome.get("summary", "No summary available"),
        "decision_quality": "good" if outcome.get("profitable", False) else "needs_improvement"
    }
    
    if "price_after_signal" in outcome and backtest_data.signal.price:
        price_change = (outcome["price_after_signal"] - backtest_data.signal.price) / backtest_data.signal.price
        analysis["price_change_pct"] = round(price_change * 100, 2)
        
    if decision.risk_assessment.stop_loss_price and "min_price" in outcome:
        if outcome["min_price"] <= decision.risk_assessment.stop_loss_price:
            analysis["stop_loss_hit"] = True
            
    if decision.risk_assessment.take_profit_price and "max_price" in outcome:
        if outcome["max_price"] >= decision.risk_assessment.take_profit_price:
            analysis["take_profit_hit"] = True
            
    return analysis


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 9000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)