"""
Fraud Detection Agent - Analyzes transactions for fraud indicators.

[OBSERVABILITY] When Qwen is available, uses LLM reasoning to detect
sophisticated fraud patterns. Falls back to heuristic keyword matching.
Every memory read and output is traced via MemGuard when interceptor is set.
"""

import json
import logging
from typing import Dict, Any, List

from .base import BaseAgent

logger = logging.getLogger(__name__)

# Qwen prompt template for fraud analysis
FRAUD_ANALYSIS_PROMPT = """You are a financial crime compliance analyst. Analyze this transaction for fraud indicators.

Transaction Details:
- ID: {transaction_id}
- Customer: {customer_id}
- Amount: {currency} {amount:,.2f}
- Pattern: {transaction_pattern}
{from_account_line}{to_account_line}{to_country_line}
Historical Context (similar past cases):
{case_context}

Respond with a JSON object ONLY (no markdown, no explanation):
{{
  "risk_indicators": ["indicator 1", "indicator 2", ...],
  "fraud_score": 0.XX,
  "reasoning": "Clear, concise analysis of why this transaction is suspicious or not. Cite specific patterns and thresholds."
}}"""


class FraudDetectionAgent(BaseAgent):
    """Fraud Detection Agent — rule-based + Qwen-enhanced."""

    def __init__(self, memory_layer=None, interceptor=None, llm_client=None):
        super().__init__(memory_layer=memory_layer, interceptor=interceptor, llm_client=llm_client)

    @property
    def agent_id(self) -> str:
        return "fraud_detection"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction for fraud indicators."""
        logger.info(f"[{self.agent_id}] Starting fraud detection...")

        transaction_pattern = state["transaction_pattern"]
        input_event_ids: List[str] = []
        output_event_ids: List[str] = []

        # ── Step 1: Query episodic memory (past SAR cases) ──
        similar_cases = []
        if self.memory and self.memory.episodic:
            similar_cases = self.memory.episodic.query_similar_cases(
                transaction_pattern=transaction_pattern,
                n_results=5,
            )
            input_event_ids = self._log_memory_access(
                state=state,
                memory_type="episodic",
                query=transaction_pattern,
                results=similar_cases,
                similarity_scores=[c.get("similarity_score") for c in similar_cases],
            )

        # ── Step 2: Detect indicators (Qwen or heuristic) ──
        prompt = ""
        if self.llm:
            prompt = self._build_fraud_prompt(state, similar_cases)
            try:
                from llm_client import parse_json_response

                response = self.llm.chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                qwen_result = parse_json_response(response.content)
                fraud_indicators = qwen_result.get("risk_indicators", [])
                fraud_score = float(qwen_result.get("fraud_score", 0.0))
                reasoning = qwen_result.get(
                    "reasoning", response.content[:500]
                )
                logger.info(
                    "[%s] Qwen analysis: score=%.2f, %d indicators",
                    self.agent_id, fraud_score, len(fraud_indicators),
                )
            except Exception as e:
                logger.warning(
                    "[%s] Qwen failed, using heuristic: %s", self.agent_id, e
                )
                fraud_indicators = self._detect_fraud_indicators(state)
                fraud_score = self._calculate_fraud_score(fraud_indicators, similar_cases)
                reasoning = self._generate_reasoning(fraud_indicators, similar_cases, fraud_score)
        else:
            # Pure heuristic (no LLM configured)
            fraud_indicators = self._detect_fraud_indicators(state)
            fraud_score = self._calculate_fraud_score(fraud_indicators, similar_cases)
            reasoning = self._generate_reasoning(fraud_indicators, similar_cases, fraud_score)
            prompt = f"[heuristic] pattern={transaction_pattern}"

        # ── Step 3: Build output ──
        analysis_result = {
            "risk_indicators": fraud_indicators,
            "fraud_score": fraud_score,
            "similar_cases_count": len(similar_cases),
            "similar_cases": [
                {
                    "sar_id": case.get("sar_id"),
                    "similarity": case.get("similarity_score"),
                    "case_type": case.get("metadata", {}).get("case_type"),
                }
                for case in similar_cases[:3]
            ],
            "reasoning": reasoning,
            "llm_used": self.llm is not None,
        }

        state["fraud_analysis"] = analysis_result
        state["risk_score"] = max(state.get("risk_score", 0.0), fraud_score)
        state["risk_factors"].extend(fraud_indicators)

        # ── Step 4: Record output event ──
        output_event_id = self._record_output_event(
            memory_key="state:fraud_analysis",
            after_value={
                "fraud_score": fraud_score,
                "indicator_count": len(fraud_indicators),
                "similar_cases": len(similar_cases),
                "reasoning": reasoning[:200],
            },
            tags=[self.agent_id, "output", "fraud_analysis"],
        )
        if output_event_id:
            output_event_ids.append(output_event_id)

        # ── Step 5: DecisionTrace ──
        self._emit_decision_trace(
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids,
            prompt_text=prompt,
            output_text=reasoning,
            influence_score=0.7 if similar_cases else 0.3,
            analysis_type="fraud_detection",
            fraud_score=fraud_score,
        )

        self._add_message(
            state,
            f"Fraud detection complete. Score: {fraud_score:.2f}. "
            f"{len(fraud_indicators)} indicators, {len(similar_cases)} similar cases.",
        )

        return state

    def _build_fraud_prompt(self, state: Dict[str, Any], similar_cases: list) -> str:
        """Build the Qwen prompt with transaction context and case history."""
        case_context = "No similar historical cases found."
        if similar_cases:
            lines = []
            for i, case in enumerate(similar_cases[:3], 1):
                meta = case.get("metadata", {})
                lines.append(
                    f"  {i}. SAR #{case.get('sar_id', '?')} "
                    f"(type: {meta.get('case_type', 'unknown')}, "
                    f"similarity: {case.get('similarity_score', 0):.2f})"
                )
            case_context = "\n".join(lines)

        from_account_line = ""
        to_account_line = ""
        to_country_line = ""
        if state.get("from_account"):
            from_account_line = f"- From: {state['from_account']}\n"
        if state.get("to_account"):
            to_account_line = f"- To: {state['to_account']}\n"
        if state.get("to_country"):
            to_country_line = f"- Destination: {state['to_country']}\n"

        return FRAUD_ANALYSIS_PROMPT.format(
            transaction_id=state["transaction_id"],
            customer_id=state["customer_id"],
            amount=state["amount"],
            currency=state.get("currency", "HKD"),
            transaction_pattern=state["transaction_pattern"],
            from_account_line=from_account_line,
            to_account_line=to_account_line,
            to_country_line=to_country_line,
            case_context=case_context,
        )

    # ── Heuristic methods (fallback when no LLM) ──

    def _detect_fraud_indicators(self, state: Dict[str, Any]) -> list:
        indicators = []
        pattern = state["transaction_pattern"].lower()
        amount = state["amount"]

        if any(
            kw in pattern
            for kw in ["multiple transactions", "below threshold", "split", "structured"]
        ):
            indicators.append("Structuring pattern detected")

        if amount >= 480000 and amount < 500000:
            indicators.append("Amount just below HKD 500K threshold")

        if "jurisdiction" in pattern or "multiple countries" in pattern:
            indicators.append("Multi-jurisdiction pattern")

        if "short time" in pattern or "minutes" in pattern:
            indicators.append("Short time window")

        return indicators

    def _calculate_fraud_score(self, indicators: list, similar_cases: list) -> float:
        indicator_score = min(len(indicators) * 0.18, 0.7)
        case_boost = 0.0
        if similar_cases:
            high_sim = [c for c in similar_cases if c.get("similarity_score", 0) > 0.8]
            if high_sim:
                case_boost = min(len(high_sim) * 0.1, 0.3)
        return round(min(indicator_score + case_boost, 1.0), 2)

    def _generate_reasoning(
        self, indicators: list, similar_cases: list, score: float
    ) -> str:
        parts = []
        if indicators:
            parts.append(f"Detected {len(indicators)} fraud indicators")
        if similar_cases:
            high_sim = [c for c in similar_cases if c.get("similarity_score", 0) > 0.8]
            if high_sim:
                parts.append(f"Found {len(high_sim)} highly similar cases (>0.80)")
        if score >= 0.85:
            parts.append("HIGH RISK: Recommend human review")
        elif score >= 0.50:
            parts.append("MEDIUM RISK: Enhanced due diligence")
        else:
            parts.append("LOW RISK: Within normal parameters")
        return ". ".join(parts) + "."
