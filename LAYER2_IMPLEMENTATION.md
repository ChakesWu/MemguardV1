# Layer 2 Implementation Guide

**Goal:** Polish Decision Trace output to show clear causal chain: Memory IN → Agent Decision → Memory OUT

**Priority:** 🔥 HIGH - This is the core product value

---

## The Problem

Current state:
- ✅ MemGuard tracks all memory events
- ✅ MemGuard stores decision traces
- ❌ The **causal link** between memory and decision is unclear
- ❌ Influence scores are not visualized
- ❌ Decision reasoning is not extracted from LLM output

What users see now:
```
Event #1: READ episodic:sar_cases
Event #2: READ semantic:regulations
Event #3: CREATE working:sar_report
```

What users SHOULD see:
```
MEMORY IN:
  episodic:sar_cases (influence: 0.88) → SAR-2024-0033
  semantic:regulations (influence: 0.76) → HKMA §35
         ↓
DECISION: FILE SAR
  Reasoning: Pattern matches SAR-2024-0033, violates HKMA §35
         ↓
MEMORY OUT:
  working:sar_report (hash: 7f3a9b...)
```

---

## Implementation Tasks

### Task 2.1: Enhance Decision Trace Data Model

**File:** `/Users/chakeswu/cursor/MemguardV1/backend/app/schemas.py`

**Add new fields to DecisionTrace:**

```python
from typing import Optional, Dict, List
from pydantic import BaseModel

class MemoryInfluence(BaseModel):
    """Memory influence details"""
    event_id: str
    memory_key: str
    memory_type: str
    operation: str
    influence_score: float
    content_preview: Optional[str] = None  # First 100 chars
    similarity_score: Optional[float] = None  # For vector retrievals
    timestamp: str

class DecisionTrace(BaseModel):
    """Enhanced decision trace with causal chain"""
    trace_id: str
    agent_id: str
    session_id: str
    timestamp: str
    
    # Memory IN
    input_memory_influences: List[MemoryInfluence]
    total_input_influence: float
    
    # Agent Decision
    decision_type: str  # "file_sar", "clear", "escalate", etc.
    decision_confidence: float
    decision_reasoning: str  # Extracted from LLM output
    llm_output: str  # Full LLM response
    
    # Memory OUT
    output_memory_influences: List[MemoryInfluence]
    
    # Metadata
    user_input: Optional[str] = None
    metadata: Optional[Dict] = None
```

---

### Task 2.2: Implement Influence Score Calculation

**File:** `/Users/chakeswu/cursor/MemguardV1/sdk/memguard/core/influence.py` (NEW)

**Purpose:** Calculate how much each memory operation influenced the final decision

**Algorithm:**

