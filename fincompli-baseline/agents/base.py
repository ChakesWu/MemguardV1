"""
Base Agent Class
基礎 Agent 類

Provides common functionality for all compliance agents.
為所有合規 Agent 提供通用功能。

[Business Purpose] Standardizes agent interface and memory access patterns
[業務目的] 標準化 Agent 接口和記憶訪問模式
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all compliance agents
    所有合規 Agent 的基類

    All agents must implement:
    - analyze() method that processes state and returns updated state
    - agent_id property for identification
    """

    def __init__(self, memory_layer=None):
        """
        Initialize base agent

        Args:
            memory_layer: MemoryLayer instance for accessing all memory types
        """
        self.memory = memory_layer

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """
        Unique identifier for this agent
        此 Agent 的唯一標識符

        Returns:
            Agent ID string
        """
        pass

    @abstractmethod
    def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by subclasses
        主要分析方法 - 必須由子類實現

        Args:
            state: Current ComplianceState

        Returns:
            Updated ComplianceState
        """
        pass

    def _log_memory_access(
        self,
        state: Dict[str, Any],
        memory_type: str,
        query: str,
        results: list,
        similarity_scores: Optional[list] = None
    ) -> None:
        """
        Log memory access to state for traceability
        記錄記憶訪問到狀態以便追溯

        [PRODUCT HOOK POINT]
        This is where memory traces are recorded for visualization

        Args:
            state: Current state to update
            memory_type: Type of memory accessed (episodic/semantic/procedural)
            query: Query text used
            results: Retrieved results
            similarity_scores: Similarity scores if applicable
        """
        from datetime import datetime, timezone

        trace = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_type": memory_type,
            "agent_id": self.agent_id,
            "query": query,
            "result_count": len(results),
            "memory_ids": [
                r.get("sar_id") or r.get("regulation_id") or r.get("rule_id", "")
                for r in results
            ],
            "similarity_scores": similarity_scores or [],
            "metadata": {
                "query_length": len(query),
                "has_results": len(results) > 0
            }
        }

        state["memory_traces"].append(trace)
        logger.info(
            f"[{self.agent_id}] Memory access logged: {memory_type}, "
            f"{len(results)} results"
        )

    def _add_message(
        self,
        state: Dict[str, Any],
        content: str,
        role: str = "assistant"
    ) -> None:
        """
        Add a message to conversation history
        添加消息到對話歷史

        Args:
            state: Current state to update
            content: Message content
            role: Message role (default: "assistant")
        """
        message = {
            "role": role,
            "content": content,
            "agent_id": self.agent_id
        }
        state["messages"].append(message)

    def _calculate_risk_contribution(
        self,
        indicators: list,
        base_score: float = 0.0
    ) -> float:
        """
        Calculate risk score contribution from this agent
        計算此 Agent 的風險分數貢獻

        Args:
            indicators: List of risk indicators identified
            base_score: Base risk score

        Returns:
            Risk score (0.0 - 1.0)
        """
        # Simple heuristic: each indicator adds risk
        indicator_score = min(len(indicators) * 0.15, 0.6)
        total_score = min(base_score + indicator_score, 1.0)
        return round(total_score, 2)
