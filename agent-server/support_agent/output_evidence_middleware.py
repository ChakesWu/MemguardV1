"""LangChain hook that attaches only governed output evidence to final answers."""

from __future__ import annotations

import json
from typing import Any

from langchain.agents.middleware import after_model

from .output_evidence_report import govern_output_content
from .repository import SupportRepository


def _context_value(runtime: Any, name: str) -> str | None:
    context = getattr(runtime, "context", None)
    value = context.get(name) if isinstance(context, dict) else getattr(context, name, None)
    return str(value) if value else None


def _tool_memory_ids(messages: list[Any]) -> set[str]:
    ids: set[str] = set()
    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        try:
            payload = json.loads(message.content)
        except (TypeError, json.JSONDecodeError):
            continue
        for memory_id in payload.get("memguard_memory_ids", []):
            if isinstance(memory_id, str):
                ids.add(memory_id)
    return ids


def output_evidence_middleware(repository: SupportRepository):
    @after_model
    def attach_output_evidence(state: dict[str, Any], runtime: Any) -> dict[str, Any] | None:
        messages = state.get("messages", [])
        if not messages:
            return None
        message = messages[-1]
        content = getattr(message, "content", None)
        if not isinstance(content, str) or getattr(message, "tool_calls", None):
            return None
        tenant_id = _context_value(runtime, "tenant_id")
        if tenant_id is None:
            return None
        answer, report = govern_output_content(
            repository=repository,
            tenant_id=tenant_id,
            content=content,
            prompt_memory_ids=_tool_memory_ids(messages),
        )
        if answer == content and report is None:
            return None
        metadata = dict(getattr(message, "additional_kwargs", {}) or {})
        if report is not None:
            metadata["memguard_output_evidence"] = report
        return {"messages": [message.model_copy(update={"content": answer, "additional_kwargs": metadata})]}

    return attach_output_evidence