```python
"""
Influence Score Calculation

For each memory READ operation before a decision:
1. Base score = 1.0 (every read has base influence)
2. Similarity boost = similarity_score (for vector retrievals)
3. Recency boost = 1.0 / (1 + hours_since_read)
4. Type weight = {
     episodic: 1.2,    # Historical cases are highly influential
     semantic: 1.1,    # Regulations are important
     procedural: 1.0,  # SOPs are standard
     working: 0.9,     # Current state is context
   }

Final influence = base * (1 + similarity) * recency * type_weight
Normalized to [0, 1] range
"""

from typing import List, Dict
from datetime import datetime
import math

class InfluenceCalculator:
    """Calculate memory influence scores"""
    
    TYPE_WEIGHTS = {
        "episodic": 1.2,
        "semantic": 1.1,
        "procedural": 1.0,
        "working": 0.9,
        "user_preferences": 0.8,
    }
    
    @staticmethod
    def calculate_influence(
        memory_event: Dict,
        decision_time: datetime,
        similarity_score: float = None
    ) -> float:
        """
        Calculate influence score for a memory event
        
        Args:
            memory_event: Memory operation event
            decision_time: When the decision was made
            similarity_score: Similarity from vector search (0-1)
        
        Returns:
            Influence score (0-1)
        """
        # Base score
        base = 1.0
        
        # Similarity boost (for vector retrievals)
        similarity_boost = similarity_score if similarity_score else 0.0
        
        # Recency boost
        event_time = datetime.fromisoformat(memory_event["timestamp"])
        hours_diff = (decision_time - event_time).total_seconds() / 3600
        recency = 1.0 / (1.0 + hours_diff)
        
        # Memory type weight
        memory_type = memory_event.get("memory_type", "working")
        type_weight = InfluenceCalculator.TYPE_WEIGHTS.get(memory_type, 1.0)
        
        # Calculate final score
        influence = base * (1.0 + similarity_boost) * recency * type_weight
        
        # Normalize to [0, 1]
        normalized = min(influence, 1.0)
        
        return round(normalized, 2)
    
    @staticmethod
    def calculate_batch_influences(
        memory_events: List[Dict],
        decision_time: datetime
    ) -> List[Dict]:
        """
        Calculate influences for a batch of memory events
        
        Returns:
            List of events with influence_score field added
        """
        results = []
        
        for event in memory_events:
            # Extract similarity if available (from context)
            similarity = None
            if event.get("context"):
                similarities = event["context"].get("similarities", [])
                if similarities:
                    similarity = max(similarities)  # Use best match
            
            influence = InfluenceCalculator.calculate_influence(
                event, decision_time, similarity
            )
            
            results.append({
                **event,
                "influence_score": influence
            })
        
        return results
```

---

### Task 2.3: Extract Decision Reasoning from LLM Output

**File:** `/Users/chakeswu/cursor/MemguardV1/backend/app/reasoning_extractor.py` (NEW)

**Purpose:** Parse LLM output to extract structured decision reasoning

**Implementation:**

```python
"""
Decision Reasoning Extractor

Extracts structured reasoning from LLM outputs using pattern matching
and optional LLM-based summarization.
"""

import re
from typing import Dict, Optional


class ReasoningExtractor:
    """Extract decision reasoning from LLM outputs"""
    
    # Common decision patterns
    DECISION_PATTERNS = {
        "file_sar": r"(?i)(file|submit|recommend|require).*?(sar|suspicious activity report)",
        "clear": r"(?i)(clear|no action|dismiss|not suspicious)",
        "escalate": r"(?i)(escalate|review|investigate|require.*?review)",
        "approve": r"(?i)(approve|accept|confirm)",
        "reject": r"(?i)(reject|decline|deny)",
    }
    
    # Reasoning keywords
    REASONING_KEYWORDS = [
        "because", "due to", "based on", "given that", "considering",
        "since", "as", "reason", "violates", "matches", "indicates",
        "suggests", "shows", "demonstrates", "evidenced by"
    ]
    
    @staticmethod
    def extract_decision_type(llm_output: str) -> str:
        """
        Extract decision type from LLM output
        
        Args:
            llm_output: Raw LLM response text
            
        Returns:
            Decision type string
        """
        output_lower = llm_output.lower()
        
        for decision_type, pattern in ReasoningExtractor.DECISION_PATTERNS.items():
            if re.search(pattern, output_lower):
                return decision_type
        
        return "unknown"
    
    @staticmethod
    def extract_reasoning(llm_output: str, max_length: int = 500) -> str:
        """
        Extract reasoning sentences from LLM output
        
        Args:
            llm_output: Raw LLM response text
            max_length: Max reasoning text length
            
        Returns:
            Extracted reasoning text
        """
        sentences = re.split(r'[.!?]\s+', llm_output)
        reasoning_sentences = []
        
        for sentence in sentences:
            # Check if sentence contains reasoning keywords
            if any(keyword in sentence.lower() for keyword in ReasoningExtractor.REASONING_KEYWORDS):
                reasoning_sentences.append(sentence.strip())
        
        # Join and truncate
        reasoning = ". ".join(reasoning_sentences)
        if len(reasoning) > max_length:
            reasoning = reasoning[:max_length] + "..."
        
        return reasoning or "No explicit reasoning found in output."
    
    @staticmethod
    def extract_confidence(llm_output: str) -> float:
        """
        Extract confidence score from LLM output
        
        Looks for patterns like:
        - "confidence: 0.92"
        - "92% confident"
        - "high confidence" (maps to 0.85)
        
        Args:
            llm_output: Raw LLM response text
            
        Returns:
            Confidence score (0-1)
        """
        output_lower = llm_output.lower()
        
        # Look for numeric confidence
        numeric_match = re.search(r'confidence[:\s]+([0-9.]+)', output_lower)
        if numeric_match:
            try:
                score = float(numeric_match.group(1))
                # If > 1, assume it's percentage
                if score > 1:
                    score = score / 100.0
                return round(min(max(score, 0.0), 1.0), 2)
            except ValueError:
                pass
        
        # Look for percentage
        percent_match = re.search(r'([0-9]+)%\s*confident', output_lower)
        if percent_match:
            try:
                score = float(percent_match.group(1)) / 100.0
                return round(score, 2)
            except ValueError:
                pass
        
        # Look for qualitative confidence
        if "high confidence" in output_lower or "very confident" in output_lower:
            return 0.85
        elif "medium confidence" in output_lower or "moderately confident" in output_lower:
            return 0.65
        elif "low confidence" in output_lower or "uncertain" in output_lower:
            return 0.45
        
        # Default
        return 0.75
    
    @staticmethod
    def extract_full_reasoning(llm_output: str) -> Dict:
        """
        Extract full reasoning structure
        
        Returns:
            Dict with decision_type, reasoning, confidence
        """
        return {
            "decision_type": ReasoningExtractor.extract_decision_type(llm_output),
            "reasoning": ReasoningExtractor.extract_reasoning(llm_output),
            "confidence": ReasoningExtractor.extract_confidence(llm_output),
        }
```

