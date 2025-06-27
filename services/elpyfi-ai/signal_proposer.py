"""
Minimal integration to submit AI analysis as proposals to elPyFi
"""

import psycopg2
import json
from datetime import datetime
from models import Decision, Signal

class SignalProposer:
    def __init__(self):
        self.conn = psycopg2.connect("postgresql://d@localhost/elpyfi")
        self.conn.autocommit = True
        
    def submit_proposal(self, signal: Signal, decision: Decision) -> int:
        """Submit high-confidence AI decisions as proposals"""
        
        # Only propose high confidence signals
        if decision.confidence < 0.70:
            return None
            
        # Only propose buy/sell (not hold)
        if decision.recommendation.value not in ["buy", "sell"]:
            return None
        
        metadata = {
            "ai_model": "claude_enhanced_v2",
            "rationale": decision.explanation,
            "risk_score": self._calculate_risk_score(decision),
            "supporting_indicators": decision.factors[:5],
            "confidence": float(decision.confidence),
            "stop_loss": decision.risk_assessment.stop_loss_price,
            "take_profit": decision.risk_assessment.take_profit_price
        }
        
        with self.conn.cursor() as cur:
            # Insert proposal
            cur.execute("""
                INSERT INTO signals (strategy, symbol, action, confidence, timestamp, metadata)
                VALUES (%s, %s, 'proposed', %s, NOW(), %s)
                RETURNING id
            """, (
                'ai_claude_analyzer',
                signal.symbol,
                float(decision.confidence),
                json.dumps(metadata)
            ))
            
            signal_id = cur.fetchone()[0]
            
            # Notify system
            cur.execute("SELECT pg_notify('trading_events', %s)", (json.dumps({
                "type": "signal.ai_generated",
                "data": {
                    "id": signal_id,
                    "symbol": signal.symbol,
                    "confidence": float(decision.confidence),
                    "risk_score": metadata["risk_score"]
                }
            }),))
            
        return signal_id
    
    def _calculate_risk_score(self, decision: Decision) -> float:
        """Convert risk assessment to 0-1 score (lower is safer)"""
        risk_map = {"low": 0.2, "medium": 0.5, "high": 0.8}
        return risk_map.get(decision.risk_assessment.risk_level, 0.5)