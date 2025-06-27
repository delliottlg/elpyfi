from typing import Dict, Any, Optional, List
from datetime import datetime
from models import Decision, Signal, SignalType, RiskAssessment, TradingConstraints


class DecisionExplainer:
    def __init__(self):
        self.explanation_templates = {
            SignalType.BUY: {
                "high": "Strong buy signal detected. Multiple indicators align favorably, suggesting a high probability upward move.",
                "medium": "Moderate buy opportunity identified. Most indicators are positive, but some caution is warranted.",
                "low": "Weak buy signal. Consider waiting for stronger confirmation or better entry points."
            },
            SignalType.SELL: {
                "high": "Strong sell signal detected. Multiple indicators suggest downward pressure ahead.",
                "medium": "Moderate sell signal. Consider reducing position size or tightening stop losses.",
                "low": "Weak sell signal. May want to hold and monitor for stronger confirmation."
            },
            SignalType.HOLD: {
                "high": "Clear hold recommendation. Market conditions are uncertain, best to wait for clearer signals.",
                "medium": "Hold position recommended. Mixed signals suggest patience is the best strategy.",
                "low": "Holding suggested due to weak or conflicting signals. Monitor closely for changes."
            }
        }
        
    def explain_decision(
        self, 
        decision: Decision, 
        signal: Signal,
        constraints: Optional[TradingConstraints] = None
    ) -> str:
        sections = []
        
        sections.append(self._create_summary(decision, signal))
        
        sections.append(self._explain_indicators(decision, signal))
        
        sections.append(self._explain_risk(decision.risk_assessment, signal))
        
        if constraints:
            constraint_notes = self._explain_constraints(constraints, decision)
            if constraint_notes:
                sections.append(constraint_notes)
                
        sections.append(self._suggest_actions(decision, signal))
        
        return "\n\n".join(sections)
    
    def _create_summary(self, decision: Decision, signal: Signal) -> str:
        confidence_level = self._get_confidence_level(decision.confidence)
        
        # Check if we have Claude's explanation
        if "Claude says:" in decision.explanation:
            # Extract Claude's thoughts and the rest
            parts = decision.explanation.split(" | ")
            claude_part = parts[0] if parts else decision.explanation
            summary = f"📊 **{signal.symbol} Analysis** - {signal.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
            summary += f"💡 **{decision.recommendation.value.upper()}** @ ${signal.price:.2f}\n"
            summary += f"🎯 Confidence: {decision.confidence:.0%}\n\n"
            summary += f"💭 **{claude_part}**\n"
        else:
            # Fallback to template
            base_explanation = self.explanation_templates.get(
                decision.recommendation, {}
            ).get(confidence_level, decision.explanation)
            
            summary = f"📊 **{signal.symbol} Analysis** - {signal.timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
            summary += f"💡 **{decision.recommendation.value.upper()}** @ ${signal.price:.2f}\n"
            summary += f"🎯 Confidence: {decision.confidence:.0%}\n\n"
            summary += base_explanation
        
        return summary
    
    def _explain_indicators(self, decision: Decision, signal: Signal) -> str:
        if not decision.factors:
            return "📈 **Technical Analysis**: Limited indicator data available."
            
        explanation = "📈 **Technical Analysis**:\n"
        
        for i, factor in enumerate(decision.factors, 1):
            indicator_emoji = self._get_factor_emoji(factor)
            explanation += f"{indicator_emoji} {factor}\n"
            
        indicator_summary = self._summarize_indicators(signal.indicators)
        if indicator_summary:
            explanation += f"\n{indicator_summary}"
            
        return explanation
    
    def _explain_risk(self, risk: RiskAssessment, signal: Signal) -> str:
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk.risk_level, "⚪")
        
        explanation = f"⚠️ **Risk Assessment**: {risk_emoji} {risk.risk_level.capitalize()} Risk\n"
        
        if risk.stop_loss_price:
            sl_distance = abs(signal.price - risk.stop_loss_price) / signal.price * 100
            explanation += f"🛑 Stop Loss: ${risk.stop_loss_price:.2f} ({sl_distance:.1f}% from entry)\n"
            
        if risk.take_profit_price:
            tp_distance = abs(risk.take_profit_price - signal.price) / signal.price * 100
            explanation += f"✅ Take Profit: ${risk.take_profit_price:.2f} ({tp_distance:.1f}% from entry)\n"
            
        if risk.risk_reward_ratio:
            explanation += f"📊 Risk/Reward Ratio: 1:{risk.risk_reward_ratio:.1f}\n"
            
        if risk.position_size_recommendation:
            explanation += f"💰 Suggested Position Size: {risk.position_size_recommendation:.0%} of capital"
            
        return explanation
    
    def _explain_constraints(self, constraints: TradingConstraints, decision: Decision) -> Optional[str]:
        notes = []
        
        if constraints.pdt_trades_remaining is not None:
            if constraints.pdt_trades_remaining == 0:
                notes.append("🚫 PDT Warning: No day trades remaining!")
            elif constraints.pdt_trades_remaining <= 2:
                notes.append(f"⚠️ PDT Notice: Only {constraints.pdt_trades_remaining} day trades left")
                
        if constraints.buying_power and decision.recommendation == SignalType.BUY:
            notes.append(f"💵 Available Buying Power: ${constraints.buying_power:,.2f}")
            
        if constraints.existing_positions:
            notes.append(f"📦 Existing Positions: {len(constraints.existing_positions)}")
            
        if notes:
            return "📋 **Account Constraints**:\n" + "\n".join(notes)
            
        return None
    
    def _suggest_actions(self, decision: Decision, signal: Signal) -> str:
        explanation = "🎬 **Recommended Actions**:\n"
        
        primary_action = self._get_primary_action(decision, signal)
        explanation += f"1. {primary_action}\n"
        
        if decision.alternative_actions:
            explanation += "\n**Alternative Approaches**:\n"
            for i, action in enumerate(decision.alternative_actions[:3], 1):
                explanation += f"  • {action}\n"
                
        return explanation
    
    def _get_confidence_level(self, confidence: float) -> str:
        if confidence > 0.7:
            return "high"
        elif confidence > 0.4:
            return "medium"
        else:
            return "low"
            
    def _get_factor_emoji(self, factor: str) -> str:
        factor_lower = factor.lower()
        if "rsi" in factor_lower:
            return "📊"
        elif "macd" in factor_lower:
            return "📈"
        elif "volume" in factor_lower:
            return "🔊"
        elif "trend" in factor_lower:
            return "📉"
        elif "volatility" in factor_lower:
            return "🌊"
        else:
            return "•"
            
    def _summarize_indicators(self, indicators: List) -> str:
        if not indicators:
            return ""
            
        timeframes = set()
        for ind in indicators:
            if hasattr(ind, 'timeframe'):
                timeframes.add(ind.timeframe.value)
                
        if timeframes:
            return f"Timeframes analyzed: {', '.join(sorted(timeframes))}"
            
        return ""
    
    def _get_primary_action(self, decision: Decision, signal: Signal) -> str:
        if decision.recommendation == SignalType.BUY:
            if decision.risk_assessment.stop_loss_price:
                return f"Enter long position at ${signal.price:.2f} with stop at ${decision.risk_assessment.stop_loss_price:.2f}"
            else:
                return f"Enter long position at ${signal.price:.2f}"
                
        elif decision.recommendation == SignalType.SELL:
            if decision.risk_assessment.stop_loss_price:
                return f"Exit/Short at ${signal.price:.2f} with stop at ${decision.risk_assessment.stop_loss_price:.2f}"
            else:
                return f"Exit position or enter short at ${signal.price:.2f}"
                
        elif decision.recommendation == SignalType.HOLD:
            return "Maintain current position and monitor for changes"
            
        elif decision.recommendation == SignalType.STOP_LOSS:
            return f"Exit immediately - stop loss triggered at ${signal.price:.2f}"
            
        elif decision.recommendation == SignalType.TAKE_PROFIT:
            return f"Take profits - target reached at ${signal.price:.2f}"
            
        return "Monitor position closely"


def format_decision_for_api(decision: Decision, signal: Signal) -> Dict[str, Any]:
    explainer = DecisionExplainer()
    formatted_explanation = explainer.explain_decision(decision, signal)
    
    return {
        "signal_id": decision.signal_id,
        "timestamp": decision.timestamp.isoformat(),
        "symbol": signal.symbol,
        "price": signal.price,
        "recommendation": decision.recommendation.value,
        "confidence": decision.confidence,
        "formatted_explanation": formatted_explanation,
        "risk_assessment": {
            "level": decision.risk_assessment.risk_level,
            "stop_loss": decision.risk_assessment.stop_loss_price,
            "take_profit": decision.risk_assessment.take_profit_price,
            "position_size": decision.risk_assessment.position_size_recommendation,
            "risk_reward_ratio": decision.risk_assessment.risk_reward_ratio
        },
        "factors": decision.factors,
        "alternatives": decision.alternative_actions
    }