---

### Task 2.4: Enhanced Decision Trace API Endpoint

**File:** `/Users/chakeswu/cursor/MemguardV1/backend/app/main.py`

**Add new endpoint:**

```python
@app.get("/v1/decision-traces/{trace_id}")
def get_decision_trace_detail(trace_id: str):
    """
    Get detailed decision trace with causal chain
    
    Returns:
        Full decision trace with:
        - Input memory influences (sorted by score)
        - Decision reasoning
        - Output memory operations
    """
    return gateway.get_decision_trace_detail(trace_id)
```

**File:** `/Users/chakeswu/cursor/MemguardV1/backend/app/services.py`

**Add method:**

```python
def get_decision_trace_detail(self, trace_id: str) -> Dict:
    """
    Get full decision trace details with causal chain
    
    Returns:
        Enhanced decision trace with influence scores
    """
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        
        # Get decision trace
        trace = conn.execute(
            "SELECT * FROM decision_traces WHERE trace_id = ?",
            (trace_id,)
        ).fetchone()
        
        if not trace:
            return {"error": "Trace not found"}
        
        # Get input memory events (before decision)
        input_events = conn.execute(
            """
            SELECT * FROM memory_events 
            WHERE session_id = ? 
              AND created_at <= ?
              AND event_type IN ('read', 'query', 'search')
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (trace["session_id"], trace["timestamp"])
        ).fetchall()
        
        # Calculate influences
        from app.reasoning_extractor import InfluenceCalculator
        decision_time = datetime.fromisoformat(trace["timestamp"])
        
        input_influences = InfluenceCalculator.calculate_batch_influences(
            [dict(e) for e in input_events],
            decision_time
        )
        
        # Sort by influence score
        input_influences.sort(key=lambda x: x["influence_score"], reverse=True)
        
        # Get output memory events (after decision)
        output_events = conn.execute(
            """
            SELECT * FROM memory_events 
            WHERE session_id = ?
              AND created_at >= ?
              AND event_type IN ('create', 'update')
            ORDER BY created_at ASC
            LIMIT 5
            """,
            (trace["session_id"], trace["timestamp"])
        ).fetchall()
        
        # Extract reasoning
        from app.reasoning_extractor import ReasoningExtractor
        reasoning_data = ReasoningExtractor.extract_full_reasoning(
            trace["llm_output"]
        )
        
        return {
            "trace_id": trace["trace_id"],
            "agent_id": trace["agent_id"],
            "session_id": trace["session_id"],
            "timestamp": trace["timestamp"],
            
            # Memory IN
            "input_memory_influences": [
                {
                    "event_id": e["event_id"],
                    "memory_key": e["memory_key"],
                    "memory_type": e["memory_type"],
                    "operation": e["event_type"],
                    "influence_score": e["influence_score"],
                    "content_preview": self._get_content_preview(e),
                    "timestamp": e["created_at"],
                }
                for e in input_influences[:5]  # Top 5
            ],
            "total_input_influence": sum(e["influence_score"] for e in input_influences[:5]),
            
            # Decision
            "decision_type": reasoning_data["decision_type"],
            "decision_confidence": reasoning_data["confidence"],
            "decision_reasoning": reasoning_data["reasoning"],
            "llm_output": trace["llm_output"],
            
            # Memory OUT
            "output_memory_influences": [
                {
                    "event_id": e["event_id"],
                    "memory_key": e["memory_key"],
                    "memory_type": e["memory_type"],
                    "operation": e["event_type"],
                    "content_hash": e["content_hash"],
                    "timestamp": e["created_at"],
                }
                for e in output_events
            ],
            
            # Metadata
            "user_input": trace.get("user_input"),
            "metadata": json.loads(trace["metadata"]) if trace.get("metadata") else {},
        }

def _get_content_preview(self, event: Dict, max_length: int = 100) -> str:
    """Get preview of memory content"""
    if event.get("after_value"):
        content = str(event["after_value"])
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
    return ""
```

