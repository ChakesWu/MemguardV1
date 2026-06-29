"""
LangGraph Node Functions - Each node wraps an agent or special logic

[Business Purpose] Bridge between LangGraph execution and agent business logic
[業務目的] LangGraph 執行和 Agent 業務邏輯之間的橋樑
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def fraud_detection_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """
    LangGraph node: Execute Fraud Detection Agent
    LangGraph 節點：執行詐欺偵測 Agent

    Note: Agents are passed via config to avoid global state
    """
    from agents.fraud_detection import FraudDetectionAgent

    agent = FraudDetectionAgent()
    state["current_stage"] = "fraud_detection"
    logger.info(f"[NODE] fraud_detection: analyzing transaction...")
    return agent.analyze(state)


def case_history_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """LangGraph node: Execute Case History Agent"""
    from agents.case_history import CaseHistoryAgent

    agent = CaseHistoryAgent()
    state["current_stage"] = "case_history"
    logger.info(f"[NODE] case_history: retrieving similar cases...")
    return agent.analyze(state)


def compliance_research_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """LangGraph node: Execute Compliance Research Agent"""
    from agents.compliance_research import ComplianceResearchAgent

    agent = ComplianceResearchAgent()
    state["current_stage"] = "compliance_research"
    logger.info(f"[NODE] compliance_research: querying regulations...")
    return agent.analyze(state)


def report_generation_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """LangGraph node: Execute Report Generation Agent"""
    from agents.report_generation import ReportGenerationAgent

    agent = ReportGenerationAgent()
    state["current_stage"] = "report_generation"
    logger.info(f"[NODE] report_generation: creating SAR draft...")
    return agent.analyze(state)


def supervisor_route_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """
    LangGraph node: Supervisor initial routing
    LangGraph 節點：Supervisor 初始路由

    Decides which agents to dispatch based on transaction data.
    根據交易數據決定調度哪些 Agent。
    """
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "supervisor_route"

    # Determine which agents to run
    agents_to_run = supervisor.route_initial(state)
    state["next_agents"] = agents_to_run

    logger.info(f"[NODE] supervisor_route: dispatching {agents_to_run}")
    return state


def supervisor_aggregate_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """
    LangGraph node: Supervisor aggregation
    LangGraph 節點：Supervisor 匯總

    Collects results from parallel agents and decides next steps.
    收集並行 Agent 的結果並決定後續步驟。
    """
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "supervisor_aggregate"

    state = supervisor.aggregate_results(state)

    logger.info(
        f"[NODE] supervisor_aggregate: risk={state.get('risk_score')}, "
        f"next={state.get('next_agent')}"
    )
    return state


def human_review_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """
    LangGraph node: Human Review (interrupt point)
    LangGraph 節點：人工審核（中斷點）

    [Business Purpose] High-risk cases pause here for compliance officer approval
    [業務目的] 高風險案件在此暫停等待合規官批准

    In production LangGraph: uses interrupt() to pause execution.
    In test/simulation: reads human_decision from state directly.
    在生產環境：使用 interrupt() 暫停執行。
    在測試/模擬：直接從 state 讀取 human_decision。
    """
    from agents.supervisor import SupervisorAgent

    supervisor = SupervisorAgent()
    state["current_stage"] = "human_review"

    logger.info(f"[NODE] human_review: awaiting decision...")

    # If human_decision already set (simulation mode), process it
    if state.get("human_decision"):
        state = supervisor.human_review_decision(state)
    else:
        # In real LangGraph: state = interrupt("Review required")
        # For now, auto-approve for demo/testing
        state["human_decision"] = "approve"
        state["human_comments"] = "AUTO-APPROVED for baseline demo"
        state = supervisor.human_review_decision(state)
        logger.warning("[NODE] auto-approving for baseline demo")

    return state


def final_submission_node(state: Dict[str, Any], config: dict = None) -> Dict[str, Any]:
    """
    LangGraph node: Final submission and archiving
    LangGraph 節點：最終提交和存檔

    [Business Purpose] Records final decision and completes the workflow
    [業務目的] 記錄最終決定並完成工作流程
    """
    state["current_stage"] = "completed"
    state["end_time"] = datetime.now(timezone.utc).isoformat()

    # Determine final outcome based on available data
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
        f"{state.get('risk_level', 'unknown')}. "
        f"Decision: {state['final_decision']}."
    )

    logger.info(
        f"[NODE] final_submission: decision={state['final_decision']}, "
        f"completed at {state['end_time']}"
    )

    return state


def build_compliance_graph(memory_saver=None, memory_layer=None):
    """
    Build the complete compliance analysis LangGraph
    構建完整的合規分析 LangGraph

    Graph structure:
    START → supervisor_route
              ↓
         [parallel dispatch]
              ↓
    fraud_detection ←→ case_history_retrieval
              ↓
    supervisor_aggregate
              ↓
         [conditional: needs_research?]
       yes /        \ no
    compliance   report_generation
    research          ↓
        ↓        [conditional: human_review?]
    report_      yes /        \ no
    generation  human_    final_submission
                  review        ↓
                    ↓         END
              final_submission
                    ↓
                   END

    Args:
        memory_saver: LangGraph checkpointer (e.g., SqliteSaver)
        memory_layer: MemoryLayer instance for agent memory access

    Returns:
        Compiled LangGraph StateGraph
    """
    from langgraph.graph import StateGraph, START, END
    from .state import ComplianceState

    builder = StateGraph(ComplianceState)

    # Add all nodes
    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("case_history_retrieval", case_history_node)
    builder.add_node("supervisor_aggregate", supervisor_aggregate_node)
    builder.add_node("compliance_research", compliance_research_node)
    builder.add_node("report_generation", report_generation_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("final_submission", final_submission_node)

    # Define flow
    builder.add_edge(START, "supervisor_route")

    # Parallel execution: both agents run simultaneously
    builder.add_edge("supervisor_route", "fraud_detection")
    builder.add_edge("supervisor_route", "case_history_retrieval")

    # Both parallel agents feed into supervisor_aggregate
    builder.add_edge("fraud_detection", "supervisor_aggregate")
    builder.add_edge("case_history_retrieval", "supervisor_aggregate")

    # Conditional routing after aggregation
    builder.add_conditional_edges(
        "supervisor_aggregate",
        route_by_risk,
        {
            "needs_research": "compliance_research",
            "skip_to_report": "report_generation",
            "low_risk_final": "final_submission"
        }
    )

    # After compliance research, always go to report generation
    builder.add_edge("compliance_research", "report_generation")

    # Conditional routing after report generation
    builder.add_conditional_edges(
        "report_generation",
        route_by_human_review,
        {
            "human_required": "human_review",
            "auto_approve": "final_submission"
        }
    )

    builder.add_edge("human_review", "final_submission")
    builder.add_edge("final_submission", END)

    # Compile graph
    if memory_saver:
        graph = builder.compile(checkpointer=memory_saver)
    else:
        graph = builder.compile()

    logger.info(f"[GRAPH] Compiled with {len(graph.nodes)} nodes")
    return graph


def route_by_risk(state: Dict[str, Any]) -> str:
    """
    Conditional routing based on risk score
    根據風險分數的條件路由

    Returns:
        Next node name
    """
    risk_score = state.get("risk_score", 0)

    if risk_score >= 0.5:
        return "needs_research"
    elif risk_score >= 0.3:
        return "skip_to_report"
    else:
        return "low_risk_final"


def route_by_human_review(state: Dict[str, Any]) -> str:
    """
    Conditional routing based on human review requirement
    根據人工審核要求的條件路由

    Returns:
        Next node name
    """
    if state.get("requires_human_review", False):
        return "human_required"
    else:
        return "auto_approve"
