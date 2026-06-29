"""
Supervisor Agent - Coordinates all compliance sub-agents

[Business Purpose] Master coordinator deciding which agents run, 
aggregating results, and determining workflow routing
[業務目的] 主管協調員，決定哪些 Agent 運行、匯總結果、確定工作流程路由
"""

import logging
from typing import Dict, Any, List
from .base import BaseAgent

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Supervisor Agent - Master coordinator for compliance workflow"""

    @property
    def agent_id(self) -> str:
        return "supervisor"

    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Not used - Supervisor uses dedicated routing methods"""
        return state

    def route_initial(self, state: Dict[str, Any]) -> List[str]:
        """
        Initial routing decision: which agents to run
        初始路由決策：運行哪些 Agent

        For all transactions, fraud_detection and case_history run in parallel.
        對所有交易，fraud_detection 和 case_history 並行運行。

        Returns:
            List of agent names to execute
        """
        txn_pattern = state.get("transaction_pattern", "").lower()
        amount = state.get("amount", 0)

        agents_to_run = ["fraud_detection", "case_history"]

        logger.info(
            f"[{self.agent_id}] Initial route: {agents_to_run} "
            f"(amount={amount}, pattern_preview={txn_pattern[:50]})"
        )

        return agents_to_run

    def aggregate_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate results from parallel agents and decide next steps
        匯總並行 Agent 的結果並決定後續步驟

        After fraud_detection and case_history complete, the supervisor:
        1. Reviews combined findings
        2. Computes final risk assessment
        3. Decides whether compliance_research is needed
        4. Determines if human review is required

        Args:
            state: Current state with fraud_analysis and case_history_analysis

        Returns:
            Updated state with routing decisions
        """
        logger.info(f"[{self.agent_id}] Aggregating agent results...")

        # --- Risk Score Aggregation ---
        fraud_score = 0.0
        if state.get("fraud_analysis"):
            fraud_score = state["fraud_analysis"].get("fraud_score", 0.0)

        # Case history can boost or reduce risk
        case_history_modifier = self._compute_case_history_modifier(state)

        # Final aggregated risk score
        aggregated_score = min(fraud_score + case_history_modifier, 1.0)
        aggregated_score = round(max(aggregated_score, 0.0), 2)

        # --- Risk Level Classification ---
        risk_level = self._classify_risk_level(aggregated_score)

        # --- Routing Decision ---
        needs_compliance_research = aggregated_score >= 0.5
        needs_human_review = aggregated_score >= 0.85

        # --- Update State ---
        state["risk_score"] = aggregated_score
        state["risk_level"] = risk_level
        state["requires_human_review"] = needs_human_review

        # Determine next stage
        if needs_compliance_research:
            state["current_stage"] = "compliance_research"
            state["next_agent"] = "compliance_research"
        else:
            state["current_stage"] = "report_generation"
            state["next_agent"] = "report_generation"

        # Aggregate all risk factors
        all_factors = list(state.get("risk_factors", []))
        if state.get("fraud_analysis"):
            all_factors.extend(state["fraud_analysis"].get("risk_indicators", []))
        state["risk_factors"] = list(set(all_factors))

        # Supervisor message
        self._add_message(
            state,
            f"Supervisor aggregate: risk_score={aggregated_score:.2f} ({risk_level}), "
            f"compliance_research={'needed' if needs_compliance_research else 'skipped'}, "
            f"human_review={'required' if needs_human_review else 'not required'}."
        )

        logger.info(
            f"[{self.agent_id}] Aggregation complete: "
            f"score={aggregated_score}, level={risk_level}, "
            f"human_review={needs_human_review}"
        )

        return state

    def decide_after_compliance(self, state: Dict[str, Any]) -> str:
        """
        Decide next step after compliance research
        合規研究後的下一步決策

        Returns:
            Next node name: "report_generation" or "final_submission"
        """
        if state.get("risk_score", 0) >= 0.85:
            return "report_generation"
        elif state.get("risk_score", 0) >= 0.3:
            return "report_generation"
        else:
            return "final_submission"

    def decide_after_report(self, state: Dict[str, Any]) -> str:
        """
        Decide next step after report generation
        報告生成後的下一步決策

        Returns:
            Next node name
        """
        if state.get("requires_human_review", False):
            return "human_review"
        else:
            return "final_submission"

    def _compute_case_history_modifier(self, state: Dict[str, Any]) -> float:
        """
        Compute risk modifier from case history analysis
        從案例歷史分析計算風險修正值

        - Highly similar historical cases with negative outcomes → increase risk
        - No similar cases → neutral
        - Cases with "dismissed" outcomes → slight decrease

        Returns:
            Modifier value (-0.2 to +0.2)
        """
        if not state.get("case_history_analysis"):
            return 0.0

        similar_cases = state["case_history_analysis"].get("similar_cases", [])
        if not similar_cases:
            return 0.0

        modifier = 0.0
        high_sim_cases = [c for c in similar_cases if c.get("similarity_score", 0) > 0.8]

        for case in high_sim_cases:
            outcome = case.get("outcome", "")
            if outcome in ("referred_to_police", "filed"):
                modifier += 0.05
            elif outcome == "dismissed":
                modifier -= 0.02

        return round(max(min(modifier, 0.2), -0.2), 2)

    def _classify_risk_level(self, score: float) -> str:
        """
        Classify risk score into level
        將風險分數分類為等級

        Args:
            score: Aggregated risk score (0.0-1.0)

        Returns:
            Risk level string
        """
        if score >= 0.85:
            return "critical"
        elif score >= 0.50:
            return "high"
        elif score >= 0.30:
            return "medium"
        else:
            return "low"

    def human_review_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process human review decision (placeholder for interrupt logic)
        處理人工審核決定

        In a real LangGraph workflow, this would use interrupt().
        在真實 LangGraph 工作流中，這將使用 interrupt()。

        Args:
            state: Current state with final_report

        Returns:
            Updated state
        """
        decision = state.get("human_decision")
        comments = state.get("human_comments", "")

        if decision == "approve":
            state["final_decision"] = "file_sar"
            state["decision_reasoning"] = f"Approved by compliance officer. {comments}"
        elif decision == "reject":
            state["final_decision"] = "clear"
            state["decision_reasoning"] = f"Rejected by compliance officer. {comments}"
        else:
            state["final_decision"] = "pending_review"
            state["decision_reasoning"] = f"Pending: {comments}"

        self._add_message(
            state,
            f"Human review decision: {decision}. "
            f"Final outcome: {state['final_decision']}."
        )

        return state
