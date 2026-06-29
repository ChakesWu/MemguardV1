"""
Graph State Schema - Complete state for compliance workflow
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, timezone


def add_messages(existing: List, new: List) -> List:
    """Message reducer"""
    return existing + new


class ComplianceState(TypedDict):
    """Complete state schema for FinCompli compliance workflow"""
    
    # Transaction Input
    transaction_id: str
    customer_id: str
    amount: float
    currency: str
    transaction_pattern: str
    
    # Messages
    messages: Annotated[List[Dict[str, str]], add_messages]
    
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
    
    # Audit
    thread_id: str
    start_time: str


def create_initial_state(transaction_id: str, customer_id: str, amount: float, 
                         currency: str, transaction_pattern: str, thread_id: str, **kwargs) -> ComplianceState:
    """Create initial state"""
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
        "thread_id": thread_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
    }
