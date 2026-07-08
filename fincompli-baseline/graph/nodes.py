"""
LangGraph Node Functions - Each node wraps an agent or special logic.

[OBSERVABILITY] Nodes extract llm_client, interceptor, and memory_layer from
the LangGraph config dict and pass them to agent constructors.

IMPORTANT: Each node modifies state in-place via agent.analyze(state),
then returns a partial dict of ONLY the keys that changed. This avoids
LangGraph InvalidUpdateError when nodes run in parallel.
"""

from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Keys that agents typically modify (used to build return dicts)
_AGENT_CHANGE_KEYS = {
    "fraud_detection": [
        "fraud_analysis", "risk_score", "risk_factors",
        "messages", "memory_traces", "current_stage",
    ],
    "case_history": [
        "case_history_analysis", "messages", "memory_traces", "current_stage",
    ],
    "compliance_research": [
        "compliance_research", "messages", "memory_traces", "current_stage",
    ],
    "report_generation": [
        "final_report", "messages", "memory_traces", "current_stage",
    ],
}


def _get_deps(config: dict | None) -> tuple:
    """Extract agent dependencies from LangGraph config."""
    if config is None:
        return None, None, None
    cfg = config.get("configurable", {})
    return (
        cfg.get("llm_client"),
        cfg.get("interceptor"),
        cfg.get("memory_layer"),
    )


def _run_agent(state: dict, AgentClass, change_key: str, stage_name: str,
               config: dict | None = None) -> dict:
    """Generic agent runner — returns only changed keys to avoid LangGraph conflicts."""
    llm_client, interceptor, memory_layer = _get_deps(config)
    agent = AgentClass(
        memory_layer=memory_layer,
        interceptor=interceptor,
        llm_client=llm_client,
    )
    state["current_stage"] = stage_name
    agent.analyze(state)

    # Return only keys that were actually added/modified
    keys = _AGENT_CHANGE_KEYS.get(change_key, [])
    return {k: state[k] for k in keys if k in state}


def fraud_detection_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Execute Fraud Detection Agent."""
    from agents.fraud_detection import FraudDetectionAgent
    logger.info("[NODE] fraud_detection: analyzing transaction...")
    return _run_agent(state, FraudDetectionAgent, "fraud_detection",
                      "fraud_detection", config)


def case_history_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Execute Case History Agent."""
    from agents.case_history import CaseHistoryAgent
    logger.info("[NODE] case_history: retrieving similar cases...")
    return _run_agent(state, CaseHistoryAgent, "case_history",
                      "case_history", config)


def compliance_research_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Execute Compliance Research Agent."""
    from agents.compliance_research import ComplianceResearchAgent
    logger.info("[NODE] compliance_research: querying regulations...")
    return _run_agent(state, ComplianceResearchAgent, "compliance_research",
                      "compliance_research_node", config)


def report_generation_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Execute Report Generation Agent."""
    from agents.report_generation import ReportGenerationAgent
    logger.info("[NODE] report_generation: creating SAR draft...")
    return _run_agent(state, ReportGenerationAgent, "report_generation",
                      "report_generation", config)


def supervisor_route_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Supervisor initial routing. Decides which agents to dispatch."""
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "supervisor_route"
    agents_to_run = supervisor.route_initial(state)
    state["next_agents"] = agents_to_run

    logger.info(f"[NODE] supervisor_route: dispatching {agents_to_run}")
    return {
        "current_stage": state["current_stage"],
        "next_agents": agents_to_run,
    }


def supervisor_aggregate_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Supervisor aggregation. Collects parallel agent results."""
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "supervisor_aggregate"
    state = supervisor.aggregate_results(state)

    logger.info(
        f"[NODE] supervisor_aggregate: risk={state.get('risk_score')}, "
        f"next={state.get('next_agent')}"
    )
    return {
        "risk_score": state["risk_score"],
        "risk_level": state["risk_level"],
        "requires_human_review": state["requires_human_review"],
        "current_stage": state["current_stage"],
        "next_agent": state["next_agent"],
        "risk_factors": state["risk_factors"],
        "messages": state["messages"],
    }


def human_review_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Human Review (interrupt point). High-risk cases pause for approval."""
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "human_review"
    logger.info("[NODE] human_review: awaiting decision...")

    if state.get("human_decision"):
        state = supervisor.human_review_decision(state)
    else:
        state["human_decision"] = "approve"
        state["human_comments"] = "AUTO-APPROVED for baseline demo"
        state = supervisor.human_review_decision(state)
        logger.warning("[NODE] auto-approving for baseline demo")

    return {
        "current_stage": state["current_stage"],
        "final_decision": state.get("final_decision"),
        "decision_reasoning": state.get("decision_reasoning"),
        "human_decision": state.get("human_decision"),
        "human_comments": state.get("human_comments"),
    }


def final_submission_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """Final submission and archiving."""
    from datetime import datetime, timezone

    state["current_stage"] = "completed"
    state["end_time"] = datetime.now(timezone.utc).isoformat()

    if not state.get("final_decision"):
        risk_score = state.get("risk_score", 0)
        if risk_score >= 0.85:
            state["final_decision"] = "file_sar"
        elif risk_score >= 0.30:
            state["final_decision"] = "clear_with_monitoring"
        else:
            state["final_decision"] = "clear"

    state["decision_reasoning"] = state.get("decision_reasoning") or (
        f"Risk score {state.get('risk_score', 0):.2f} classified as "
        f"{state.get('risk_level', 'unknown')}. Decision: {state['final_decision']}."
    )

    logger.info(
        f"[NODE] final_submission: decision={state['final_decision']}, "
        f"completed at {state['end_time']}"
    )
    return {
        "current_stage": state["current_stage"],
        "end_time": state["end_time"],
        "final_decision": state["final_decision"],
        "decision_reasoning": state["decision_reasoning"],
    }


def route_by_risk(state: Dict[str, Any]) -> str:
    if state.get("risk_score", 0) >= 0.5:
        return "needs_research"
    elif state.get("risk_score", 0) >= 0.3:
        return "skip_to_report"
    else:
        return "low_risk_final"


def route_by_human_review(state: Dict[str, Any]) -> str:
    if state.get("requires_human_review", False):
        return "human_required"
    else:
        return "auto_approve"