---

### Task 2.5: Rich Terminal Formatter for Decision Traces

**File:** `/Users/chakeswu/cursor/MemguardV1/sdk/memguard/display/decision_trace.py` (NEW)

**Purpose:** Beautiful terminal display of decision traces

```python
"""
Decision Trace Terminal Display

Beautiful Rich-based formatting for decision traces
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing import Dict, List


class DecisionTraceDisplay:
    """Display decision traces in terminal"""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
    
    def render_influence_bar(self, score: float, width: int = 20) -> str:
        """Render influence score as visual bar"""
        filled = int(score * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"{bar} {score:.2f}"
    
    def display_decision_trace(self, trace: Dict) -> None:
        """
        Display full decision trace with causal chain
        
        Args:
            trace: Decision trace dict from API
        """
        self.console.print()
        
        # Header
        self.console.print(Panel.fit(
            f"[bold cyan]Decision Trace: {trace['agent_id']}[/bold cyan]\n"
            f"[dim]{trace['timestamp']}[/dim]",
            border_style="cyan"
        ))
        
        self.console.print()
        
        # Memory IN
        self._display_memory_in(trace["input_memory_influences"])
        
        self.console.print("\n" + " " * 30 + "[yellow]↓[/yellow]\n")
        
        # Agent Decision
        self._display_decision(
            trace["decision_type"],
            trace["decision_confidence"],
            trace["decision_reasoning"]
        )
        
        self.console.print("\n" + " " * 30 + "[yellow]↓[/yellow]\n")
        
        # Memory OUT
        self._display_memory_out(trace["output_memory_influences"])
        
        self.console.print()
    
    def _display_memory_in(self, influences: List[Dict]) -> None:
        """Display memory inputs with influence scores"""
        self.console.print("[bold white]MEMORY IN[/bold white]")
        self.console.print()
        
        for influence in influences:
            # Memory operation
            icon = "🔵" if influence["operation"] == "read" else "🔷"
            self.console.print(
                f"  {icon} [cyan]{influence['operation'].upper()}[/cyan]  "
                f"[blue]{influence['memory_type']}:{influence['memory_key']}[/blue]"
            )
            
            # Content preview
            if influence.get("content_preview"):
                self.console.print(
                    f"     [dim]\"{influence['content_preview']}\"[/dim]"
                )
            
            # Influence score bar
            bar = self.render_influence_bar(influence["influence_score"])
            self.console.print(
                f"     Influence: [green]{bar}[/green]"
            )
            
            self.console.print()
    
    def _display_decision(
        self, 
        decision_type: str, 
        confidence: float,
        reasoning: str
    ) -> None:
        """Display agent decision"""
        self.console.print("[bold white]AGENT DECISION[/bold white]")
        self.console.print()
        
        # Decision type
        decision_color = "red" if decision_type == "file_sar" else "green"
        self.console.print(
            f"  Decision: [{decision_color}]{decision_type.upper()}[/{decision_color}]"
        )
        
        # Confidence
        conf_bar = self.render_influence_bar(confidence)
        self.console.print(
            f"  Confidence: [yellow]{conf_bar}[/yellow]"
        )
        
        self.console.print()
        
        # Reasoning
        self.console.print("  [bold]Reasoning:[/bold]")
        for line in reasoning.split(". "):
            if line.strip():
                self.console.print(f"    • {line.strip()}")
        
        self.console.print()
    
    def _display_memory_out(self, outputs: List[Dict]) -> None:
        """Display memory outputs"""
        self.console.print("[bold white]MEMORY OUT[/bold white]")
        self.console.print()
        
        for output in outputs:
            icon = "🟢" if output["operation"] == "create" else "🟡"
            self.console.print(
                f"  {icon} [cyan]{output['operation'].upper()}[/cyan]  "
                f"[blue]{output['memory_type']}:{output['memory_key']}[/blue]"
            )
            
            if output.get("content_hash"):
                self.console.print(
                    f"     Hash: [dim]{output['content_hash'][:16]}...[/dim]"
                )
            
            self.console.print()
```

