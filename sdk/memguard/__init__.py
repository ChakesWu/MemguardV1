"""
MemGuard SDK - Memory Observability for AI Agents.

Usage:
    from memguard import MemGuardInterceptor
    from memguard.adapters.langgraph import MemGuardCheckpointer
    from memguard.config import LLMConfig, create_llm_client

MemGuard wraps your existing memory backend and records every
memory operation (read/write/update/delete) without requiring
changes to your agent code.
"""

from memguard.client import MemGuard
from memguard.core import (
    DecisionTrace,
    MemGuardInterceptor,
    MemoryEvent,
    MemoryOp,
    MemoryType,
)
from memguard.config import LLMConfig, create_llm_client, llm_chat, check_config

__version__ = "0.1.0"

__all__ = [
    "MemGuardInterceptor",
    "MemGuard",
    "MemoryEvent",
    "MemoryOp",
    "MemoryType",
    "DecisionTrace",
    # LLM config
    "LLMConfig",
    "create_llm_client",
    "llm_chat",
    "check_config",
]
