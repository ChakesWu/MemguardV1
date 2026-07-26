#!/usr/bin/env python3
"""
MemGuard Quick Demo — runs in ~30 seconds

Requirements:
  pip install -e sdk/
  pip install openai rich

Usage:
  # Default: uses OpenAI gpt-4o-mini
  export OPENAI_API_KEY=sk-xxx
  python demo_simple.py

  # Using Anthropic Claude
  export MEMGUARD_LLM_PROVIDER=anthropic
  export ANTHROPIC_API_KEY=sk-ant-xxx
  python demo_simple.py

  # Using local Ollama (Qwen / Llama)
  export MEMGUARD_LLM_PROVIDER=ollama
  export MEMGUARD_LLM_MODEL=qwen2.5:7b
  python demo_simple.py

  # Using custom OpenAI-compatible API (Together, Groq, vLLM...)
  export MEMGUARD_LLM_PROVIDER=openai_compatible
  export MEMGUARD_LLM_MODEL=mistralai/Mixtral-8x7B
  export MEMGUARD_LLM_API_KEY=your-key
  export MEMGUARD_LLM_BASE_URL=https://api.together.xyz/v1
  python demo_simple.py

This demo shows MemGuard tracking memory operations in a simple research assistant.
No backend required - all output goes to terminal.
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Ensure SDK can be imported (if not pip installed yet)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Import MemGuard
from memguard import (
    MemGuardInterceptor,
    MemoryOp,
    MemoryType,
    LLMConfig,
    create_llm_client,
    llm_chat,
    check_config,
)
from memguard.transport.null import NullTransport

console = Console()

# Global stats
stats = {
    "total_events": 0,
    "reads": 0,
    "writes": 0,
    "conflicts": 0,
    "traces": 0,
}


class SimpleMemoryStore:
    """In-memory key-value store with MemGuard instrumentation."""

    def __init__(self, interceptor: MemGuardInterceptor):
        self.data: Dict[str, Any] = {}
        self.interceptor = interceptor
        self.write_log: Dict[str, list] = {}

    def write(self, key: str, value: Any, memory_type: MemoryType = MemoryType.WORKING) -> None:
        before = self.data.get(key)

        if key in self.write_log and len(self.write_log[key]) > 0:
            last_write = self.write_log[key][-1]
            if time.time() - last_write["timestamp"] < 1.0:
                console.print(
                    f"[red bold]⚠️  CONFLICT[/red bold]  "
                    f"[yellow]{key}[/yellow]  "
                    f"[dim]2 writers within 1s[/dim]"
                )
                stats["conflicts"] += 1

        self.data[key] = value

        if key not in self.write_log:
            self.write_log[key] = []
        self.write_log[key].append({"value": value, "timestamp": time.time()})

        operation = MemoryOp.UPDATE if before is not None else MemoryOp.CREATE
        self.interceptor.record(
            operation=operation,
            memory_key=key,
            before_value={"value": before} if before else None,
            after_value={"value": value},
            memory_type=memory_type,
        )

        icon = "🟡" if operation == MemoryOp.UPDATE else "🟢"
        op_name = operation.value.upper()
        console.print(
            f"[bright_white][MemGuard] {icon} {op_name:<8}[/bright_white] "
            f"[cyan]{key:<30}[/cyan] "
            f"[dim]\"{str(value)[:50]}\"[/dim]"
        )

        stats["total_events"] += 1
        stats["writes"] += 1

    def read(self, key: str) -> Any:
        value = self.data.get(key)

        self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key=key,
            after_value={"value": value} if value else None,
            memory_type=MemoryType.WORKING,
        )

        console.print(
            f"[bright_white][MemGuard] 🔵 READ[/bright_white]    "
            f"[cyan]{key:<30}[/cyan] "
            f"[dim]→ \"{str(value)[:50] if value else '(not found)'}\"[/dim]"
        )

        stats["total_events"] += 1
        stats["reads"] += 1

        return value


class ResearchAssistant:
    """Simple research assistant that uses memory."""

    def __init__(self, memory: SimpleMemoryStore, llm_client, llm_model: str, llm_config: LLMConfig):
        self.memory = memory
        self.llm = llm_client
        self.model = llm_model
        self.config = llm_config

    def simulate_search(self, query: str) -> str:
        if "python" in query.lower():
            return "Python 3.12 released with improved error messages and performance optimizations."
        elif "javascript" in query.lower():
            return "JavaScript ES2024 features include new array methods and improved async handling."
        else:
            return f"Research findings for: {query}"

    def run(self, user_request: str) -> str:
        console.print(f"\n[bold blue]User:[/bold blue] {user_request}\n")

        language_pref = self.memory.read("user:language_preference")
        topic_pref = self.memory.read("user:topic_preference")

        search_query = f"{topic_pref or 'programming'} {language_pref or ''}"
        findings = self.simulate_search(search_query)

        self.memory.write("session:findings", findings, MemoryType.EPISODIC)

        prompt = f"""You are a helpful research assistant.
User prefers: {language_pref or 'any language'}
Topic: {topic_pref or 'general programming'}
Recent findings: {findings}

