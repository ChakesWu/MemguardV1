"""
Graph Builder - Assembles the complete LangGraph compliance workflow

[Business Purpose] Connects all agents into a coordinated analysis pipeline
[業務目的] 將所有 Agent 連接成協調的分析管道
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def build_compliance_graph(memory_saver=None, memory_layer=None):
    """
    Build the complete compliance analysis LangGraph

    Graph structure:
    ```
    START
      ↓
    [supervisor_route]         ← Initial routing decision
      ↓
    [fraud_detection] ←→ [case_history_retrieval]   ← Parallel
      ↓
    [supervisor_aggregate]      ← Combine results
      ↓ (conditional)
    [compliance_research]       ← If risk >= 0.5
      ↓
    [report_generation]         ← SAR draft
      ↓ (conditional)
    [human_review]              ← If risk >= 0.85
      ↓
    [final_submission]          ← Archive & complete
      ↓
    END
    ```

    Args:
        memory_saver: Optional LangGraph checkpointer
        memory_layer: Optional MemoryLayer instance for agent memory access

    Returns:
        Compiled LangGraph StateGraph ready for invocation
    """
    from langgraph.graph import StateGraph, START, END
    from .state import ComplianceState
    from .nodes import (
        fraud_detection_node,
        case_history_node,
        compliance_research_node,
        report_generation_node,
        supervisor_route_node,
        supervisor_aggregate_node,
        human_review_node,
        final_submission_node,
        route_by_risk,
        route_by_human_review,
    )

    builder = StateGraph(ComplianceState)

    # Add all 8 nodes
    builder.add_node("supervisor_route", supervisor_route_node)
    builder.add_node("fraud_detection", fraud_detection_node)
    builder.add_node("case_history_retrieval", case_history_node)
    builder.add_node("supervisor_aggregate", supervisor_aggregate_node)
    builder.add_node("compliance_research", compliance_research_node)
    builder.add_node("report_generation", report_generation_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("final_submission", final_submission_node)

    # Edges
    builder.add_edge(START, "supervisor_route")
    builder.add_edge("supervisor_route", "fraud_detection")
    builder.add_edge("supervisor_route", "case_history_retrieval")
    builder.add_edge("fraud_detection", "supervisor_aggregate")
    builder.add_edge("case_history_retrieval", "supervisor_aggregate")

    builder.add_conditional_edges(
        "supervisor_aggregate",
        route_by_risk,
        {
            "needs_research": "compliance_research",
            "skip_to_report": "report_generation",
            "low_risk_final": "final_submission",
        },
    )

    builder.add_edge("compliance_research", "report_generation")

    builder.add_conditional_edges(
        "report_generation",
        route_by_human_review,
        {
            "human_required": "human_review",
            "auto_approve": "final_submission",
        },
    )

    builder.add_edge("human_review", "final_submission")
    builder.add_edge("final_submission", END)

    if memory_saver:
        graph = builder.compile(checkpointer=memory_saver)
    else:
        graph = builder.compile()

    logger.info(f"Graph compiled: {len(graph.nodes)} nodes")
    return graph


def run_compliance_workflow(
    graph,
    state: Dict[str, Any],
    thread_id: str = "default-thread"
) -> Dict[str, Any]:
    """Run the compliance workflow end-to-end"""
    config = {"configurable": {"thread_id": thread_id}}
    logger.info(f"Starting workflow: {state.get('transaction_id')}")
    final_state = graph.invoke(state, config)
    logger.info(f"Workflow complete: {final_state.get('final_decision')}")
    return final_state
