from typing import List, Dict, Any, Optional
from models import (
    Signal, SignalType, Decision, RiskAssessment, 
    TradingConstraints, Indicator, TimeFrame
)


class SignalAnalyzer:
    def __init__(self):
        self.indicator_weights = {
            "RSI": 0.25,
            "MACD": 0.30,
            "MA": 0.20,
            "VOLUME": 0.15,
            "BB": 0.10,
        }
        
    def analyze(
        self, 
        signal: Signal, 
        constraints: Optional[TradingConstraints] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Decision:
        confidence = self._calculate_confidence(signal)
        recommendation = self._determine_recommendation(signal, confidence)
        risk_assessment = self._assess_risk(signal, recommendation)
        factors = self._identify_key_factors(signal)
        explanation = self._generate_basic_explanation(
            signal, recommendation, confidence, factors
        )
        
        if constraints and self._should_override_for_pdt(constraints, recommendation):
            recommendation = SignalType.HOLD
            explanation = f"PDT constraint override: {explanation}"
            factors.append("PDT limit reached - recommendation changed to HOLD")
        
        return Decision(
            recommendation=recommendation,
            confidence=confidence,
            explanation=explanation,
            factors=factors,
            risk_assessment=risk_assessment,
            alternative_actions=self._get_alternative_actions(recommendation),
            metadata={"analyzer_version": "1.0", "signal_strength": confidence}
        )
    
    def _calculate_confidence(self, signal: Signal) -> float:
        if not signal.indicators:
            return 0.5
        
        indicator_scores = {}
        for indicator in signal.indicators:
            score = self._score_indicator(indicator, signal.type)
            indicator_scores[indicator.name] = score
        
        weighted_sum = 0
        total_weight = 0
        
        for name, score in indicator_scores.items():
            weight = self.indicator_weights.get(name.upper(), 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        if signal.market_conditions:
            market_adjustment = self._adjust_for_market_conditions(
                signal.market_conditions, signal.type
            )
            base_confidence = base_confidence * 0.8 + market_adjustment * 0.2
        
        return max(0.1, min(0.95, base_confidence))
    
    def _score_indicator(self, indicator: Indicator, signal_type: SignalType) -> float:
        name = indicator.name.upper()
        value = indicator.value
        
        if name == "RSI":
            if signal_type == SignalType.BUY:
                if value < 30:
                    return 0.9
                elif value < 40:
                    return 0.7
                elif value < 50:
                    return 0.5
                else:
                    return 0.3
            elif signal_type == SignalType.SELL:
                if value > 70:
                    return 0.9
                elif value > 60:
                    return 0.7
                elif value > 50:
                    return 0.5
                else:
                    return 0.3
                    
        elif name == "MACD":
            if signal_type == SignalType.BUY and value > 0:
                return 0.8
            elif signal_type == SignalType.SELL and value < 0:
                return 0.8
            else:
                return 0.4
                
        elif name == "MA" or name.startswith("MA_"):
            return 0.6
            
        elif name == "VOLUME":
            if value > 1.5:
                return 0.8
            elif value > 1.0:
                return 0.6
            else:
                return 0.4
                
        elif name == "BB" or name.startswith("BB_"):
            return 0.5
            
        return 0.5
    
    def _adjust_for_market_conditions(self, conditions, signal_type: SignalType) -> float:
        score = 0.5
        
        if conditions.trend == "bullish" and signal_type == SignalType.BUY:
            score += 0.2
        elif conditions.trend == "bearish" and signal_type == SignalType.SELL:
            score += 0.2
        elif conditions.trend == "neutral":
            score += 0.0
        else:
            score -= 0.1
            
        if conditions.volatility > 0.7:
            score -= 0.1
        elif conditions.volatility < 0.3:
            score += 0.1
            
        return max(0.0, min(1.0, score))
    
    def _determine_recommendation(self, signal: Signal, confidence: float) -> SignalType:
        if confidence < 0.4:
            return SignalType.HOLD
            
        if signal.type in [SignalType.STOP_LOSS, SignalType.TAKE_PROFIT]:
            return signal.type
            
        return signal.type
    
    def _assess_risk(self, signal: Signal, recommendation: SignalType) -> RiskAssessment:
        risk_level = "medium"
        
        if signal.market_conditions and signal.market_conditions.volatility > 0.7:
            risk_level = "high"
        elif signal.market_conditions and signal.market_conditions.volatility < 0.3:
            risk_level = "low"
            
        stop_loss_pct = 0.02 if risk_level == "low" else (0.03 if risk_level == "medium" else 0.05)
        take_profit_pct = 0.03 if risk_level == "low" else (0.05 if risk_level == "medium" else 0.08)
        
        stop_loss_price = None
        take_profit_price = None
        
        if recommendation == SignalType.BUY:
            stop_loss_price = signal.price * (1 - stop_loss_pct)
            take_profit_price = signal.price * (1 + take_profit_pct)
        elif recommendation == SignalType.SELL:
            stop_loss_price = signal.price * (1 + stop_loss_pct)
            take_profit_price = signal.price * (1 - take_profit_pct)
            
        position_size = 1.0 if risk_level == "low" else (0.5 if risk_level == "medium" else 0.25)
        
        risk_reward_ratio = take_profit_pct / stop_loss_pct if stop_loss_pct > 0 else 1.5
        
        return RiskAssessment(
            risk_level=risk_level,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            position_size_recommendation=position_size,
            risk_reward_ratio=risk_reward_ratio
        )
    
    def _identify_key_factors(self, signal: Signal) -> List[str]:
        factors = []
        
        for indicator in signal.indicators:
            if indicator.name.upper() == "RSI":
                if indicator.value < 30:
                    factors.append(f"RSI oversold at {indicator.value:.1f}")
                elif indicator.value > 70:
                    factors.append(f"RSI overbought at {indicator.value:.1f}")
            elif indicator.name.upper() == "MACD":
                if indicator.value > 0:
                    factors.append("MACD positive crossover")
                else:
                    factors.append("MACD negative crossover")
            elif indicator.name.upper() == "VOLUME":
                if indicator.value > 1.5:
                    factors.append(f"High volume spike ({indicator.value:.1f}x average)")
                    
        if signal.market_conditions:
            factors.append(f"Market trend: {signal.market_conditions.trend}")
            if signal.market_conditions.volatility > 0.7:
                factors.append("High market volatility")
                
        return factors[:5]
    
    def _generate_basic_explanation(
        self, 
        signal: Signal, 
        recommendation: SignalType,
        confidence: float,
        factors: List[str]
    ) -> str:
        action_verb = {
            SignalType.BUY: "buy",
            SignalType.SELL: "sell",
            SignalType.HOLD: "hold",
            SignalType.STOP_LOSS: "exit with stop loss",
            SignalType.TAKE_PROFIT: "take profits"
        }.get(recommendation, "hold")
        
        confidence_desc = "high" if confidence > 0.7 else ("moderate" if confidence > 0.4 else "low")
        
        explanation = f"Recommendation: {action_verb.capitalize()} {signal.symbol} with {confidence_desc} confidence ({confidence:.0%}). "
        
        if factors:
            explanation += f"Key factors: {', '.join(factors[:3])}."
            
        return explanation
    
    def _get_alternative_actions(self, recommendation: SignalType) -> List[str]:
        if recommendation == SignalType.BUY:
            return ["Wait for better entry", "Buy half position now", "Set limit order below current price"]
        elif recommendation == SignalType.SELL:
            return ["Hold for reversal", "Sell half position", "Set stop loss and hold"]
        elif recommendation == SignalType.HOLD:
            return ["Set price alerts", "Review in next timeframe", "Prepare orders for breakout"]
        else:
            return ["Adjust stop loss", "Take partial profits", "Hold position"]
    
    def _should_override_for_pdt(
        self, 
        constraints: TradingConstraints, 
        recommendation: SignalType
    ) -> bool:
        if constraints.pdt_trades_remaining is None:
            return False
            
        if constraints.pdt_trades_remaining <= 0 and recommendation in [SignalType.BUY, SignalType.SELL]:
            return True
            
        return False