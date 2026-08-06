"""Explicit output-citation protocol for the customer-support agent."""

from __future__ import annotations

import json
from dataclasses import dataclass


_OPEN = "<memguard-evidence>"
_CLOSE = "</memguard-evidence>"
_ROLES = {"factual_support", "constraint", "preference", "background_context"}


@dataclass(frozen=True)
class ExplicitCitation:
    start_offset: int
    end_offset: int
    segment: str
    memory_id: str
    evidence_quote: str
    role: str


def extract_explicit_citations(content: str) -> tuple[str, tuple[ExplicitCitation, ...]]:
    """Remove the private protocol block and return only unambiguous citations."""
    start = content.rfind(_OPEN)
    end = content.rfind(_CLOSE)
    if start < 0 or end < start:
        return content, ()
    answer = content[:start].rstrip()
    if end + len(_CLOSE) != len(content):
        return answer, ()
    try:
        payload = json.loads(content[start + len(_OPEN) : end])
    except json.JSONDecodeError:
        return answer, ()
    raw_citations = payload.get("citations") if isinstance(payload, dict) else None
    if not isinstance(raw_citations, list):
        return answer, ()

    citations: list[ExplicitCitation] = []
    for raw in raw_citations:
        if not isinstance(raw, dict):
            return answer, ()
        segment = raw.get("segment")
        memory_id = raw.get("memory_id")
        quote = raw.get("evidence_quote")
        role = raw.get("role")
        if not all(isinstance(value, str) and value for value in (segment, memory_id, quote, role)) or role not in _ROLES:
            return answer, ()
        offset = answer.find(segment)
        if offset < 0 or answer.find(segment, offset + len(segment)) >= 0:
            return answer, ()
        citations.append(ExplicitCitation(offset, offset + len(segment), segment, memory_id, quote, role))
    return answer, tuple(citations)
