"""
Graph State Schema - Complete state for compliance workflow
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, timezone


def add_messages(existing: List, new: List) -> List:
    """Message reducer — appends new messages to existing list."""
    return existing + new


def merge_lists(existing: List, new: List) -> List:
    """List reducer — concatenates lists (for memory_traces, risk_factors)."""
    return existing + new


def last_wins(_existing: Any, new: Any) -> Any:
    """Reducer — last value wins (for single-value fields)."""
    return new


class ComplianceState(TypedDict):
    """Complete state schema for FinCompli compliance workflow."""

    # Transaction Input (set once, never modified)
    transaction_id: str
    customer_id: str
    amount: float
    currency: str
    transaction_pattern: str

    # Messages — built in-place by agents, returned as full list per node
    messages: List[Dict[str, str]]

    # Agent Results
    fraud_analysis: Optional[Dict[str, Any]]
    case_history_analysis: Optional[Dict[str, Any]]
    compliance_research: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # Risk
    risk_score: float
    risk_level: str
    risk_factors: List[str]

    # Memory Traces [PRODUCT HOOK POINT]
    memory_traces: List[Dict[str, Any]]

    # Workflow
    current_stage: str
    requires_human_review: bool
    final_decision: Optional[str]
    next_agents: Optional[List[str]]
    next_agent: Optional[str]

    # Audit
    thread_id: str
    start_time: str
    end_time: Optional[str]
    human_decision: Optional[str]
    human_comments: Optional[str]
    decision_reasoning: Optional[str]


def create_initial_state(
    transaction_id: str,
    customer_id: str,
    amount: float,
    currency: str,
    transaction_pattern: str,
    thread_id: str,
    **kwargs,
) -> ComplianceState:
    """Create initial state for a compliance workflow run."""
    return {
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "transaction_pattern": transaction_pattern,
        "messages": [],
        "fraud_analysis": None,
        "case_history_analysis": None,
        "compliance_research": None,
        "final_report": None,
        "risk_score": 0.0,
        "risk_level": "unknown",
        "risk_factors": [],
        "memory_traces": [],
        "current_stage": "input_validation",
        "requires_human_review": False,
        "final_decision": None,
        "next_agents": None,
        "next_agent": None,
        "thread_id": thread_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "human_decision": None,
        "human_comments": None,
        "decision_reasoning": None,
    }
