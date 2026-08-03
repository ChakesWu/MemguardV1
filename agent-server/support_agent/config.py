"""Server-only configuration for the customer-support agent."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SupportAgentSettings:
    database_url: str
    deepseek_api_key: str
    deepseek_model: str
    langsmith_tracing: bool
    langsmith_api_key: str | None
    langsmith_project: str

    @classmethod
    def from_env(cls) -> "SupportAgentSettings":
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise ValueError("DATABASE_URL is required")

        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")

        langsmith_tracing = _env_flag("LANGSMITH_TRACING")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "").strip() or None
        if langsmith_tracing and not langsmith_api_key:
            raise ValueError("LANGSMITH_API_KEY is required when LANGSMITH_TRACING=true")

        return cls(
            database_url=database_url,
            deepseek_api_key=deepseek_api_key,
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
            langsmith_tracing=langsmith_tracing,
            langsmith_api_key=langsmith_api_key,
            langsmith_project=os.getenv("LANGSMITH_PROJECT", "memguard-customer-support-baseline"),
        )
