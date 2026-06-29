"""
Short-term Memory Module
短期記憶模塊

Short-term memory is managed by LangGraph's built-in state checkpointing.
This module provides utilities for working with thread state.

短期記憶由 LangGraph 內建的狀態檢查點管理。
本模塊提供操作線程狀態的工具函數。

[Business Purpose] Maintains conversation context within current analysis session
[業務目的] 維護當前分析會話中的對話上下文
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class ShortTermMemory:
    """
    Short-term Memory Interface
    短期記憶接口

    Note: Actual storage is handled by LangGraph's State.
    This class provides convenience methods for state manipulation.

    注意：實際存儲由 LangGraph 的 State 處理。
    此類提供操作狀態的便利方法。
    """

    @staticmethod
    def format_memory_trace(
        memory_type: str,
        agent_id: str,
        query: str,
        results: List[Dict[str, Any]],
        similarity_scores: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Format a memory trace record for state storage
        格式化記憶追蹤記錄用於狀態存儲

        Args:
            memory_type: Type of memory accessed (episodic/semantic/procedural)
            agent_id: Agent that accessed the memory
            query: Query text used
            results: Retrieved results
            similarity_scores: Similarity scores if applicable

        Returns:
            Formatted memory trace dict
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_type": memory_type,
            "agent_id": agent_id,
            "query": query,
            "result_count": len(results),
            "memory_ids": [r.get("id") or r.get("memory_id") for r in results],
            "similarity_scores": similarity_scores or [],
            "metadata": {
                "query_length": len(query),
                "has_results": len(results) > 0
            }
        }

    @staticmethod
    def get_conversation_summary(messages: List[Dict[str, str]]) -> str:
        """
        Generate a brief summary of conversation history
        生成對話歷史的簡要摘要

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Summary string
        """
        if not messages:
            return "No conversation history"

        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        summary = f"Conversation: {len(user_messages)} user messages, {len(assistant_messages)} assistant messages"

        if user_messages:
            latest_user = user_messages[-1].get("content", "")[:100]
            summary += f". Latest user input: {latest_user}"

        return summary

    @staticmethod
    def extract_transaction_context(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract transaction-specific context from state
        從狀態中提取交易特定上下文

        Args:
            state: Current graph state

        Returns:
            Dict with transaction context
        """
        return {
            "transaction_id": state.get("transaction_id"),
            "customer_id": state.get("customer_id"),
            "amount": state.get("amount"),
            "risk_score": state.get("risk_score"),
            "analysis_stage": state.get("current_stage"),
            "memory_traces_count": len(state.get("memory_traces", []))
        }
