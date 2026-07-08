"""
Core data models for MemGuard events.

MemoryEvent is the atomic unit of MemGuard.
Every memory operation (create/read/update/delete/search) produces one.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class MemoryOp(str, Enum):
    """Types of memory operations we intercept."""
    CREATE = "create"    # New memory written
    READ = "read"        # Memory retrieved by key
    UPDATE = "update"    # Existing memory modified
    DELETE = "delete"    # Memory removed
    QUERY = "query"      # Structured search
    SEARCH = "search"    # Semantic/vector search


class MemoryType(str, Enum):
    """Cognitive memory taxonomy."""
    EPISODIC = "episodic"      # Specific past events
    SEMANTIC = "semantic"      # General facts about user/world
    PROCEDURAL = "procedural"  # How to do things
    WORKING = "working"        # Short-term, in-context state


@dataclass
class MemoryEvent:
    """
    Atomic record of a single memory operation.

    This is the fundamental unit of MemGuard observability.
    Every time an agent reads or writes memory, one of these is produced.
    """
    # Identity
    event_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    session_id: str = ""

    # What happened
    operation: MemoryOp = MemoryOp.CREATE
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Memory target
    memory_key: str = ""           # Logical key / identifier
    namespace: str = "default"     # Scoping (tenant_id, user_id, etc.)
    memory_type: MemoryType = MemoryType.WORKING

    # Content (privacy-first: hashed by default)
    before_value: dict | None = None    # State before op (for UPDATE/DELETE)
    after_value: dict | None = None     # State after op (for CREATE/UPDATE)
    content_hash: str = ""              # SHA-256 of content

    # Causality
    caused_by: str | None = None        # event_id of upstream event
    llm_call_id: str | None = None      # Which LLM completion triggered this

    # Context
    context: dict = field(default_factory=dict)    # Framework-specific metadata
    tags: list[str] = field(default_factory=list)  # Developer-defined labels

    def __post_init__(self):
        if not self.content_hash and (self.after_value or self.before_value):
            value = self.after_value or self.before_value or {}
            self.content_hash = hashlib.sha256(
                str(sorted(value.items())).encode()
            ).hexdigest()[:16]


@dataclass
class DecisionTrace:
    """
    Links memory reads → LLM call → LLM output → memory writes.

    This is how you answer: "Why did the agent decide that?"
    Trace back from any agent output to the memories that shaped it.
    """
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    session_id: str = ""
    namespace: str = "default"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Input side: which memories were read
    input_event_ids: list[str] = field(default_factory=list)

    # The LLM call
    prompt_hash: str = ""
    output_hash: str = ""
    output_summary: str = ""

    # Output side: which memories were written
    output_event_ids: list[str] = field(default_factory=list)

    # Analysis
    memory_influence_score: float = 0.0  # 0-1: how much memory shaped this decision

    context: dict = field(default_factory=dict)
