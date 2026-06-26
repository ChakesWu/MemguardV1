"""
LangGraph Adapter — wraps BaseCheckpointSaver for memory observability.

LangGraph agents use a Checkpointer for state persistence. MemGuard wraps
any checkpointer to intercept all memory operations transparently.

Usage — ZERO changes to your agent code, just swap the checkpointer:

    # === Before MemGuard ===
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)

    # === After MemGuard (add 3 lines) ===
    from langgraph.checkpoint.memory import MemorySaver
    from memguard.adapters.langgraph import MemGuardCheckpointer

    checkpointer = MemGuardCheckpointer(
        inner=MemorySaver(),
        agent_id="my-agent",
        namespace="my-org",
        transport=StdoutTransport()  # or HttpTransport(...)
    )
    graph = workflow.compile(checkpointer=checkpointer)
    # === Everything else is identical ===
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Iterator, Optional, Sequence, Union

from ..core.interceptor import MemGuardInterceptor, Transport
from ..core.event import MemoryOp, MemoryType

logger = logging.getLogger("memguard.adapter.langgraph")


class MemGuardCheckpointer:
    """
    Wraps any LangGraph BaseCheckpointSaver with memory observability.

    Intercepts:
        - put() / aput()    → CREATE or UPDATE memory events
        - get_tuple()       → READ memory events
        - list() / alist()  → QUERY memory events

    Features:
        - Transparent: inner checkpointer behavior is unchanged
        - Non-blocking: events are emitted async, never blocking
        - Privacy-first: state is hashed by default, not stored raw
        - Zero agent changes: just swap the checkpointer
    """

    def __init__(
        self,
        inner: Any,  # BaseCheckpointSaver — we duck-type to avoid import requirement
        agent_id: str = "langgraph-agent",
        namespace: str = "default",
        transport: Transport | None = None,
        capture_content: bool = False,
    ):
        """
        Args:
            inner: Any LangGraph BaseCheckpointSaver (MemorySaver, SqliteSaver, etc.)
            agent_id: Identifier for this agent
            namespace: Tenant/org namespace (maps to tenant_id)
            transport: Where to send events (HttpTransport, FileTransport, StdoutTransport)
            capture_content: If True, store full state content. Privacy-first: default False.
        """
        self.inner = inner
        self.interceptor = MemGuardInterceptor(
            agent_id=agent_id,
            transport=transport,
            namespace=namespace,
            capture_content=capture_content,
        )
        self._thread_id_to_session: dict[str, str] = {}

    # ── Synchronous API (LangGraph calls these) ──────────────

    def get_tuple(self, config: dict) -> Any | None:
        """
        Intercepted READ: retrieve checkpoint state.

        LangGraph calls this before every node execution to restore state.
        We record what state was retrieved.
        """
        result = self.inner.get_tuple(config)

        thread_id = self._extract_thread_id(config)
        if thread_id and result:
            self.interceptor.set_session(thread_id)
            self.interceptor.record(
                operation=MemoryOp.READ,
                memory_key=f"checkpoint:{thread_id}",
                after_value=self._serialize_checkpoint(result) if self.interceptor.capture_content else None,
                memory_type=MemoryType.WORKING,
                config_thread_id=thread_id,
            )

        return result

    def put(
        self,
        config: dict,
        checkpoint: Any,
        metadata: dict | None = None,
        new_versions: dict | None = None,
    ) -> dict:
        """
        Intercepted CREATE/UPDATE: persist checkpoint state.

        LangGraph calls this after every node execution to save state.
        We record what changed.
        """
        # Determine if this is CREATE or UPDATE
        existing = None
        try:
            existing = self.inner.get_tuple(config)
        except Exception:
            pass

        operation = MemoryOp.UPDATE if existing else MemoryOp.CREATE

        # Delegate to the real checkpointer
        result = self.inner.put(config, checkpoint, metadata, new_versions)

        # Record the event
        thread_id = self._extract_thread_id(config)
        if thread_id:
            self.interceptor.set_session(thread_id)
            self.interceptor.record(
                operation=operation,
                memory_key=f"checkpoint:{thread_id}",
                before_value=self._serialize_checkpoint(existing) if existing and self.interceptor.capture_content else None,
                after_value=self._serialize_checkpoint(checkpoint) if self.interceptor.capture_content else None,
                memory_type=MemoryType.WORKING,
                config_thread_id=thread_id,
                metadata=metadata or {},
            )

        return result

    def put_writes(
        self,
        config: dict,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Intercepted: store pending writes (subgraph communication)."""
        if hasattr(self.inner, 'put_writes'):
            self.inner.put_writes(config, writes, task_id)

            thread_id = self._extract_thread_id(config)
            if thread_id:
                self.interceptor.record(
                    operation=MemoryOp.UPDATE,
                    memory_key=f"writes:{thread_id}:{task_id}",
                    memory_type=MemoryType.WORKING,
                    config_thread_id=thread_id,
                    task_id=task_id,
                    write_count=len(writes),
                )

    def list(
        self,
        config: dict | None,
        *,
        filter: dict | None = None,
        before: dict | None = None,
        limit: int | None = None,
    ) -> Iterator[Any]:
        """Intercepted QUERY: list checkpoints."""
        result = self.inner.list(config, filter=filter, before=before, limit=limit)

        thread_id = self._extract_thread_id(config) if config else None
        if thread_id:
            self.interceptor.record(
                operation=MemoryOp.QUERY,
                memory_key=f"list:{thread_id}",
                memory_type=MemoryType.WORKING,
                config_thread_id=thread_id,
            )

        return result

    # ── Async API (for async LangGraph) ──────────────────────

    async def aget_tuple(self, config: dict) -> Any | None:
        """Async version of get_tuple."""
        if hasattr(self.inner, 'aget_tuple'):
            result = await self.inner.aget_tuple(config)
        else:
            result = self.inner.get_tuple(config)

        thread_id = self._extract_thread_id(config)
        if thread_id and result:
            self.interceptor.set_session(thread_id)
            self.interceptor.record(
                operation=MemoryOp.READ,
                memory_key=f"checkpoint:{thread_id}",
                after_value=self._serialize_checkpoint(result) if self.interceptor.capture_content else None,
                memory_type=MemoryType.WORKING,
                config_thread_id=thread_id,
            )

        return result

    async def aput(
        self,
        config: dict,
        checkpoint: Any,
        metadata: dict | None = None,
        new_versions: dict | None = None,
    ) -> dict:
        """Async version of put."""
        existing = None
        try:
            if hasattr(self.inner, 'aget_tuple'):
                existing = await self.inner.aget_tuple(config)
            else:
                existing = self.inner.get_tuple(config)
        except Exception:
            pass

        operation = MemoryOp.UPDATE if existing else MemoryOp.CREATE

        if hasattr(self.inner, 'aput'):
            result = await self.inner.aput(config, checkpoint, metadata, new_versions)
        else:
            result = self.inner.put(config, checkpoint, metadata, new_versions)

        thread_id = self._extract_thread_id(config)
        if thread_id:
            self.interceptor.set_session(thread_id)
            self.interceptor.record(
                operation=operation,
                memory_key=f"checkpoint:{thread_id}",
                before_value=self._serialize_checkpoint(existing) if existing and self.interceptor.capture_content else None,
                after_value=self._serialize_checkpoint(checkpoint) if self.interceptor.capture_content else None,
                memory_type=MemoryType.WORKING,
                config_thread_id=thread_id,
                metadata=metadata or {},
            )

        return result

    async def aput_writes(
        self,
        config: dict,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async version of put_writes."""
        if hasattr(self.inner, 'aput_writes'):
            await self.inner.aput_writes(config, writes, task_id)
        elif hasattr(self.inner, 'put_writes'):
            self.inner.put_writes(config, writes, task_id)

    async def alist(
        self,
        config: dict | None,
        *,
        filter: dict | None = None,
        before: dict | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[Any]:
        """Async version of list."""
        if hasattr(self.inner, 'alist'):
            async for item in self.inner.alist(config, filter=filter, before=before, limit=limit):
                yield item
        else:
            if hasattr(self.inner, 'list'):
                for item in self.inner.list(config, filter=filter, before=before, limit=limit):
                    yield item

    # ── Helpers ──────────────────────────────────────────────

    def _extract_thread_id(self, config: dict) -> str | None:
        """Extract thread_id from LangGraph config."""
        if not config:
            return None
        configurable = config.get("configurable", {})
        return configurable.get("thread_id")

    def _serialize_checkpoint(self, checkpoint: Any) -> dict | None:
        """Safely serialize a LangGraph checkpoint to a dict."""
        if checkpoint is None:
            return None
        try:
            if hasattr(checkpoint, '__dict__'):
                # Take a shallow copy of public attrs
                return {
                    k: str(v)[:200]  # Truncate long values
                    for k, v in checkpoint.__dict__.items()
                    if not k.startswith('_')
                }
            return {"value": str(checkpoint)[:500]}
        except Exception:
            return {"raw": str(type(checkpoint))}

    # ── Passthrough for any other methods ────────────────────

    def __getattr__(self, name: str):
        """Pass through any unimplemented methods to the inner checkpointer."""
        return getattr(self.inner, name)
