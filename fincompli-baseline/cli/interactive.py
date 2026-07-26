"""
Interactive CLI for FinCompli Baseline

Provides interactive testing of the compliance workflow with predefined scenarios.

Usage:
    python cli/interactive.py --scenario 02              # heuristic only
    python cli/interactive.py --scenario 02 --memory     # with domain memory (ChromaDB)
    python cli/interactive.py --scenario 02 --memory --llm   # with Qwen LLM
    python cli/interactive.py --scenario 02 --memory --llm --memguard  # + MemGuard tracing
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from graph import create_initial_state, build_compliance_graph
from graph.builder import run_compliance_workflow
from memory import MemoryLayer

console = Console()


def load_scenario(scenario_id: str) -> dict:
    """Load a predefined scenario from scenarios directory"""
    scenario_file = Path(__file__).parent.parent / "scenarios" / f"scenario_{scenario_id}.json"

    if not scenario_file.exists():
        console.print(f"[red]❌ Scenario {scenario_id} not found at {scenario_file}[/red]")
        sys.exit(1)

    with open(scenario_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_scenario_info(scenario: dict):
    """Display scenario information"""
    console.print("\n" + "="*70)
    console.print(Panel(
        f"[bold cyan]{scenario['title']}[/bold cyan]\n"
        f"[yellow]Scenario ID:[/yellow] {scenario['scenario_id']}\n"
        f"[yellow]Type:[/yellow] {scenario['type']}\n"
        f"[yellow]Expected Risk:[/yellow] {scenario['expected_risk_level']}\n\n"
        f"{scenario['description']}",
        title="📋 Scenario Information",
        border_style="cyan"
    ))


def display_transaction(txn: dict):
    """Display transaction details"""
    table = Table(title="💰 Transaction Details", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Transaction ID", txn.get("transaction_id", "N/A"))
    table.add_row("Customer ID", txn.get("customer_id", "N/A"))
    table.add_row("Amount", f"{txn.get('currency', 'HKD')} {txn.get('amount', 0):,.2f}")
    table.add_row("Pattern", txn.get("transaction_pattern", "N/A"))

    if txn.get("from_account"):
        table.add_row("From Account", txn["from_account"])
    if txn.get("to_account"):
        table.add_row("To Account", txn["to_account"])
    if txn.get("to_country"):
        table.add_row("Destination", txn["to_country"])

    console.print(table)


def display_analysis_results(state: dict):
    """Display analysis results after workflow completion"""
    console.print("\n" + "="*70)
    console.print(Panel(
        "[bold green]✅ Analysis Complete[/bold green]",
        title="🎯 Workflow Status",
        border_style="green"
    ))

    # Risk Assessment
    risk_score = state.get("risk_score", 0)
    risk_level = state.get("risk_level", "unknown")

    risk_color = "green" if risk_score < 0.3 else "yellow" if risk_score < 0.85 else "red"

    console.print(f"\n[bold]Risk Assessment:[/bold]")
    console.print(f"  Score: [{risk_color}]{risk_score:.2f}[/{risk_color}]")
    console.print(f"  Level: [{risk_color}]{risk_level.upper()}[/{risk_color}]")
    console.print(f"  Human Review: {'✅ Required' if state.get('requires_human_review') else '❌ Not Required'}")

    # Fraud Analysis
    if state.get("fraud_analysis"):
        fa = state["fraud_analysis"]
        console.print(f"\n[bold]Fraud Detection:[/bold]")
        console.print(f"  Fraud Score: {fa.get('fraud_score', 0):.2f}")
        console.print(f"  LLM Used: {'✅ Qwen' if fa.get('llm_used') else '❌ Heuristic'}")
        console.print(f"  Indicators: {len(fa.get('risk_indicators', []))}")
        for ind in fa.get("risk_indicators", [])[:3]:
            console.print(f"    • {ind}")

    # Case History
    if state.get("case_history_analysis"):
        ch = state["case_history_analysis"]
        console.print(f"\n[bold]Case History:[/bold]")
        console.print(f"  Similar Cases: {ch.get('similar_cases_count', 0)}")
        console.print(f"  Lessons Learned: {len(ch.get('lessons_learned', []))}")

    # Compliance Research
    if state.get("compliance_research"):
        cr = state["compliance_research"]
        console.print(f"\n[bold]Compliance Research:[/bold]")
        console.print(f"  LLM Used: {'✅ Qwen' if cr.get('llm_used') else '❌ Heuristic'}")
        console.print(f"  Regulations: {len(cr.get('applicable_regulations', []))}")
        console.print(f"  Requirements: {len(cr.get('compliance_requirements', []))}")

    # Final Report
    if state.get("final_report"):
        fr = state["final_report"]
        console.print(f"\n[bold]Report:[/bold]")
        console.print(f"  LLM Used: {'✅ Qwen' if fr.get('llm_used') else '❌ Template'}")
        console.print(f"  SAR Draft: {len(fr.get('sar_draft', ''))} characters")
        console.print(f"  Recommendation: {fr.get('recommendation', 'N/A')}")

    # Memory Traces
    console.print(f"\n[bold]Memory Traces:[/bold]")
    console.print(f"  Total: {len(state.get('memory_traces', []))}")

    # Final Decision
    final_decision = state.get("final_decision", "N/A")
    decision_color = "green" if final_decision == "clear" else "red" if final_decision == "file_sar" else "yellow"
    console.print(f"\n[bold]Final Decision:[/bold] [{decision_color}]{final_decision}[/{decision_color}]")


def run_scenario(
    scenario_id: str,
    use_memory: bool = False,
    use_llm: bool = False,
    use_memguard: bool = False,
):
    """Run a predefined scenario"""
    console.print(f"\n[bold cyan]🚀 Starting FinCompli Baseline - Scenario {scenario_id}[/bold cyan]")

    # ── Mode badge ──
    modes = []
    if use_llm:
        modes.append("🤖 Qwen LLM")
    else:
        modes.append("🔧 Heuristic")
    if use_memory:
        modes.append("🧠 Domain Memory")
    if use_memguard:
        modes.append("🔍 MemGuard")
    console.print(f"[dim]Mode: {' | '.join(modes)}[/dim]")

    # Load scenario
    scenario = load_scenario(scenario_id)
    display_scenario_info(scenario)
    display_transaction(scenario)

    # ── Initialize memory layer ──
    memory_layer = None
    if use_memory:
        console.print("\n[yellow]⚙️  Initializing memory layer...[/yellow]")
        try:
            from config import get_data_dir
            memory_layer = MemoryLayer(
                chroma_path=get_data_dir() / "chroma",
                sqlite_path=get_data_dir() / "sqlite" / "fincompli.db"
            )
            stats = memory_layer.get_memory_statistics()
            console.print("[green]✅ Memory layer initialized[/green]")
            console.print(f"[dim]   Episodic: {stats.get('episodic', {})}[/dim]")
            console.print(f"[dim]   Semantic: {stats.get('semantic', {})}[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Memory layer unavailable: {e}[/yellow]")
            console.print("[yellow]   Continuing without domain memory...[/yellow]")

    # ── Initialize LLM client ──
    llm_client = None
    if use_llm:
        console.print("\n[yellow]🤖 Initializing Qwen LLM client...[/yellow]")
        try:
            from llm_client import LLMClient
            llm_client = LLMClient()
            if llm_client.health_check():
                console.print(f"[green]✅ Qwen connected at {llm_client.base_url}[/green]")
                console.print(f"[dim]   Model: {llm_client.model}[/dim]")
            else:
                console.print("[yellow]⚠️  Qwen not reachable — will use heuristic fallback[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  LLM client init failed: {e}[/yellow]")

    # ── Initialize MemGuard ──
    interceptor = None
    memguard_checkpointer = None
    if use_memguard:
        console.print("\n[yellow]🔍 Initializing MemGuard SDK...[/yellow]")
        try:
            from memguard.adapters.langgraph import MemGuardCheckpointer
            from memguard.transport import HttpTransport, StdoutTransport
            from langgraph.checkpoint.memory import MemorySaver

            transport = HttpTransport("http://localhost:8000")
            interceptor = transport.interceptor if hasattr(transport, 'interceptor') else None
            # Actually, interceptor needs special handling — create it manually
            from memguard.core.interceptor import MemGuardInterceptor
            interceptor = MemGuardInterceptor(
                agent_id="fincompli-supervisor",
                transport=transport,
                namespace="fincompli",
                capture_content=False,
            )
            interceptor.set_session(f"scenario-{scenario_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

            memguard_checkpointer = MemGuardCheckpointer(
                inner=MemorySaver(),
                agent_id="fincompli-supervisor",
                namespace="fincompli",
                transport=transport,
            )
            console.print("[green]✅ MemGuard SDK initialized[/green]")
            console.print("[dim]   Transport: HTTP → http://localhost:8000[/dim]")
        except ImportError as e:
            console.print(f"[yellow]⚠️  MemGuard SDK not installed: {e}[/yellow]")
            console.print("[yellow]   Run: pip install -e ../sdk[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠️  MemGuard init failed: {e}[/yellow]")

    # ── Build graph ──
    console.print("\n[yellow]⚙️  Building compliance graph...[/yellow]")
    graph = build_compliance_graph(memory_saver=memguard_checkpointer)
    console.print("[green]✅ Graph built[/green]")

    # ── Create initial state ──
    thread_id = f"scenario-{scenario_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    state = create_initial_state(
        transaction_id=scenario["transaction_id"],
        customer_id=scenario["customer_id"],
        amount=scenario["amount"],
        currency=scenario.get("currency", "HKD"),
        transaction_pattern=scenario["transaction_pattern"],
        thread_id=thread_id,
        from_account=scenario.get("from_account"),
        to_account=scenario.get("to_account"),
        to_country=scenario.get("to_country")
    )

    # ── Run workflow ──
    console.print(f"\n[yellow]⚙️  Running compliance workflow...[/yellow]")
    console.print(f"[dim]Thread ID: {thread_id}[/dim]")

    try:
        final_state = run_compliance_workflow(
            graph=graph,
            state=state,
            thread_id=thread_id,
            llm_client=llm_client,
            interceptor=interceptor,
            memory_layer=memory_layer,
        )

        # Display results
        display_analysis_results(final_state)

        # Optionally display SAR draft
        if final_state.get("final_report", {}).get("sar_draft"):
            console.print("\n" + "="*70)
            if console.input("\n[cyan]📄 View SAR draft? (y/n): [/cyan]").lower() == 'y':
                console.print("\n" + "="*70)
                console.print(final_state["final_report"]["sar_draft"])
                console.print("="*70)

        # ── MemGuard summary ──
        if use_memguard:
            console.print("\n" + "="*70)
            console.print(Panel(
                "[bold green]🔍 MemGuard Observability[/bold green]\n\n"
                f"Session: {thread_id}\n"
                f"Dashboard: http://localhost:3001\n"
                f"Backend:   http://localhost:8000\n\n"
                "Check the dashboard to see:\n"
                "  • Which memories each agent read\n"
                "  • What each agent output\n"
                "  • Decision traces linking memory → output",
                title="📊 Observability",
                border_style="magenta"
            ))

        console.print(f"\n[green]✅ Workflow complete![/green]")
        return final_state

    except Exception as e:
        console.print(f"\n[red]❌ Error during workflow execution:[/red]")
        console.print(f"[red]{type(e).__name__}: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def list_scenarios():
    """List all available scenarios"""
    scenarios_dir = Path(__file__).parent.parent / "scenarios"

    if not scenarios_dir.exists():
        console.print("[red]❌ Scenarios directory not found[/red]")
        return

    scenario_files = sorted(scenarios_dir.glob("scenario_*.json"))

    if not scenario_files:
        console.print("[yellow]⚠️  No scenarios found[/yellow]")
        return

    console.print("\n[bold cyan]📂 Available Scenarios:[/bold cyan]\n")

    for file in scenario_files:
        try:
            with open(file, 'r') as f:
                sc = json.load(f)
            console.print(f"[green]▸[/green] [bold]{sc['scenario_id']}[/bold]: {sc['title']}")
            console.print(f"  Type: {sc['type']} | Risk: {sc['expected_risk_level']}")
            console.print()
        except:
            continue


def main():
    parser = argparse.ArgumentParser(
        description="FinCompli Baseline - Interactive CLI"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Run a specific scenario (e.g., 02)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scenarios"
    )
    parser.add_argument(
        "--memory",
        action="store_true",
        help="Enable domain memory layer (ChromaDB + SQLite)"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use Qwen LLM for agent reasoning (falls back to heuristic if unreachable)"
    )
    parser.add_argument(
        "--memguard",
        action="store_true",
        help="Enable MemGuard SDK tracing (requires SDK installed + backend running)"
    )

    args = parser.parse_args()

    if args.list:
        list_scenarios()
    elif args.scenario:
        run_scenario(
            args.scenario,
            use_memory=args.memory,
            use_llm=args.llm,
            use_memguard=args.memguard,
        )
    else:
        console.print("[yellow]Usage:[/yellow]")
        console.print("  python cli/interactive.py --list")
        console.print("  python cli/interactive.py --scenario 02")
        console.print("  python cli/interactive.py --scenario 02 --memory")
        console.print("  python cli/interactive.py --scenario 02 --memory --llm")
        console.print("  python cli/interactive.py --scenario 02 --memory --llm --memguard")


if __name__ == "__main__":
    main()
