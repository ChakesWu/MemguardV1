"""
Base Interceptor — the core of the MemGuard SDK.

Wraps any memory backend and records every memory operation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from .event import DecisionTrace, MemoryEvent, MemoryOp, MemoryType, hash_content

logger = logging.getLogger("memguard")


class MemGuardInterceptor:
    """
    Wraps a memory backend and records every memory operation.

    Usage:
        interceptor = MemGuardInterceptor(
            agent_id="my-agent",
            transport=HttpTransport("http://localhost:8000"),
            namespace="my-org"
        )

        # Record a memory write
        interceptor.record(
            operation=MemoryOp.CREATE,
            memory_key="user_prefs",
            after_value={"language": "Python"}
        )
    """

    def __init__(
        self,
        agent_id: str,
        transport: "Transport | None" = None,
        namespace: str = "default",
        capture_content: bool = False,  # Privacy-first: hash only by default
    ):
        self.agent_id = agent_id
        self.transport = transport
        self.namespace = namespace
        self.capture_content = capture_content
        self._session_id: str | None = None
        self._current_llm_call_id: str | None = None

    def set_session(self, session_id: str) -> None:
        """Set the current session ID. All subsequent events inherit this."""
        self._session_id = session_id

    def set_llm_call(self, llm_call_id: str) -> None:
        """Set the current LLM call ID for causality linking."""
        self._current_llm_call_id = llm_call_id

    def clear_llm_call(self) -> None:
        self._current_llm_call_id = None

    @staticmethod
    def _hash_content(value: dict[str, Any] | None) -> str:
        return hash_content(value)

    def record(
        self,
        operation: MemoryOp,
        memory_key: str,
        before_value: dict | None = None,
        after_value: dict | None = None,
        memory_type: MemoryType = MemoryType.WORKING,
        caused_by: str | None = None,
        tags: list[str] | None = None,
        agent_id: str | None = None,
        **context: Any,
    ) -> str:
        """
        Record a memory operation event.

        Returns the event_id so callers can link events together.

        Args:
            operation: What kind of memory operation (CREATE, READ, UPDATE, etc.)
            memory_key: Logical identifier for this memory
            before_value: State before the operation (for UPDATE/DELETE)
            after_value: State after the operation (for CREATE/UPDATE)
            memory_type: Cognitive type (EPISODIC, SEMANTIC, PROCEDURAL, WORKING)
            caused_by: event_id of an upstream event (for lineage)
            tags: Developer-defined labels
            agent_id: Override the interceptor's agent_id for this event
            **context: Framework-specific metadata

        Returns:
            event_id: UUID of the recorded event
        """
        value_to_hash = after_value if after_value is not None else before_value
        content_hash = self._hash_content(value_to_hash)

        event = MemoryEvent(
            agent_id=agent_id or self.agent_id,
            session_id=self._session_id or "unknown",
            operation=operation,
            memory_key=memory_key,
            namespace=self.namespace,
            memory_type=memory_type,
            before_value=before_value if self.capture_content else None,
            after_value=after_value if self.capture_content else None,
            content_hash=content_hash,
            caused_by=caused_by,
            llm_call_id=self._current_llm_call_id,
            tags=tags or [],
            context=context,
        )

        # Fire-and-forget: never block the calling agent
        if self.transport:
            self._emit_async(event)

        logger.debug(
            "MemGuard event: op=%s key=%s agent=%s session=%s",
            operation.value,
            memory_key,
            self.agent_id,
            self._session_id,
        )

        return event.event_id

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
        """Record one memory selected by the application for generation."""
        if retrieval_rank is not None and retrieval_rank < 1:
            raise ValueError("retrieval_rank must be at least 1")
        if retrieval_score is not None and not 0.0 <= retrieval_score <= 1.0:
            raise ValueError("retrieval_score must be between 0.0 and 1.0")
        if max_age_seconds is not None and max_age_seconds < 0:
            raise ValueError("max_age_seconds must not be negative")

        return self.record(
            operation=MemoryOp.READ,
            memory_key=memory_key,
            after_value=value,
            memory_type=memory_type,
            evidence_role="retrieved_memory",
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
        """Record an output and the evidence available when it was generated."""
        return self.trace_decision(
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids or [],
            prompt_text=user_input,
            output_text=output_text,
            user_input=user_input,
            model=model,
            current_facts=current_facts or {},
            evidence_model="recorded_lineage",
            causality_claim="not_proven",
        )

    def _emit_async(self, event: MemoryEvent) -> None:
        """Emit event via transport in a background thread. Never blocks, never raises."""
        if not self.transport:
            return

        import threading

        def _send() -> None:
            try:
                # Call transport.emit synchronously from the thread
                if hasattr(self.transport, "_emit_sync"):
                    self.transport._emit_sync(event)
                else:
                    import asyncio

                    try:
                        asyncio.run(self.transport.emit(event))
                    except RuntimeError:
                        # Already a running event loop — create task instead
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.transport.emit(event))
            except Exception:
                logger.warning(
                    "MemGuard: failed to emit event %s to transport",
                    getattr(event, "event_id", "?"),
                    exc_info=True,
                )

        t = threading.Thread(target=_send, daemon=True)
        t.start()

    def trace_decision(
        self,
        input_event_ids: list[str],
        output_event_ids: list[str],
        prompt_text: str = "",
        output_text: str = "",
        influence_score: float = 0.0,
        agent_id: str | None = None,
        user_input: str = "",
        model: str = "",
        **context: Any,
    ) -> DecisionTrace:
        """
        Create a decision trace linking memory reads to LLM output.

        Args:
            input_event_ids: event_ids of READ operations before the LLM call
            output_event_ids: event_ids of CREATE/UPDATE operations after
            prompt_text: The full prompt sent to the LLM
            output_text: The LLM's response
            influence_score: 0-1 metric of how much memory shaped this decision
            agent_id: Override the interceptor's agent_id for this trace
            **context: Additional metadata

        Returns:
            DecisionTrace object
        """
        import hashlib

        trace = DecisionTrace(
            agent_id=agent_id or self.agent_id,
            session_id=self._session_id or "unknown",
            namespace=self.namespace,
            input_event_ids=input_event_ids,
            output_event_ids=output_event_ids,
            prompt_hash=(
                hashlib.sha256(prompt_text.encode()).hexdigest()[:16]
                if prompt_text
                else ""
            ),
            user_input=user_input,
            model=model,
            output_hash=(
                hashlib.sha256(output_text.encode()).hexdigest()[:16]
                if output_text
                else ""
            ),
            output_summary=output_text[:200] if output_text else "",
            memory_influence_score=influence_score,
            context=context,
        )

        if self.transport:
            self._emit_async(trace)  # type: ignore[arg-type]

        return trace


class Transport:
    """
    Abstract transport for delivering MemGuard events to the control plane.

    Implementations:
        HttpTransport  — POST events to MemGuard server
        FileTransport  — Append to JSONL file (offline/development)
        StdoutTransport — Print to stdout (debugging)
    """

    async def emit(self, event) -> None:
        raise NotImplementedError
