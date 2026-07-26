"""
Decision Trace Terminal Display

Beautiful Rich-based formatting for decision traces showing the causal chain:
Memory IN → Agent Decision → Memory OUT
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Dict, List, Optional


class DecisionTraceDisplay:
    """Display decision traces in terminal with Rich formatting"""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def render_influence_bar(self, score: float, width: int = 20) -> str:
        """
        Render influence score as visual bar

        Args:
            score: Influence score (0-1)
            width: Width of bar in characters

        Returns:
            Visual bar string with score
        """
        filled = int(score * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {score:.2f}"

    def display_decision_trace(self, trace: Dict) -> None:
        """
        Display full decision trace with causal chain

        Args:
            trace: Decision trace dict with input_memory_influences,
                   decision details, and output_memory_influences
        """
        self.console.print()

        # Header
        agent_id = trace.get("agent_id", "unknown")
        timestamp = trace.get("timestamp", "")

        self.console.print(Panel.fit(
            f"[bold cyan]Decision Trace: {agent_id}[/bold cyan]\n"
            f"[dim]{timestamp}[/dim]",
            border_style="cyan"
        ))

        self.console.print()

        # Memory IN
        input_influences = trace.get("input_memory_influences", [])
        if input_influences:
            self._display_memory_in(input_influences)
            self.console.print("\n" + " " * 30 + "[yellow]↓[/yellow]\n")

        # Agent Decision
        self._display_decision(
            trace.get("decision_type", "unknown"),
            trace.get("decision_confidence", 0.75),
            trace.get("decision_reasoning", "No reasoning provided"),
            trace.get("key_factors", [])
        )

        self.console.print("\n" + " " * 30 + "[yellow]↓[/yellow]\n")

        # Memory OUT
        output_influences = trace.get("output_memory_influences", [])
        if output_influences:
            self._display_memory_out(output_influences)

        self.console.print()

    def _display_memory_in(self, influences: List[Dict]) -> None:
        """Display memory inputs with influence scores"""
        self.console.print("[bold white]MEMORY IN[/bold white]")

        # Calculate total influence
        total_influence = sum(inf.get("influence_score", 0) for inf in influences)
        self.console.print(f"[dim](Total Influence: {total_influence:.2f})[/dim]")
        self.console.print()

        for influence in influences:
            # Memory operation
            operation = influence.get("operation", "read")
            icon = "🔵" if operation == "read" else "🔷"

            memory_type = influence.get("memory_type", "working")
            memory_key = influence.get("memory_key", "unknown")

            # Color by memory type
            type_colors = {
                "episodic": "blue",
                "semantic": "magenta",
                "procedural": "cyan",
                "working": "white",
                "user_preferences": "yellow",
            }
            color = type_colors.get(memory_type, "white")

            self.console.print(
                f"  {icon} [{color}]{memory_type}:{memory_key}[/{color}]"
            )

            # Content preview
            content_preview = influence.get("content_preview", "")
            if content_preview:
                # Truncate if too long
                if len(content_preview) > 80:
                    content_preview = content_preview[:80] + "..."
                self.console.print(
                    f"     [dim]\"{content_preview}\"[/dim]"
                )

            # Influence score bar
            score = influence.get("influence_score", 0)
            bar = self.render_influence_bar(score)
            self.console.print(
                f"     Influence: [green]{bar}[/green]"
            )

            # Similarity score if available
            similarity = influence.get("similarity_score")
            if similarity is not None:
                self.console.print(
                    f"     Similarity: [cyan]{similarity:.2f}[/cyan]"
                )

            self.console.print()

    def _display_decision(
        self,
        decision_type: str,
        confidence: float,
        reasoning: str,
        key_factors: List[str] = None
    ) -> None:
        """Display agent decision with reasoning"""
        self.console.print("[bold white]AGENT DECISION[/bold white]")
        self.console.print()

        # Decision type with color coding
        decision_colors = {
            "file_sar": "red",
            "escalate": "yellow",
            "clear": "green",
            "approve": "green",
            "reject": "red",
        }
        decision_color = decision_colors.get(decision_type, "white")

        self.console.print(
            f"  Decision: [bold {decision_color}]{decision_type.upper().replace('_', ' ')}[/bold {decision_color}]"
        )

        # Confidence bar
        conf_bar = self.render_influence_bar(confidence)
        self.console.print(
            f"  Confidence: [yellow]{conf_bar}[/yellow]"
        )

        self.console.print()

        # Reasoning
        if reasoning and reasoning != "No reasoning provided":
            self.console.print("  [bold]Reasoning:[/bold]")

            # Split into sentences
            sentences = reasoning.split(". ")
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Add bullet point
                    if not sentence.endswith("."):
                        sentence += "."
                    self.console.print(f"    • {sentence}")

        # Key factors if available
        if key_factors:
            self.console.print()
            self.console.print("  [bold]Key Factors:[/bold]")
            for factor in key_factors[:5]:  # Limit to 5
                self.console.print(f"    • {factor}")

        self.console.print()

    def _display_memory_out(self, outputs: List[Dict]) -> None:
        """Display memory outputs"""
        self.console.print("[bold white]MEMORY OUT[/bold white]")
        self.console.print()

        for output in outputs:
            operation = output.get("operation", "create")
            icon = "🟢" if operation == "create" else "🟡"

            memory_type = output.get("memory_type", "working")
            memory_key = output.get("memory_key", "unknown")

            # Color by memory type
            type_colors = {
                "episodic": "blue",
                "semantic": "magenta",
                "procedural": "cyan",
                "working": "white",
                "user_preferences": "yellow",
            }
            color = type_colors.get(memory_type, "white")

            self.console.print(
                f"  {icon} [{color}]{memory_type}:{memory_key}[/{color}]"
            )

            # Content hash
            content_hash = output.get("content_hash", "")
            if content_hash:
                # Show first 16 chars
                hash_preview = content_hash[:16] + "..." if len(content_hash) > 16 else content_hash
                self.console.print(
                    f"     Hash: [dim]{hash_preview}[/dim]"
                )

            # Timestamp
            timestamp = output.get("timestamp", "")
            if timestamp:
                self.console.print(
                    f"     Time: [dim]{timestamp}[/dim]"
                )

            self.console.print()

    def display_decision_trace_summary(self, trace: Dict) -> None:
        """
        Display compact decision trace summary (one-liner)

        Args:
            trace: Decision trace dict
        """
        agent_id = trace.get("agent_id", "unknown")
        decision_type = trace.get("decision_type", "unknown")
        confidence = trace.get("decision_confidence", 0)
        input_count = len(trace.get("input_memory_influences", []))
        output_count = len(trace.get("output_memory_influences", []))

        self.console.print(
            f"[cyan]{agent_id}[/cyan]: {input_count} reads → "
            f"[bold]{decision_type}[/bold] ({confidence:.2f}) → "
            f"{output_count} writes"
        )

    def display_multiple_traces(self, traces: List[Dict]) -> None:
        """
        Display multiple decision traces in sequence

        Args:
            traces: List of decision trace dicts
        """
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]Decision Traces[/bold cyan]\n"
            f"[dim]Showing {len(traces)} decision points[/dim]",
            border_style="cyan"
        ))
        self.console.print()

        for i, trace in enumerate(traces):
            self.console.print(f"[bold white]Trace #{i+1}[/bold white]")
            self.display_decision_trace_summary(trace)
            self.console.print()
