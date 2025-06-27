 elPyFi AI - Design Document

  Overview

  AI service that interprets signals from all strategies and
  provides trading recommendations. Starts simple (rule-based),
  evolves to use LLMs.

  Core Purpose

  Strategies say: "I see a signal"
  AI says: "Here's what to do about it"

  Architecture Choices

  Option 1: Separate Service (Recommended)

  elpyfi-ai/
  ├── analyzer.py      # Interprets signals
  ├── explainer.py     # Human-readable output
  ├── models.py        # Signal/Decision types
  └── main.py          # API server

  Why separate?
  - Can use different language (Python for LLMs)
  - Different deployment (needs more RAM/GPU)
  - Different update cycle (iterate on AI without touching
  trading)
  - Could use Claude API, OpenAI, local models

  Option 2: Module in Engine

  elpyfi-engine/
  └── ai/
      └── decision_maker.py

  Why not?
  - Engine should be FAST and RELIABLE
  - AI experiments shouldn't risk trading system
  - Different dependencies (transformers, torch, etc)

  Implementation (Simple Start)

  analyzer.py

  from typing import List, Dict
  from dataclasses import dataclass

  @dataclass
  class Signal:
      strategy: str
      symbol: str
      action: str  # buy/sell/hold
      confidence: float
      timestamp: datetime

  @dataclass
  class Decision:
      action: str  # "buy", "wait", "close_position"
      size: float  # 0.01 = 1% of portfolio
      reasoning: str
      confidence: float

  class SignalAnalyzer:
      def analyze(self, signals: List[Signal], context: Dict) ->
   Decision:
          """
          V1: Simple rules
          V2: ML model
          V3: LLM with context
          """

          # Count agreeing signals
          buy_signals = [s for s in signals if s.action ==
  "buy"]
          sell_signals = [s for s in signals if s.action ==
  "sell"]

          # Simple rule: 2+ strategies agree
          if len(buy_signals) >= 2:
              avg_confidence = sum(s.confidence for s in
  buy_signals) / len(buy_signals)

              return Decision(
                  action="buy",
                  size=0.02 if avg_confidence > 0.8 else 0.01,
                  reasoning=f"{len(buy_signals)} strategies 
  signal buy",
                  confidence=avg_confidence
              )

          return Decision(
              action="wait",
              size=0.0,
              reasoning="Insufficient agreement between 
  strategies",
              confidence=0.0
          )

  explainer.py

  class DecisionExplainer:
      """Generate human-readable explanations"""

      def explain(self, signals: List[Signal], decision: 
  Decision) -> str:
          """
          V1: Template-based
          V2: LLM-generated
          """

          if decision.action == "buy":
              return f"""
  📈 BUY RECOMMENDATION

  Confidence: {decision.confidence:.0%}
  Position Size: {decision.size:.1%} of portfolio

  Reasoning:
  {decision.reasoning}

  Supporting Signals:
  {self._format_signals(signals)}

  Risk Note: {self._risk_assessment(decision)}
  """

          return f"⏸️ WAIT - {decision.reasoning}"

  With LLM Integration (V2)

  from anthropic import Anthropic

  class LLMAnalyzer:
      def __init__(self):
          self.client =
  Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

      async def analyze_with_context(self, signals, market_data,
   portfolio):
          prompt = f"""
  You are analyzing trading signals for a PDT-constrained 
  account.

  Current Signals:
  {json.dumps(signals, indent=2)}

  Portfolio Status:
  - Value: ${portfolio['value']}
  - Day Trades Used: {portfolio['pdt_used']}/3
  - Open Positions: {portfolio['positions']}

  Market Context:
  - SPY: {market_data['spy_trend']}
  - VIX: {market_data['vix']}

  Provide a trading decision with reasoning.
  """

          response = await self.client.messages.create(
              model="claude-3-haiku",  # Fast and cheap
              messages=[{"role": "user", "content": prompt}],
              max_tokens=500
          )

          return self._parse_llm_response(response)

  API Endpoints

  from fastapi import FastAPI

  app = FastAPI()

  @app.post("/analyze")
  async def analyze_signals(signals: List[Signal], context: 
  Dict):
      """Real-time signal analysis"""
      decision = analyzer.analyze(signals, context)
      explanation = explainer.explain(signals, decision)

      return {
          "decision": decision,
          "explanation": explanation,
          "timestamp": datetime.now()
      }

  @app.post("/backtest-decision")
  async def backtest_decision(historical_signals: List[Signal]):
      """What would AI have done?"""
      # For training/testing
      pass

  Evolution Path

  V1: Rule-Based (Week 1)

  - If 2+ strategies agree → trade
  - Simple confidence thresholds
  - Template explanations

  V2: Add LLM (Week 2)

  - Claude/GPT for complex decisions
  - Natural language explanations
  - Learn from outcomes

  V3: Custom Model (Month 2)

  - Train on your trade history
  - Optimize for your style
  - Predict success probability

  Why This Design Works

  1. Separate Service = Safe experimentation
  2. Simple Start = Working system fast
  3. Clear Interface = Engine doesn't care if it's rules or AI
  4. Explainable = You understand every decision
  5. Evolvable = Start dumb, get smarter

  The AI never places trades directly - it just advises. The
  engine makes final decisions based on risk rules.

  Want me to detail any specific part?