"""Intent-level public client for MemGuard memory evidence."""

from __future__ import annotations

from typing import Any, Optional

from .core.event import DecisionTrace, MemoryType
from .core.interceptor import MemGuardInterceptor
from .transport.http import HttpTransport


class MemGuard:
    """Record retrieved memories and outputs with a small public API."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        agent_id: str,
        namespace: str = "default",
        capture_content: bool = False,
    ) -> None:
        self._transport = HttpTransport(api_url, api_key=api_key)
        self._interceptor = MemGuardInterceptor(
            agent_id=agent_id,
            transport=self._transport,
            namespace=namespace,
            capture_content=capture_content,
        )

    def set_session(self, session_id: str) -> None:
        self._interceptor.set_session(session_id)

    def record_retrieval(
        self,
        memory_key: str,
        value: dict[str, Any],
        *,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        source_type: str,
        source_id: Optional[str] = None,
        memory_created_at: Optional[str] = None,
        memory_last_verified_at: Optional[str] = None,
        retrieval_query: str = "",
        retrieval_score: Optional[float] = None,
        retrieval_rank: Optional[int] = None,
        included_in_prompt: bool = True,
        fact_key: Optional[str] = None,
        max_age_seconds: Optional[int] = None,
    ) -> str:
        return self._interceptor.record_retrieval(
            memory_key,
            value,
            memory_type=memory_type,
            source_type=source_type,
            source_id=source_id,
            memory_created_at=memory_created_at,
            memory_last_verified_at=memory_last_verified_at,
            retrieval_query=retrieval_query,
            retrieval_score=retrieval_score,
            retrieval_rank=retrieval_rank,
            included_in_prompt=included_in_prompt,
            fact_key=fact_key,
            max_age_seconds=max_age_seconds,
        )

    def record_output(
        self,
        *,
        user_input: str,
        output_text: str,
        input_event_ids: list[str],
        output_event_ids: Optional[list[str]] = None,
        model: str = "",
        current_facts: Optional[dict[str, Any]] = None,
    ) -> DecisionTrace:
        return self._interceptor.record_output(
            user_input=user_input,
            output_text=output_text,
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids,
            model=model,
            current_facts=current_facts,
        )

    def flush(self, timeout: float = 5.0) -> bool:
        return self._transport.flush(timeout)
