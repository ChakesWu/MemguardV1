"""
API Schemas - Pydantic models for request/response validation
API 模式 - 用於請求/響應驗證的 Pydantic 模型

[Business Purpose] Standardizes API contract for compliance workflow
[業務目的] 標準化合規工作流程的 API 合約
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request to analyze a transaction"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="HKD", description="Currency code")
    transaction_pattern: str = Field(..., description="Description of transaction pattern")
    from_account: Optional[str] = Field(default=None)
    to_account: Optional[str] = Field(default=None)
    to_country: Optional[str] = Field(default=None)
    thread_id: Optional[str] = Field(default=None)


class AnalyzeResponse(BaseModel):
    """Response after analysis is started"""
    thread_id: str
    transaction_id: str
    status: str
    current_stage: str


class StatusResponse(BaseModel):
    """Response for status queries"""
    thread_id: str
    transaction_id: str
    status: str
    current_stage: str
    risk_score: Optional[float] = 0.0
    risk_level: Optional[str] = "unknown"
    requires_human_review: bool = False
    final_decision: Optional[str] = None
    memory_traces_count: int = 0
    messages_count: int = 0


class HumanDecisionRequest(BaseModel):
    """Request to submit human review decision"""
    reviewer_id: str = Field(..., description="Compliance officer identifier")
    decision: str = Field(..., description="Decision: approve | reject | request_more_info")
    comments: Optional[str] = Field(default="")


class HumanDecisionResponse(BaseModel):
    """Response after human decision is processed"""
    thread_id: str
    final_decision: str
    status: str = "completed"


class MemoryTraceItem(BaseModel):
    """Single memory trace record"""
    timestamp: str
    memory_type: str
    agent_id: str
    query: str
    result_count: int
    memory_ids: List[str]
    similarity_scores: List[float]


class MemoryTracesResponse(BaseModel):
    """Response for memory traces query"""
    thread_id: str
    total_traces: int
    traces: List[Dict[str, Any]]


class ReportResponse(BaseModel):
    """Response for report query"""
    thread_id: str
    transaction_id: str
    risk_score: float
    risk_level: str
    final_decision: Optional[str]
    sar_draft: Optional[str]
    memory_traces: List[Dict[str, Any]]
    execution_summary: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    version: str
    agents_loaded: List[str]
    scenarios_available: List[str]
    memory_status: Dict[str, Any]
