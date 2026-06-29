"""
Fraud Detection Agent - Analyzes transactions for fraud indicators
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)


class FraudDetectionAgent(BaseAgent):
    """Fraud Detection Agent"""

    @property
    def agent_id(self) -> str:
        return "fraud_detection"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction for fraud indicators"""
        logger.info(f"[{self.agent_id}] Starting fraud detection...")

        transaction_pattern = state["transaction_pattern"]
        amount = state["amount"]

        # Detect indicators
        fraud_indicators = self._detect_fraud_indicators(state)

        # Query episodic memory
        similar_cases = []
        if self.memory and self.memory.episodic:
            similar_cases = self.memory.episodic.query_similar_cases(
                transaction_pattern=transaction_pattern,
                n_results=5
            )
            self._log_memory_access(
                state=state,
                memory_type="episodic",
                query=transaction_pattern,
                results=similar_cases,
                similarity_scores=[c.get("similarity_score") for c in similar_cases]
            )

        # Calculate score
        fraud_score = self._calculate_fraud_score(fraud_indicators, similar_cases)

        # Build result
        analysis_result = {
            "risk_indicators": fraud_indicators,
            "fraud_score": fraud_score,
            "similar_cases_count": len(similar_cases),
            "similar_cases": [
                {
                    "sar_id": case.get("sar_id"),
                    "similarity": case.get("similarity_score"),
                    "case_type": case.get("metadata", {}).get("case_type")
                }
                for case in similar_cases[:3]
            ],
            "reasoning": self._generate_reasoning(fraud_indicators, similar_cases, fraud_score)
        }

        state["fraud_analysis"] = analysis_result
        state["risk_score"] = max(state.get("risk_score", 0.0), fraud_score)
        state["risk_factors"].extend(fraud_indicators)

        self._add_message(
            state,
            f"Fraud detection complete. Score: {fraud_score:.2f}. "
            f"{len(fraud_indicators)} indicators, {len(similar_cases)} similar cases."
        )

        return state

    def _detect_fraud_indicators(self, state: Dict[str, Any]) -> list:
        indicators = []
        pattern = state["transaction_pattern"].lower()
        amount = state["amount"]

        if any(kw in pattern for kw in ["multiple transactions", "below threshold", "split", "structured"]):
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

    def _generate_reasoning(self, indicators: list, similar_cases: list, score: float) -> str:
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
