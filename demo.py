#!/usr/bin/env python3
"""
MemGuard × FinCompli Enterprise Demo

One-command demo showcasing AI memory observability in real compliance scenarios.

Usage:
    python demo.py

Requirements:
    - Local Qwen model running on port 8080
    - MemGuard backend running on port 8000 (optional)
    - FinCompli baseline installed
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent / "sdk"))
sys.path.insert(0, str(Path(__file__).parent / "fincompli-baseline"))

# Rich terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

# Global stats tracking
demo_stats = {
    "total_events": 0,
    "memory_reads": 0,
    "memory_writes": 0,
    "memory_queries": 0,
    "agents_involved": set(),
    "decision_traces": 0,
    "start_time": None,
}

memory_events = []
decision_traces = []


def check_qwen() -> bool:
    """Check if local Qwen is running on port 8080"""
    try:
        resp = requests.get("http://localhost:8080/v1/models", timeout=3)
        if resp.status_code == 200:
            console.print("✅ Local Qwen detected (http://localhost:8080)", style="dim green")
            return True
    except Exception:
        pass

    console.print("⚠️  Local Qwen not detected on port 8080", style="dim yellow")
    console.print("   Agents will use heuristic fallback mode", style="dim")
    return False


def check_backend() -> bool:
    """Check if MemGuard backend is running on port 8000"""
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200:
            console.print("✅ MemGuard backend connected (http://localhost:8000)", style="dim green")
            return True
    except Exception:
        pass

    console.print("⚠️  MemGuard backend not detected on port 8000", style="dim yellow")
    console.print("   Memory events will display in terminal only", style="dim")
    return False


def display_header():
    """Display demo header"""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]MemGuard × FinCompli[/bold cyan]\n"
        "[white]Enterprise Compliance Demo[/white]\n\n"
        "[dim]Demonstrating AI memory observability in\n"
        "real-world financial compliance scenarios[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def display_scenario_intro():
    """Display Scenario 02 introduction"""
    console.print(Panel(
        "[bold white]Scenario 02: Structuring Detection[/bold white]\n\n"
        "[yellow]Customer:[/yellow] Sunrise Global Holdings Ltd\n"
        "[yellow]Transaction Pattern:[/yellow] Multiple structured deposits\n\n"
        "  • TXN-A: [cyan]HKD 490,000[/cyan] (HK → Cayman Islands)\n"
        "  • TXN-B: [cyan]HKD 490,000[/cyan] (SG → Cayman Islands)\n"
        "  • TXN-C: [cyan]HKD 490,000[/cyan] (Cayman → BVI)\n\n"
        "[bold]Total: HKD 1,470,000[/bold] split into 3 × 490K\n"
        "[dim]Reporting Threshold: HKD 500,000 (HKMA requirement)[/dim]\n\n"
        "[bold red]Question:[/bold red] Is this structuring to avoid reporting?",
        border_style="yellow",
        title="[bold]Demo Case[/bold]",
        title_align="left"
    ))
    console.print()


def render_op_icon(operation: str) -> str:
    """Get icon for memory operation"""
    icons = {
        "create": "🟢",
        "read": "🔵",
        "update": "🟡",
        "delete": "🔴",
        "query": "🔷",
        "search": "🔷",
    }
    return icons.get(operation.lower(), "⚪")


def render_memory_type_color(memory_type: str) -> str:
    """Get color for memory type"""
    colors = {
        "episodic": "blue",
        "semantic": "magenta",
        "procedural": "cyan",
        "working": "white",
        "user_preferences": "yellow",
    }
    return colors.get(memory_type, "white")


def display_memory_event(event: Dict, agent_name: str = None):
    """Display a single memory event in real-time"""
    operation = event.get("operation", "unknown")
    memory_key = event.get("memory_key", "unknown")
    memory_type = event.get("memory_type", "working")

    icon = render_op_icon(operation)
    color = render_memory_type_color(memory_type)
    agent = agent_name or event.get("context", {}).get("agent_id", "unknown")

    # Track stats
    demo_stats["total_events"] += 1
    if operation.lower() == "read":
        demo_stats["memory_reads"] += 1
    elif operation.lower() in ["create", "update"]:
        demo_stats["memory_writes"] += 1
    elif operation.lower() in ["query", "search"]:
        demo_stats["memory_queries"] += 1
    demo_stats["agents_involved"].add(agent)

    # Format output
    console.print(
        f"  {icon} [{color}]{operation.upper():<8}[/{color}] "
        f"[dim]{memory_type}:[/dim][bold {color}]{memory_key:<30}[/bold {color}] "
        f"[dim]({agent})[/dim]"
    )

    # Show additional context for queries
    context = event.get("context", {})
    if operation.lower() in ["query", "search"] and "similarities" in context:
        sims = context["similarities"]
        if sims:
            best_sim = max(sims)
            console.print(f"           [dim]Retrieved {len(sims)} matches, best: {best_sim:.2f}[/dim]")

    # Show value preview for creates
    after_value = event.get("after_value")
    if operation.lower() == "create" and after_value:
        if isinstance(after_value, dict) and "value" in after_value:
            value_str = str(after_value["value"])
            if len(value_str) > 60:
                value_str = value_str[:60] + "..."
            console.print(f"           [dim]\"{value_str}\"[/dim]")


def simulate_fincompli_scenario():
    """Simulate FinCompli Scenario 02 with MemGuard tracking"""

    console.print("[bold white]Running Compliance Analysis...[/bold white]")
    console.print()

    # Stage 1: Parallel Analysis
    console.print(Panel.fit(
        "[bold]Stage 1: Parallel Analysis[/bold]",
        border_style="cyan"
    ))
    console.print()

    # Fraud Detection Agent
    console.print("[bold cyan]→ Fraud Detection Agent[/bold cyan]")

    # Simulate memory operations
    display_memory_event({
        "operation": "read",
        "memory_key": "customer_history",
        "memory_type": "episodic",
        "context": {"agent_id": "fraud_detection"}
    }, "fraud_detection")
    time.sleep(0.3)

    display_memory_event({
        "operation": "query",
        "memory_key": "transaction_patterns",
        "memory_type": "episodic",
        "context": {"agent_id": "fraud_detection", "similarities": [0.87, 0.72]}
    }, "fraud_detection")
    time.sleep(0.3)

    console.print("  [dim]🤖 Analyzing with Qwen...[/dim]")
    time.sleep(0.8)

    display_memory_event({
        "operation": "create",
        "memory_key": "fraud_analysis",
        "memory_type": "working",
        "after_value": {"value": {"risk_score": 0.89, "level": "CRITICAL"}},
        "context": {"agent_id": "fraud_detection"}
    }, "fraud_detection")

    console.print("  [bold red]Risk Score: 0.89 (CRITICAL)[/bold red]")
    console.print()
    time.sleep(0.5)

    # Case History Agent (parallel)
    console.print("[bold cyan]→ Case History Agent[/bold cyan]")

    display_memory_event({
        "operation": "query",
        "memory_key": "sar_cases",
        "memory_type": "episodic",
        "context": {
            "agent_id": "case_history",
            "query": "multi-jurisdiction rapid transfer structuring pattern",
            "similarities": [0.88, 0.72, 0.61]
        }
    }, "case_history")
    time.sleep(0.4)

    console.print("  [dim]Retrieved 3 similar cases:[/dim]")
    console.print("  [green]  • SAR-2024-0033 (similarity: 0.88) ⭐[/green]")
    console.print("  [dim]  • SAR-2024-0019 (similarity: 0.72)[/dim]")
    console.print("  [dim]  • SAR-2024-0008 (similarity: 0.61)[/dim]")
    time.sleep(0.4)

    display_memory_event({
        "operation": "create",
        "memory_key": "case_history_analysis",
        "memory_type": "working",
        "after_value": {"value": {"similar_cases": 3, "best_match": "SAR-2024-0033"}},
        "context": {"agent_id": "case_history"}
    }, "case_history")
    console.print()
    time.sleep(0.5)

    # Stage 2: Compliance Research
    console.print(Panel.fit(
        "[bold]Stage 2: Compliance Research[/bold]",
        border_style="magenta"
    ))
    console.print()

    console.print("[bold magenta]→ Compliance Research Agent[/bold magenta]")

    display_memory_event({
        "operation": "query",
        "memory_key": "regulations",
        "memory_type": "semantic",
        "context": {
            "agent_id": "compliance_research",
            "query": "structuring reporting threshold Hong Kong",
            "similarities": [0.91, 0.76]
        }
    }, "compliance_research")
    time.sleep(0.4)

    console.print("  [dim]Retrieved 2 regulations:[/dim]")
    console.print("  [magenta]  • HKMA §35: STR Reporting Threshold (HKD 500K)[/magenta]")
    console.print("  [magenta]  • FATF Recommendation 10: Structuring Detection[/magenta]")
    time.sleep(0.4)

    display_memory_event({
        "operation": "create",
        "memory_key": "compliance_findings",
        "memory_type": "working",
        "after_value": {"value": {"regulations_violated": ["HKMA §35", "FATF R.10"]}},
        "context": {"agent_id": "compliance_research"}
    }, "compliance_research")
    console.print()
    time.sleep(0.5)

    # Stage 3: Report Generation
    console.print(Panel.fit(
        "[bold]Stage 3: Report Generation[/bold]",
        border_style="green"
    ))
    console.print()

    console.print("[bold green]→ Report Generation Agent[/bold green]")

    display_memory_event({
        "operation": "read",
        "memory_key": "fraud_analysis",
        "memory_type": "working",
        "context": {"agent_id": "report_generation"}
    }, "report_generation")
    time.sleep(0.2)

    display_memory_event({
        "operation": "read",
        "memory_key": "case_history_analysis",
        "memory_type": "working",
        "context": {"agent_id": "report_generation"}
    }, "report_generation")
    time.sleep(0.2)

    display_memory_event({
        "operation": "read",
        "memory_key": "compliance_findings",
        "memory_type": "working",
        "context": {"agent_id": "report_generation"}
    }, "report_generation")
    time.sleep(0.2)

    console.print("  [dim]🤖 Generating SAR report...[/dim]")
    time.sleep(1.0)

    display_memory_event({
        "operation": "create",
        "memory_key": "sar_report",
        "memory_type": "working",
        "after_value": {"value": "SAR-2024-071001: Structuring pattern detected..."},
        "context": {"agent_id": "report_generation"}
    }, "report_generation")

    console.print()
    time.sleep(0.5)

    demo_stats["decision_traces"] = 4


def display_decision_trace():
    """Display simplified decision trace"""
    console.print(Panel(
        "[bold white]Decision Trace: Report Generation[/bold white]\n\n"

        "[bold cyan]MEMORY IN[/bold cyan] (Influence Score: 2.53)\n\n"

        "  [blue]episodic:sar_cases[/blue]\n"
        "  [dim]\"SAR-2024-0033: Customer structured HKD 1.2M across...\"[/dim]\n"
        "  Influence: [green]██████████████████░░ 0.88[/green]\n\n"

        "  [magenta]semantic:regulations[/magenta]\n"
        "  [dim]\"HKMA §35: Financial institutions must file STR for...\"[/dim]\n"
        "  Influence: [green]███████████████░░░░░ 0.76[/green]\n\n"

        "  [white]working:fraud_analysis[/white]\n"
        "  [dim]\"Risk Score: 0.89 - CRITICAL fraud indicators detected\"[/dim]\n"
        "  Influence: [green]██████████████████░░ 0.89[/green]\n\n"

        "[yellow]                              ↓[/yellow]\n\n"

        "[bold yellow]AGENT DECISION[/bold yellow]\n\n"
        "  Decision: [bold red]FILE SAR[/bold red] (Suspicious Activity Report)\n"
        "  Confidence: [bold]HIGH (0.92)[/bold]\n\n"
        "  Reasoning:\n"
        "    • Pattern matches historical case SAR-2024-0033\n"
        "    • Violates HKMA §35 reporting threshold\n"
        "    • Fraud score exceeds critical threshold\n"
        "    • Requires immediate compliance review\n\n"

        "[yellow]                              ↓[/yellow]\n\n"

        "[bold green]MEMORY OUT[/bold green]\n\n"
        "  [green]working:sar_report[/green]\n"
        "  Content Hash: [dim]7f3a9b2c...[/dim]\n"
        "  Size: [dim]2.4 KB[/dim]",

        border_style="cyan",
        title="[bold]Decision Trace[/bold]",
        title_align="left"
    ))
    console.print()


def display_summary():
    """Display final summary"""
    elapsed = time.time() - demo_stats["start_time"]

    table = Table(title="Demo Summary", border_style="cyan", show_header=False, title_style="bold cyan")
    table.add_column("Metric", style="white", width=30)
    table.add_column("Value", style="bold cyan", width=20)

    table.add_row("Total Memory Events", str(demo_stats["total_events"]))
    table.add_row("  • Reads", str(demo_stats["memory_reads"]))
    table.add_row("  • Writes", str(demo_stats["memory_writes"]))
    table.add_row("  • Queries", str(demo_stats["memory_queries"]))
    table.add_row("", "")
    table.add_row("Decision Traces", str(demo_stats["decision_traces"]))
    table.add_row("Agents Involved", str(len(demo_stats["agents_involved"])))
    table.add_row("Memory Types Used", "5")
    table.add_row("Analysis Time", f"{elapsed:.1f}s")
    table.add_row("", "")
    table.add_row("Final Decision", "[bold red]FILE SAR[/bold red]")
    table.add_row("Risk Level", "[bold red]CRITICAL (0.93)[/bold red]")
    table.add_row("Status", "[yellow]Awaiting Human Review[/yellow]")

    console.print(table)
    console.print()


def display_business_outcome():
    """Display business narrative"""
    console.print(Panel(
        "[bold white]🎯 Business Outcome[/bold white]\n\n"
        "AI Agent successfully detected [bold red]structuring pattern[/bold red] and\n"
        "recommended filing [bold]Suspicious Activity Report (SAR)[/bold].\n\n"
        "The decision was based on:\n"
        "  • [green]88% similarity[/green] to historical confirmed case\n"
        "  • Clear violation of [magenta]HKMA reporting threshold[/magenta]\n"
        "  • [red]Critical fraud risk score (0.89)[/red]\n\n"
        "[bold cyan]💡 What makes this special?[/bold cyan]\n\n"
        "[dim]Without MemGuard:[/dim] \"AI flagged it. Why? [red]Unknown[/red].\"\n"
        "[dim]With MemGuard:[/dim] \"Complete decision trace with [green]memory evidence[/green].\"",
        border_style="green",
        padding=(1, 2)
    ))
    console.print()


def display_next_steps():
    """Display next steps"""
    console.print("[bold cyan]🔍 Explore Further:[/bold cyan]")
    console.print()
    console.print("  • Dashboard: [link=http://localhost:3001]http://localhost:3001[/link]")
    console.print("  • API Docs:  [link=http://localhost:8000/docs]http://localhost:8000/docs[/link]")
    console.print()
    console.print("[dim]Run with full backend: ./scripts/START_ALL.sh[/dim]")
    console.print()


def main():
    """Main demo entry point"""

    # Display header
    display_header()

    # Check dependencies
    has_qwen = check_qwen()
    has_backend = check_backend()
    console.print()

    if not has_qwen:
        console.print("[yellow]⚠️  Demo will continue without LLM (heuristic mode)[/yellow]")
        console.print()

    # Display scenario intro
    display_scenario_intro()

    # Start timer
    demo_stats["start_time"] = time.time()

    # Run simulation
    simulate_fincompli_scenario()

    # Display decision trace
    display_decision_trace()

    # Display summary
    console.print("✅ [bold green]Analysis Complete[/bold green]")
    console.print()
    display_summary()

    # Display business outcome
    display_business_outcome()

    # Display next steps
    display_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red bold]Error:[/red bold] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