Provide a brief recommendation (2 sentences max) based on the findings."""

        try:
            response = llm_chat(
                self.llm,
                self.model,
                messages=[{"role": "user", "content": prompt}],
                config=self.config,
            )
        except Exception as e:
            # Extract short error message
            error_msg = str(e)
            if "401" in error_msg:
                error_msg = "API Key invalid (401) — check OPENAI_API_KEY"
            elif "404" in error_msg:
                error_msg = f"Model not found (404) — check MEMGUARD_LLM_MODEL={self.config.model}"
            elif "Connection" in error_msg or "connect" in error_msg.lower():
                error_msg = f"Cannot connect — check network or MEMGUARD_LLM_BASE_URL"
            else:
                error_msg = error_msg.split("\n")[0][:100]
            response = (
                f"[⚠️  LLM call failed: {error_msg}]\n\n"
                f"Based on findings, consider following the latest developments in the {language_pref or 'relevant'} ecosystem."
            )

        self.memory.write("session:recommendation", response, MemoryType.WORKING)
        stats["traces"] += 1

        return response


def main():
    # ── Display LLM config ──────────────────────────────────
    console.print(Panel.fit(
        "[bold cyan]MemGuard Quick Demo[/bold cyan]\n"
        "[dim]Watch memory operations in real-time[/dim]",
        border_style="cyan",
    ))

    llm_config = check_config()

    # ── Check API key ────────────────────────────────────
    if llm_config.provider != "ollama" and not llm_config.api_key:
        console.print("\n[red bold]❌ API Key not set[/red bold]")
        console.print()
        console.print("[dim]Please set one of the following environment variables:[/dim]")
        console.print(f"  [cyan]export {llm_config.provider.upper()}_API_KEY=xxx[/cyan]")
        console.print(f"  [cyan]export MEMGUARD_LLM_API_KEY=xxx[/cyan]")
        console.print()
        console.print("[dim]Or use local Ollama (no API key needed):[/dim]")
        console.print("  [cyan]export MEMGUARD_LLM_PROVIDER=ollama[/cyan]")
        console.print("  [cyan]export MEMGUARD_LLM_MODEL=qwen2.5:7b[/cyan]")
        console.print()
        console.print("[dim]View all config options: [bold]cat .env.example[/bold][/dim]")
        console.print()
        return

    # ── Create LLM client ─────────────────────────────────
    try:
        llm_client, llm_model = create_llm_client(llm_config)
        console.print(f"[dim]✅ Connected: {llm_config.provider} / {llm_model}[/dim]")
    except Exception as e:
        console.print(f"[red bold]❌ LLM init failed:[/red bold] {e}")
        return

    # ── Initialize MemGuard ────────────────────────────────
    interceptor = MemGuardInterceptor(
        agent_id="research-assistant",
        transport=NullTransport(),
        namespace="demo",
        capture_content=True,
    )
    interceptor.set_session("demo-session-001")

    memory = SimpleMemoryStore(interceptor)
    assistant = ResearchAssistant(memory, llm_client, llm_model, llm_config)

    # ── Set user preferences ─────────────────────────────
    console.print("\n[bold]Setting up user preferences...[/bold]\n")
    memory.write("user:language_preference", "Python", MemoryType.SEMANTIC)
    memory.write("user:topic_preference", "AI frameworks", MemoryType.SEMANTIC)
    time.sleep(0.5)

    # ── Research task 1 ─────────────────────────────────
    console.print("\n[bold]Running research task...[/bold]\n")
    result1 = assistant.run("What's new in Python for AI development?")
    console.print(f"\n[bold green]Assistant:[/bold green] {result1}\n")
    time.sleep(0.5)

    # ── Trigger Conflict ──────────────────────────────────
    console.print("\n[bold]Simulating concurrent writes (conflict scenario)...[/bold]\n")
    memory.write("session:recommendation", "Alternative recommendation A", MemoryType.WORKING)
    time.sleep(0.3)
    memory.write("session:recommendation", "Alternative recommendation B", MemoryType.WORKING)
    time.sleep(0.5)

    # ── Research task 2 ─────────────────────────────────
    console.print("\n[bold]Running second research task...[/bold]\n")
    memory.write("user:topic_preference", "JavaScript", MemoryType.SEMANTIC)
    result2 = assistant.run("What about JavaScript updates?")
    console.print(f"\n[bold green]Assistant:[/bold green] {result2}\n")

    # ── Session Summary ──────────────────────────────────
    console.print("\n")
    table = Table(title="MemGuard Session Summary", border_style="cyan", show_header=False)
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Count", style="bold white", width=10)

    table.add_row("Total events", str(stats["total_events"]))
    table.add_row("Memory reads", str(stats["reads"]))
    table.add_row("Memory writes", str(stats["writes"]))
    table.add_row(
        "Conflicts",
        f"[red]{stats['conflicts']}[/red]" if stats["conflicts"] > 0 else "0",
    )
    table.add_row("Decision traces", str(stats["traces"]))

    console.print(table)

    # ── Quick tips ────────────────────────────────────────
    console.print()
    provider_tips = {
        "openai": "💡 Try another model: export MEMGUARD_LLM_MODEL=gpt-4o",
        "anthropic": "💡 Try another model: export MEMGUARD_LLM_MODEL=claude-opus-4-8",
        "ollama": "💡 Try another model: export MEMGUARD_LLM_MODEL=llama3.1:8b",
        "openai_compatible": "💡 Verify BASE_URL is correct: echo $MEMGUARD_LLM_BASE_URL",
    }
    tip = provider_tips.get(llm_config.provider, "")
    if tip:
        console.print(f"[dim]{tip}[/dim]")
    console.print("[dim]→ Run with dashboard: [bold]python demo_with_dashboard.py[/bold][/dim]")
    console.print("[dim]→ Config help: [bold]cat .env.example[/bold][/dim]")
    console.print()


if __name__ == "__main__":
    main()
