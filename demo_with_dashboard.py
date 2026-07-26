#!/usr/bin/env python3
"""
MemGuard Dashboard Demo

Step 1: Start the backend and dashboard:
    ./scripts/START_ALL.sh

Step 2: Run this script:
    # Default: uses OpenAI gpt-4o-mini
    export OPENAI_API_KEY=sk-xxx
    python demo_with_dashboard.py

    # Using Anthropic Claude
    export MEMGUARD_LLM_PROVIDER=anthropic
    export ANTHROPIC_API_KEY=sk-ant-xxx
    python demo_with_dashboard.py

    # Using local Ollama
    export MEMGUARD_LLM_PROVIDER=ollama
    export MEMGUARD_LLM_MODEL=qwen2.5:7b
    python demo_with_dashboard.py

Step 3: Open the dashboard:
    http://localhost:3001

You'll see:
  • Memory timeline with all events
  • Decision traces linking memory reads to decisions
  • Conflict detection
  • Audit report (click button in top right)
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
from memguard.transport.http import HttpTransport

console = Console()

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

    def write(self, key: str, value: Any, memory_type: MemoryType = MemoryType.WORKING) -> str:
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
        event_id = self.interceptor.record(
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
            f"[dim]→ Backend[/dim]"
        )

        stats["total_events"] += 1
        stats["writes"] += 1

        return event_id

    def read(self, key: str) -> tuple:
        value = self.data.get(key)

        event_id = self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key=key,
            after_value={"value": value} if value else None,
            memory_type=MemoryType.WORKING,
        )

        console.print(
            f"[bright_white][MemGuard] 🔵 READ[/bright_white]    "
            f"[cyan]{key:<30}[/cyan] "
            f"[dim]→ Backend[/dim]"
        )

        stats["total_events"] += 1
        stats["reads"] += 1

        return value, event_id


class ResearchAssistant:
    """Simple research assistant that uses memory."""

    def __init__(self, memory: SimpleMemoryStore, llm_client, llm_model: str,
                 llm_config: LLMConfig, interceptor: MemGuardInterceptor):
        self.memory = memory
        self.llm = llm_client
        self.model = llm_model
        self.config = llm_config
        self.interceptor = interceptor

    def simulate_search(self, query: str) -> str:
        if "python" in query.lower():
            return "Python 3.12 released with improved error messages and performance optimizations."
        elif "javascript" in query.lower():
            return "JavaScript ES2024 features include new array methods and improved async handling."
        else:
            return f"Research findings for: {query}"

    def run(self, user_request: str) -> str:
        console.print(f"\n[bold blue]User:[/bold blue] {user_request}\n")

        input_events = []

        _, evt_id = self.memory.read("user:language_preference")
        input_events.append(evt_id)

        _, evt_id = self.memory.read("user:topic_preference")
        input_events.append(evt_id)

        language_pref = self.memory.data.get("user:language_preference")
        topic_pref = self.memory.data.get("user:topic_preference")

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
            error_msg = str(e)
            if "401" in error_msg:
                error_msg = "API Key invalid (401)"
            elif "404" in error_msg:
                error_msg = f"Model not found (404): {self.config.model}"
            elif "Connection" in error_msg:
                error_msg = "Cannot connect"
            else:
                error_msg = error_msg.split("\n")[0][:100]
            response = f"[⚠️  LLM call failed: {error_msg}]\n\nSuggestion based on findings."

        output_evt_id = self.memory.write("session:recommendation", response, MemoryType.WORKING)

        # Create DecisionTrace
        self.interceptor.trace_decision(
            input_event_ids=input_events,
            output_event_ids=[output_evt_id],
            prompt_text=prompt,
            output_text=response,
            influence_score=0.0,  # Let backend calculate automatically
        )

        stats["traces"] += 1

        return response


def main():
    console.print(Panel.fit(
        "[bold cyan]MemGuard Dashboard Demo[/bold cyan]\n"
        "[dim]Events are being sent to the backend for visualization[/dim]",
        border_style="cyan",
    ))

    llm_config = check_config()

    # Check API key
    if llm_config.provider != "ollama" and not llm_config.api_key:
        console.print("\n[red bold]❌ API Key not set[/red bold]")
        console.print()
        console.print("[dim]Please set one of the following environment variables:[/dim]")
        console.print(f"  [cyan]export {llm_config.provider.upper()}_API_KEY=xxx[/cyan]")
        console.print(f"  [cyan]export MEMGUARD_LLM_API_KEY=xxx[/cyan]")
        console.print()
        console.print("[dim]Or use local Ollama:[/dim]")
        console.print("  [cyan]export MEMGUARD_LLM_PROVIDER=ollama[/cyan]")
        console.print("  [cyan]export MEMGUARD_LLM_MODEL=qwen2.5:7b[/cyan]")
        console.print()
        return

    # Create LLM client
    try:
        llm_client, llm_model = create_llm_client(llm_config)
        console.print(f"[dim]✅ Connected: {llm_config.provider} / {llm_model}[/dim]")
    except Exception as e:
        console.print(f"[red bold]❌ LLM init failed:[/red bold] {e}")
        return

    # Initialize MemGuard (HTTP transport → backend)
    try:
        transport = HttpTransport(base_url="http://localhost:8000")
        interceptor = MemGuardInterceptor(
            agent_id="research-assistant-dashboard",
            transport=transport,
            namespace="demo",
            capture_content=True,
        )
        interceptor.set_session("demo-dashboard-session")
    except Exception as e:
        console.print(f"[red bold]❌ Cannot connect to Backend[/red bold]")
        console.print("[dim]Please start Backend first: ./scripts/START_ALL.sh[/dim]")
        return

    memory = SimpleMemoryStore(interceptor)
    assistant = ResearchAssistant(memory, llm_client, llm_model, llm_config, interceptor)

    # Set user preferences
    console.print("\n[bold]Setting up user preferences...[/bold]\n")
    memory.write("user:language_preference", "Python", MemoryType.SEMANTIC)
    memory.write("user:topic_preference", "AI frameworks", MemoryType.SEMANTIC)
    time.sleep(0.5)

    # Research task 1
    console.print("\n[bold]Running research task...[/bold]\n")
    result1 = assistant.run("What's new in Python for AI development?")
    console.print(f"\n[bold green]Assistant:[/bold green] {result1}\n")
    time.sleep(0.5)

    # Trigger Conflict
    console.print("\n[bold]Simulating concurrent writes (conflict scenario)...[/bold]\n")
    memory.write("session:recommendation", "Alternative recommendation A", MemoryType.WORKING)
    time.sleep(0.3)
    memory.write("session:recommendation", "Alternative recommendation B", MemoryType.WORKING)
    time.sleep(0.5)

    # Research task 2
    console.print("\n[bold]Running second research task...[/bold]\n")
    memory.write("user:topic_preference", "JavaScript", MemoryType.SEMANTIC)
    result2 = assistant.run("What about JavaScript updates?")
    console.print(f"\n[bold green]Assistant:[/bold green] {result2}\n")

    # Session Summary
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

    console.print("\n[bold green]✅ Done![/bold green] Open [bold cyan]http://localhost:3001[/bold cyan] to see:\n")
    console.print(f"   • Memory timeline with {stats['total_events']} events")
    console.print(f"   • {stats['traces']} Decision traces")
    console.print(f"   • {stats['conflicts']} Conflict{'s' if stats['conflicts'] != 1 else ''} detected")
    console.print("   • Audit report (click button in top right)")
    console.print(f"\n[dim]Provider: {llm_config.provider} / Model: {llm_model}[/dim]")
    console.print()


if __name__ == "__main__":
    main()
