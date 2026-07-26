"""
MemGuard LLM Configuration — Multi-Provider Support.

Usage:
    from memguard.config import LLMConfig, create_llm_client

    # Auto-detect from environment variables
    client, model = create_llm_client()

    # Or configure manually
    config = LLMConfig(
        provider="anthropic",
        model="claude-sonnet-4-6",
        api_key="sk-ant-xxx"
    )
    client, model = create_llm_client(config)

Supported Providers:
    openai             — OpenAI API (GPT-4o, GPT-4o-mini, etc.)
    anthropic          — Anthropic API (Claude Opus, Sonnet, Haiku)
    ollama             — Local Ollama (Qwen, Llama, Mistral, etc.)
    openai_compatible  — Any OpenAI-compatible API (Together, Groq, vLLM, etc.)

Environment Variables (highest priority):
    MEMGUARD_LLM_PROVIDER     — Provider name (default: openai)
    MEMGUARD_LLM_MODEL        — Model name (default: gpt-4o-mini)
    MEMGUARD_LLM_API_KEY      — API Key (falls back to provider-specific variable if not set)
    MEMGUARD_LLM_BASE_URL     — Custom API URL (used by openai_compatible / ollama)
    MEMGUARD_LLM_TEMPERATURE  — Temperature parameter (default: 0.7)
    MEMGUARD_LLM_MAX_TOKENS   — Maximum output tokens (default: 100)

Provider-Specific API Key Environment Variables (fallback):
    OPENAI_API_KEY            — openai / openai_compatible
    ANTHROPIC_API_KEY         — anthropic
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional, Tuple


# ── Type alias ────────────────────────────────────────────────

Provider = Literal["openai", "anthropic", "ollama", "openai_compatible"]


# ── Defaults ──────────────────────────────────────────────────

DEFAULT_MODELS: dict[Provider, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-6",
    "ollama": "qwen2.5:7b",
    "openai_compatible": "gpt-4o-mini",
}

# Provider-specific API key environment variable names
PROVIDER_API_KEY_ENV: dict[Provider, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": "",  # Ollama does not require an API key
    "openai_compatible": "OPENAI_API_KEY",
}


# ── Config dataclass ──────────────────────────────────────────

@dataclass
class LLMConfig:
    """
    LLM configuration.

    Priority: passed arguments > environment variables > .env file > defaults

    Examples:
        # Auto-detect from environment variables
        config = LLMConfig.from_env()

        # Manual configuration
        config = LLMConfig(
            provider="anthropic",
            model="claude-opus-4-8",
            api_key="sk-ant-xxx",
            temperature=0.3,
            max_tokens=200,
        )

        # Use local Ollama
        config = LLMConfig(
            provider="ollama",
            model="qwen2.5:14b",
            base_url="http://localhost:11434/v1",
        )
    """
    provider: Provider = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 100

    # Advanced options
    extra_kwargs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, **overrides: Any) -> "LLMConfig":
        """
        Create LLMConfig from environment variables.

        Tries to read the .env file first (if it exists),
        then reads environment variables.
        Finally applies overrides (highest priority).

        Args:
            **overrides: Manual override parameters, highest priority
        """
        # Try loading the .env file
        _load_dotenv()

        # Read environment variables
        provider = os.getenv("MEMGUARD_LLM_PROVIDER", "openai").lower()
        if provider not in ("openai", "anthropic", "ollama", "openai_compatible"):
            print(f"WARNING: Unknown provider '{provider}', falling back to 'openai'")
            provider = "openai"

        provider = provider  # type: ignore[assignment]

        model = os.getenv("MEMGUARD_LLM_MODEL") or DEFAULT_MODELS.get(provider, "gpt-4o-mini")

        # API key: try the generic one first, then the provider-specific one
        api_key = os.getenv("MEMGUARD_LLM_API_KEY", "")
        if not api_key:
            provider_env = PROVIDER_API_KEY_ENV.get(provider, "")
            if provider_env:
                api_key = os.getenv(provider_env, "")

        base_url = os.getenv("MEMGUARD_LLM_BASE_URL", "")

        temperature = float(os.getenv("MEMGUARD_LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("MEMGUARD_LLM_MAX_TOKENS", "100"))

        config = cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def validate(self) -> list[str]:
        """Validate the configuration, returning a list of errors."""
        errors: list[str] = []

        if self.provider not in ("openai", "anthropic", "ollama", "openai_compatible"):
            errors.append(f"Unknown provider: {self.provider}")

        if self.provider != "ollama" and not self.api_key:
            env_name = PROVIDER_API_KEY_ENV.get(self.provider, "API_KEY")
            errors.append(
                f"API key is required for provider '{self.provider}'. "
                f"Set MEMGUARD_LLM_API_KEY or {env_name}"
            )

        if self.temperature < 0 or self.temperature > 2:
            errors.append(f"Temperature must be between 0 and 2, got {self.temperature}")

        if self.max_tokens < 1:
            errors.append(f"max_tokens must be >= 1, got {self.max_tokens}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert the configuration to a dict (API key hidden)."""
        d = {
            "provider": self.provider,
            "model": self.model,
            "api_key": "***" if self.api_key else "(not set)",
            "base_url": self.base_url or "(default)",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        return d

    def display(self) -> None:
        """Display the current configuration in the terminal."""
        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title="🔧 LLM Configuration", show_header=False)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="white")
            for key, value in self.to_dict().items():
                table.add_row(key, str(value))
            console.print(table)
        except ImportError:
            print("\n🔧 LLM Configuration:")
            for key, value in self.to_dict().items():
                print(f"  {key}: {value}")
            print()


