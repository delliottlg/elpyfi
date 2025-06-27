"""
AI-powered analyzer using Claude for advanced signal interpretation (V2)
"""

import os
import json
from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from models import (
    Signal, Decision, RiskAssessment, TradingConstraints,
    SignalType
)
from analyzer import SignalAnalyzer
from logging_config import get_logger

logger = get_logger(__name__)

class AISignalAnalyzer(SignalAnalyzer):
    """Enhanced analyzer that uses Claude for sophisticated analysis"""
    
    def __init__(self):
        super().__init__()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Fast and cost-effective
        
    def analyze(
        self, 
        signal: Signal, 
        constraints: Optional[TradingConstraints] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Decision:
        """Analyze signal using Claude AI"""
        
        # First, get the rule-based analysis as a baseline
        rule_based_decision = super().analyze(signal, constraints, user_preferences)
        
        try:
            # Prepare context for Claude
            prompt = self._build_analysis_prompt(signal, constraints, rule_based_decision)
            
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Lower temperature for more consistent analysis
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            ai_analysis = self._parse_ai_response(response.content[0].text)
            
            # Log Claude's response for debugging
            logger.debug(f"Claude's raw response: {response.content[0].text[:500]}...")
            logger.debug(f"Parsed analysis: {ai_analysis}")
            
            # Merge AI insights with rule-based analysis
            return self._merge_decisions(rule_based_decision, ai_analysis, signal)
            
        except Exception as e:
            logger.error(f"AI analysis failed, falling back to rule-based: {e}")
            return rule_based_decision
    
    def _get_system_prompt(self) -> str:
        """System prompt to configure Claude's behavior"""
        return """You are an expert trading signal analyst. Analyze trading signals and provide actionable insights.

Your analysis should consider:
1. Technical indicators and their relationships
2. Market conditions and volatility
3. Risk management principles
4. Pattern Day Trading (PDT) rules when applicable
5. Position sizing based on risk

Provide analysis in JSON format with these exact fields:
{
    "recommendation": "buy" | "sell" | "hold" | "stop_loss" | "take_profit",
    "confidence": 0.0 to 1.0,
    "plain_english_thoughts": "Write a full paragraph (3-5 sentences) explaining your analysis in plain English. Talk like you're explaining to a friend over coffee. Be specific about what you see and why it matters.",
    "key_insights": ["insight1", "insight2", "insight3"],
    "risk_factors": ["risk1", "risk2"],
    "hidden_patterns": "any non-obvious patterns you detect",
    "market_psychology": "current market sentiment interpretation"
}

Be conservative with recommendations. When uncertain, recommend hold."""
    
    def _build_analysis_prompt(
        self, 
        signal: Signal, 
        constraints: Optional[TradingConstraints],
        rule_based: Decision
    ) -> str:
        """Build a comprehensive prompt for Claude"""
        
        prompt = f"""Analyze this trading signal for {signal.symbol}:

Current Price: ${signal.price}
Signal Type: {signal.type.value}

Technical Indicators:"""
        
        for indicator in signal.indicators:
            prompt += f"\n- {indicator.name}: {indicator.value:.2f} ({indicator.timeframe.value})"
        
        if signal.market_conditions:
            prompt += f"\n\nMarket Conditions:"
            prompt += f"\n- Trend: {signal.market_conditions.trend}"
            prompt += f"\n- Volatility: {signal.market_conditions.volatility:.0%}"
            prompt += f"\n- Volume: {signal.market_conditions.volume:,}"
            
            if signal.market_conditions.support_levels:
                prompt += f"\n- Support: {signal.market_conditions.support_levels}"
            if signal.market_conditions.resistance_levels:
                prompt += f"\n- Resistance: {signal.market_conditions.resistance_levels}"
        
        if constraints:
            prompt += f"\n\nAccount Constraints:"
            if constraints.pdt_trades_remaining is not None:
                prompt += f"\n- PDT trades remaining: {constraints.pdt_trades_remaining}"
            if constraints.account_balance:
                prompt += f"\n- Account balance: ${constraints.account_balance:,.2f}"
            if constraints.existing_positions:
                prompt += f"\n- Existing positions: {len(constraints.existing_positions)}"
        
        prompt += f"\n\nRule-based system suggests: {rule_based.recommendation.value} with {rule_based.confidence:.0%} confidence"
        prompt += f"\nKey factors identified: {', '.join(rule_based.factors[:3])}"
        
        prompt += "\n\nProvide your advanced analysis considering all factors above."
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response (Claude might add explanation text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            return json.loads(json_str)
        except:
            # If parsing fails, return a safe default
            return {
                "recommendation": "hold",
                "confidence": 0.5,
                "key_insights": ["AI parsing failed, using fallback"],
                "risk_factors": ["Technical analysis only"]
            }
    
    def _merge_decisions(
        self, 
        rule_based: Decision, 
        ai_analysis: Dict[str, Any],
        signal: Signal
    ) -> Decision:
        """Merge rule-based and AI analyses into final decision"""
        
        # Parse AI recommendation
        ai_rec = ai_analysis.get("recommendation", "hold")
        ai_confidence = float(ai_analysis.get("confidence", 0.5))
        
        # Weight the decisions (60% AI, 40% rules for now)
        if ai_rec == rule_based.recommendation.value:
            # Both agree - higher confidence
            final_confidence = min(0.95, (ai_confidence * 0.6 + rule_based.confidence * 0.4) * 1.1)
            final_recommendation = rule_based.recommendation
        else:
            # Disagreement - be more cautious
            if ai_confidence > 0.7 and rule_based.confidence < 0.5:
                # Trust AI if it's confident and rules are not
                final_recommendation = SignalType(ai_rec)
                final_confidence = ai_confidence * 0.8
            elif rule_based.confidence > 0.7 and ai_confidence < 0.5:
                # Trust rules if they're confident and AI is not
                final_recommendation = rule_based.recommendation
                final_confidence = rule_based.confidence * 0.8
            else:
                # Both uncertain or both confident but disagree - hold
                final_recommendation = SignalType.HOLD
                final_confidence = 0.4
        
        # Combine factors from both analyses
        all_factors = rule_based.factors.copy()
        
        # Add AI insights
        ai_insights = ai_analysis.get("key_insights", [])
        for insight in ai_insights[:2]:  # Add top 2 AI insights
            all_factors.append(f"AI: {insight}")
        
        # Add any hidden patterns detected
        if "hidden_patterns" in ai_analysis and ai_analysis["hidden_patterns"]:
            all_factors.append(f"Pattern: {ai_analysis['hidden_patterns']}")
        
        # Enhanced explanation with Claude's thoughts
        plain_thoughts = ai_analysis.get("plain_english_thoughts", "")
        market_psychology = ai_analysis.get("market_psychology", "")
        
        enhanced_explanation = rule_based.explanation
        if plain_thoughts:
            enhanced_explanation = f"Claude says: {plain_thoughts} | {enhanced_explanation}"
        if market_psychology:
            enhanced_explanation += f" Market sentiment: {market_psychology}"
        
        # Risk assessment can be enhanced with AI risk factors
        risk_assessment = rule_based.risk_assessment
        ai_risks = ai_analysis.get("risk_factors", [])
        if ai_risks and len(all_factors) < 8:
            all_factors.extend([f"Risk: {risk}" for risk in ai_risks[:2]])
        
        return Decision(
            recommendation=final_recommendation,
            confidence=final_confidence,
            explanation=enhanced_explanation,
            factors=all_factors[:7],  # Limit to 7 most important
            risk_assessment=risk_assessment,
            alternative_actions=rule_based.alternative_actions,
            metadata={
                **rule_based.metadata,
                "ai_enabled": True,
                "ai_confidence": ai_confidence,
                "ai_recommendation": ai_rec,
                "analyzer_version": "2.0"
            }
        )


class MockAIAnalyzer(AISignalAnalyzer):
    """Mock AI analyzer for testing without API calls"""
    
    def __init__(self):
        # Skip parent init to avoid API key requirement
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
        """Simulate AI analysis without actual API calls"""
        
        # Get rule-based analysis
        rule_based = SignalAnalyzer().analyze(signal, constraints, user_preferences)
        
        # Simulate AI enhancement
        import random
        
        # Simulate finding patterns
        patterns = [
            "Potential cup and handle formation",
            "Divergence between price and volume",
            "Momentum shift detected in shorter timeframes",
            "Institutional accumulation pattern",
            "Retail exhaustion signals present"
        ]
        
        market_sentiments = [
            "Cautious optimism with underlying strength",
            "Fear-driven selling creating opportunities",
            "Euphoric buying requiring caution",
            "Consolidation before next major move",
            "Smart money rotating into position"
        ]
        
        # Add some "AI insights"
        enhanced_factors = rule_based.factors.copy()
        enhanced_factors.append(f"AI: {random.choice(patterns)}")
        enhanced_factors.append(f"Sentiment: {random.choice(market_sentiments)}")
        
        # Slightly adjust confidence based on "AI analysis"
        ai_adjustment = random.uniform(-0.1, 0.15)
        new_confidence = max(0.1, min(0.95, rule_based.confidence + ai_adjustment))
        
        enhanced_explanation = rule_based.explanation + " [AI Enhanced]"
        
        return Decision(
            recommendation=rule_based.recommendation,
            confidence=new_confidence,
            explanation=enhanced_explanation,
            factors=enhanced_factors[:7],
            risk_assessment=rule_based.risk_assessment,
            alternative_actions=rule_based.alternative_actions,
            metadata={
                **rule_based.metadata,
                "ai_enabled": True,
                "ai_mode": "mock",
                "analyzer_version": "2.0-mock"
            }
        )