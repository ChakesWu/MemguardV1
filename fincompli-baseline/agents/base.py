"""
Base Agent Class
基礎 Agent 類

Provides common functionality for all compliance agents.
為所有合規 Agent 提供通用功能。

[Business Purpose] Standardizes agent interface and memory access patterns
[業務目的] 標準化 Agent 接口和記憶訪問模式

[OBSERVABILITY] When an interceptor (MemGuardInterceptor) is provided,
every memory access is emitted as a MemGuard MemoryEvent so the dashboard
can show the complete memory-to-output chain.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Optional memguard import — base.py works without memguard installed
try:
    from memguard.core.event import MemoryOp, MemoryType
    HAS_MEMGUARD = True
except ImportError:
    HAS_MEMGUARD = False
    # Define stub enums so type hints don't break
    class MemoryOp:  # type: ignore[no-redef]
        CREATE = "create"
        READ = "read"
        UPDATE = "update"
        DELETE = "delete"
        QUERY = "query"
        SEARCH = "search"

    class MemoryType:  # type: ignore[no-redef]
        EPISODIC = "episodic"
        SEMANTIC = "semantic"
        PROCEDURAL = "procedural"
        WORKING = "working"


# Map our memory_type strings → MemGuard MemoryType
_MEMORY_TYPE_MAP = {
    "episodic": MemoryType.EPISODIC,
    "semantic": MemoryType.SEMANTIC,
    "procedural": MemoryType.PROCEDURAL,
    "working": MemoryType.WORKING,
}


class BaseAgent(ABC):
    """
    Base class for all compliance agents
    所有合規 Agent 的基類

    All agents must implement:
    - analyze() method that processes state and returns updated state
    - agent_id property for identification
    """

    def __init__(self, memory_layer=None, interceptor=None, llm_client=None):
        """
        Initialize base agent.

        Args:
            memory_layer: MemoryLayer instance for accessing all memory types
            interceptor: Optional MemGuardInterceptor for observability
            llm_client: Optional LLMClient for Qwen-powered reasoning
        """
        self.memory = memory_layer
        self.interceptor = interceptor
        self.llm = llm_client

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
        similarity_scores: Optional[list] = None,
    ) -> List[str]:
        """
        Log memory access to state for traceability AND emit memguard events.

        [OBSERVABILITY HOOK]
        When self.interceptor is set, each retrieval result is emitted as a
        READ MemoryEvent. The returned event_ids can be used to build
        DecisionTraces linking these memory reads to agent outputs.

        Args:
            state: Current state to update
            memory_type: Type of memory accessed (episodic/semantic/procedural)
            query: Query text used
            results: Retrieved results
            similarity_scores: Similarity scores if applicable

        Returns:
            List of event_ids (empty if no interceptor or no results)
        """
        from datetime import datetime, timezone

        # ── Existing state trace (backward compatible) ──
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
                "has_results": len(results) > 0,
            },
        }

        state["memory_traces"].append(trace)
        logger.info(
            f"[{self.agent_id}] Memory access logged: {memory_type}, "
            f"{len(results)} results"
        )

        # ── MemGuard observability events ──
        event_ids: List[str] = []
        if self.interceptor:
            mg_type = _MEMORY_TYPE_MAP.get(memory_type, MemoryType.WORKING)

            for i, result in enumerate(results):
                memory_id = (
                    result.get("sar_id")
                    or result.get("regulation_id")
                    or result.get("rule_id")
                    or f"{memory_type}-{i}"
                )
                sim = (
                    similarity_scores[i]
                    if similarity_scores and i < len(similarity_scores)
                    else None
                )

                try:
                    event_id = self.interceptor.record(
                        operation=MemoryOp.READ,
                        memory_key=f"{memory_type}:{memory_id}",
                        memory_type=mg_type,
                        agent_id=self.agent_id,
                        tags=[memory_type, self.agent_id],
                        query=query,
                        similarity=sim,
                        result_index=i,
                    )
                    event_ids.append(event_id)
                except Exception:
                    logger.debug(
                        "Failed to emit memguard event for %s", memory_id,
                        exc_info=True,
                    )

        return event_ids

    def _emit_decision_trace(
        self,
        input_event_ids: List[str],
        output_event_ids: List[str],
        prompt_text: str = "",
        output_text: str = "",
        influence_score: float = 0.0,
        **context: Any,
    ) -> None:
        """
        Create a DecisionTrace linking memory reads → agent output.

        [OBSERVABILITY] This is HOW the dashboard answers:
        "Which memory led to this agent's decision?"

        Args:
            input_event_ids: event_ids from _log_memory_access (READ events)
            output_event_ids: event_ids from output recordings (CREATE events)
            prompt_text: The full prompt sent to the LLM
            output_text: The agent's output / decision text
            influence_score: 0-1 metric of how much memory shaped this decision
            **context: Additional metadata for the trace
        """
        if not self.interceptor:
            return

        try:
            self.interceptor.trace_decision(
                input_event_ids=input_event_ids,
                output_event_ids=output_event_ids,
                prompt_text=prompt_text,
                output_text=output_text,
                influence_score=influence_score,
                agent_id=self.agent_id,
                **context,
            )
            logger.debug(
                "[%s] DecisionTrace: %d reads → %d writes (influence=%.2f)",
                self.agent_id,
                len(input_event_ids),
                len(output_event_ids),
                influence_score,
            )
        except Exception:
            logger.debug(
                "[%s] Failed to emit DecisionTrace", self.agent_id, exc_info=True
            )

    def _record_output_event(
        self,
        memory_key: str,
        after_value: Optional[dict] = None,
        tags: Optional[list] = None,
    ) -> str:
        """
        Record an agent output as a CREATE event.

        Returns:
            event_id (empty string if no interceptor)
        """
        if not self.interceptor:
            return ""

        try:
            return self.interceptor.record(
                operation=MemoryOp.CREATE,
                memory_key=memory_key,
                memory_type=MemoryType.WORKING,
                agent_id=self.agent_id,
                after_value=after_value if self.interceptor.capture_content else None,
                tags=tags or [self.agent_id, "output"],
            )
        except Exception:
            logger.debug(
                "[%s] Failed to record output event", self.agent_id, exc_info=True
            )
            return ""

    def _add_message(
        self,
        state: Dict[str, Any],
        content: str,
        role: str = "assistant",
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
            "agent_id": self.agent_id,
        }
        state["messages"].append(message)

    def _calculate_risk_contribution(
        self,
        indicators: list,
        base_score: float = 0.0,
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