---

### Task 2.6: Testing Checklist

**Before marking Layer 2 complete:**

- [ ] Influence scores calculated correctly
- [ ] Influence scores range from 0-1
- [ ] Episodic memory gets higher weight
- [ ] Similarity scores boost influence
- [ ] Decision reasoning extracted from LLM output
- [ ] Decision type detected correctly
- [ ] Confidence score extracted
- [ ] API endpoint returns enhanced traces
- [ ] Terminal display shows causal chain clearly
- [ ] Influence bars render correctly
- [ ] Memory preview truncates long content

---

## Execution Prompt for Layer 2

**Prompt to give to Claude Code:**

```
I need you to implement Layer 2 of the MemGuard demo system: Decision Trace enhancement.

Read the architecture design: DEMO_ARCHITECTURE.md
Read this implementation guide: LAYER2_IMPLEMENTATION.md

Your tasks:
1. Create influence score calculation system
2. Create reasoning extractor for LLM outputs
3. Enhance decision trace API endpoint
4. Create beautiful terminal formatter for decision traces
5. Integrate with Layer 1 demo.py

Key files to create:
- /Users/chakeswu/cursor/MemguardV1/sdk/memguard/core/influence.py (NEW)
- /Users/chakeswu/cursor/MemguardV1/backend/app/reasoning_extractor.py (NEW)
- /Users/chakeswu/cursor/MemguardV1/sdk/memguard/display/decision_trace.py (NEW)

Key files to modify:
- /Users/chakeswu/cursor/MemguardV1/backend/app/schemas.py (add MemoryInfluence model)
- /Users/chakeswu/cursor/MemguardV1/backend/app/main.py (add decision trace detail endpoint)
- /Users/chakeswu/cursor/MemguardV1/backend/app/services.py (add get_decision_trace_detail method)
- /Users/chakeswu/cursor/MemguardV1/demo.py (integrate decision trace display)

Requirements:
- Influence scores range 0-1
- Memory type weights: episodic=1.2, semantic=1.1, procedural=1.0, working=0.9
- Similarity scores boost influence
- Decision reasoning extracted from LLM
- Beautiful terminal display with Rich
- Clear causal chain: Memory IN → Decision → Memory OUT

After implementation:
- Test with: python demo.py
- Verify decision traces show influence scores
- Verify reasoning is extracted correctly
- Show me the enhanced output
```

---

**End of Layer 2 Implementation Guide**