# ── Client factory ────────────────────────────────────────────

def create_llm_client(
    config: Optional[LLMConfig] = None,
    **overrides: Any,
) -> Tuple[Any, str]:
    """
    Create an LLM client, returning (client, model_name).

    Args:
        config: LLMConfig, reads from environment variables if None
        **overrides: Override specific parameters in the config

    Returns:
        (client, model_name)

    Examples:
        # Auto-detect configuration
        client, model = create_llm_client()

        # Use Anthropic
        client, model = create_llm_client(provider="anthropic", model="claude-sonnet-4-6")

        # Use local Ollama
        client, model = create_llm_client(provider="ollama", model="qwen2.5:7b")

        # Use a custom endpoint
        client, model = create_llm_client(
            provider="openai_compatible",
            model="mistral-large",
            base_url="https://api.mistral.ai/v1",
            api_key="...",
        )
    """
    if config is None:
        config = LLMConfig.from_env()

    # Apply overrides
    if overrides:
        config = LLMConfig.from_env(**overrides)

    # Validate
    errors = config.validate()
    if errors:
        raise ValueError("LLM configuration errors:\n  " + "\n  ".join(errors))

    if config.provider == "openai":
        return _create_openai_client(config)

    elif config.provider == "anthropic":
        return _create_anthropic_client(config)

    elif config.provider == "ollama":
        return _create_openai_compatible_client(config)

    elif config.provider == "openai_compatible":
        return _create_openai_compatible_client(config)

    else:
        raise ValueError(f"Unsupported provider: {config.provider}")


def _create_openai_client(config: LLMConfig) -> Tuple[Any, str]:
    """Create an OpenAI client."""
    from openai import OpenAI

    client = OpenAI(api_key=config.api_key)
    return client, config.model


def _create_anthropic_client(config: LLMConfig) -> Tuple[Any, str]:
    """Create an Anthropic client."""
    from anthropic import Anthropic

    client = Anthropic(api_key=config.api_key)
    return client, config.model


def _create_openai_compatible_client(config: LLMConfig) -> Tuple[Any, str]:
    """Create an OpenAI-compatible client (Ollama, Together, Groq, etc.)."""
    from openai import OpenAI

    if not config.api_key and config.provider != "ollama":
        # Some compatible APIs don't require a key, use placeholder
        pass

    kwargs = {}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    if config.api_key:
        kwargs["api_key"] = config.api_key
    else:
        kwargs["api_key"] = "ollama"  # Ollama doesn't need a real key

    client = OpenAI(**kwargs)
    return client, config.model


# ── LLM call wrapper (cross-provider) ─────────────────────────

def llm_chat(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    config: Optional[LLMConfig] = None,
    **kwargs: Any,
) -> str:
    """
    Unified LLM call interface, supporting all providers.

    Args:
        client: LLM client
        model: Model name
        messages: Message list
        config: LLMConfig (used for temperature/max_tokens)
        **kwargs: Additional parameters

    Returns:
        LLM response text
    """
    cfg = config or LLMConfig.from_env()

    if cfg.provider == "anthropic":
        # Anthropic API has a different format
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)

        response = client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", cfg.max_tokens),
            system=system_msg if system_msg else None,  # type: ignore[arg-type]
            messages=user_msgs,
            temperature=kwargs.get("temperature", cfg.temperature),
        )
        return response.content[0].text

    else:
        # OpenAI / Ollama / compatible — unified chat.completions API
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", cfg.max_tokens),
            temperature=kwargs.get("temperature", cfg.temperature),
        )
        return response.choices[0].message.content


# ── .env loader ───────────────────────────────────────────────

def _load_dotenv() -> None:
    """Try loading the .env file (if it exists). No python-dotenv dependency needed."""
    env_file = Path.cwd() / ".env"
    if not env_file.exists():
        return

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only load if the environment variable is not already set (env vars have higher priority)
                if key and not os.getenv(key):
                    os.environ[key] = value
    except Exception:
        pass  # .env load failure does not affect the main flow


# ── Quick check ───────────────────────────────────────────────

def check_config() -> LLMConfig:
    """
    Quick configuration check and display. Used at the start of demo scripts.

    Skips display if the environment variable `MEMGUARD_LLM_SKIP_CHECK=1` is set.
    """
    config = LLMConfig.from_env()

    if os.getenv("MEMGUARD_LLM_SKIP_CHECK"):
        return config

    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()

        provider_icons = {
            "openai": "🤖",
            "anthropic": "🧠",
            "ollama": "🏠",
            "openai_compatible": "🔌",
        }
        icon = provider_icons.get(config.provider, "🤖")

        console.print(Panel.fit(
            f"{icon}  Provider: [bold cyan]{config.provider}[/bold cyan]  |  "
            f"Model: [bold green]{config.model}[/bold green]\n"
            f"[dim]Usage: export MEMGUARD_LLM_PROVIDER=xxx  or  edit the .env file[/dim]",
            border_style="blue"
        ))
    except ImportError:
        print(f"🔧 LLM: {config.provider} / {config.model}")

    return config
