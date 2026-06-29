"""
Case History Agent - Retrieves and analyzes similar historical SAR cases
"""

import logging
from typing import Dict, Any
from .base import BaseAgent

logger = logging.getLogger(__name__)


class CaseHistoryAgent(BaseAgent):
    """Case History Agent - Learns from past SAR cases"""

    @property
    def agent_id(self) -> str:
        return "case_history"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve and analyze similar historical cases"""
        logger.info(f"[{self.agent_id}] Retrieving case history...")

        transaction_pattern = state["transaction_pattern"]

        # Determine case type filter from fraud analysis
        case_type_filter = None
        if state.get("fraud_analysis"):
            indicators = state["fraud_analysis"].get("risk_indicators", [])
            if any("structuring" in ind.lower() for ind in indicators):
                case_type_filter = "structuring"
            elif any("laundering" in ind.lower() for ind in indicators):
                case_type_filter = "money_laundering"

        # Query episodic memory for similar cases
        similar_cases = []
        if self.memory and self.memory.episodic:
            similar_cases = self.memory.episodic.query_similar_cases(
                transaction_pattern=transaction_pattern,
                n_results=10,
                case_type_filter=case_type_filter
            )
            self._log_memory_access(
                state=state,
                memory_type="episodic",
                query=f"{transaction_pattern} [filter: {case_type_filter}]",
                results=similar_cases,
                similarity_scores=[c.get("similarity_score") for c in similar_cases]
            )

        # Extract lessons learned
        lessons = self._extract_lessons_learned(similar_cases)

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(similar_cases, state)

        # Build analysis result
        analysis_result = {
            "similar_cases_count": len(similar_cases),
            "case_type_filter": case_type_filter,
            "similar_cases": [
                {
                    "sar_id": case.get("sar_id"),
                    "case_summary": case.get("case_summary", "")[:200] + "...",
                    "similarity_score": case.get("similarity_score"),
                    "case_type": case.get("metadata", {}).get("case_type"),
                    "outcome": case.get("metadata", {}).get("outcome")
                }
                for case in similar_cases[:5]
            ],
            "lessons_learned": lessons,
            "recommended_actions": recommended_actions,
            "reasoning": self._generate_reasoning(similar_cases, lessons)
        }

        state["case_history_analysis"] = analysis_result

        self._add_message(
            state,
            f"Case history analysis complete. Found {len(similar_cases)} similar cases. "
            f"Key lessons: {len(lessons)}. Recommended actions: {len(recommended_actions)}."
        )

        logger.info(f"[{self.agent_id}] Analysis complete. {len(similar_cases)} cases retrieved.")
        return state

    def _extract_lessons_learned(self, similar_cases: list) -> list:
        """Extract key lessons from similar cases"""
        lessons = []

        if not similar_cases:
            return ["No historical precedent - treat as novel case"]

        # Extract from top 3 most similar cases
        for case in similar_cases[:3]:
            similarity = case.get("similarity_score", 0)
            if similarity > 0.8:
                case_type = case.get("metadata", {}).get("case_type", "unknown")
                lessons.append(
                    f"High similarity to {case_type} case {case.get('sar_id')} "
                    f"(similarity: {similarity:.2f})"
                )

        # Pattern-based lessons
        case_types = [c.get("metadata", {}).get("case_type") for c in similar_cases]
        if case_types.count("structuring") >= 3:
            lessons.append("Multiple historical structuring cases suggest elevated risk")

        outcomes = [c.get("metadata", {}).get("outcome") for c in similar_cases]
        if outcomes.count("referred_to_police") >= 2:
            lessons.append("Similar cases previously resulted in police referral")

        return lessons

    def _generate_recommendations(self, similar_cases: list, state: Dict[str, Any]) -> list:
        """Generate recommended actions based on case history"""
        actions = []

        if not similar_cases:
            actions.append("Conduct thorough investigation as no historical precedent exists")
            return actions

        # High similarity recommendations
        high_sim_cases = [c for c in similar_cases if c.get("similarity_score", 0) > 0.85]
        if high_sim_cases:
            actions.append("Review detailed case files of highly similar historical cases")
            actions.append("Apply lessons learned from similar case outcomes")

        # Structuring-specific
        if any(c.get("metadata", {}).get("case_type") == "structuring" for c in similar_cases[:3]):
            actions.append("Verify transaction timing across all related accounts")
            actions.append("Check for coordination with other customers")

        # General recommendations
        if state.get("risk_score", 0) > 0.7:
            actions.append("Escalate to senior compliance officer")
            actions.append("Prepare comprehensive SAR documentation")

        return actions

    def _generate_reasoning(self, similar_cases: list, lessons: list) -> str:
        """Generate reasoning text"""
        if not similar_cases:
            return "No similar historical cases found. This appears to be a novel transaction pattern requiring careful analysis."

        parts = [f"Retrieved {len(similar_cases)} similar historical SAR cases"]

        high_sim = [c for c in similar_cases if c.get("similarity_score", 0) > 0.8]
        if high_sim:
            parts.append(f"{len(high_sim)} cases show high similarity (>0.80)")

        if lessons:
            parts.append(f"Extracted {len(lessons)} key lessons from case history")

        return ". ".join(parts) + "."
