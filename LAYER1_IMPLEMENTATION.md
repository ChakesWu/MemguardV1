# Layer 1 Implementation Guide

**Goal:** `python demo.py` runs complete FinCompli Scenario 02 with beautiful terminal output

**Priority:** 🔥 CRITICAL - This is the foundation for everything

---

## Implementation Tasks

### Task 1.1: Create Demo Entry Point

**File:** `/Users/chakeswu/cursor/MemguardV1/demo.py`

**Requirements:**
1. Single command execution: `python demo.py`
2. Works with local Qwen model (http://localhost:8080)
3. Runs FinCompli Scenario 02 (Structuring case)
4. Beautiful Rich terminal output
5. Completes in ~60 seconds

**Key Features:**
- Auto-detect and connect to:
  - Local Qwen (port 8080)
  - MemGuard backend (port 8000)
  - FinCompli memory stores (ChromaDB + SQLite)
- Display real-time memory events with colors
- Show decision traces with influence scores
- Display final summary with business narrative

**Dependencies:**
```python
# Core
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Rich for terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout

# MemGuard SDK
from memguard import MemGuardInterceptor
from memguard.transport.http import HttpTransport

# FinCompli
sys.path.insert(0, str(Path(__file__).parent / "fincompli-baseline"))
from cli.interactive import run_scenario
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.procedural import ProceduralMemory
```

**Code Structure:**
```python
def check_qwen() -> bool:
    """Check if local Qwen is running on port 8080"""
    
def check_backend() -> bool:
    """Check if MemGuard backend is running on port 8000"""
    
def setup_memguard() -> MemGuardInterceptor:
    """Initialize MemGuard with HTTP transport"""
    
def setup_fincompli_with_memguard(interceptor):
    """Wrap all FinCompli memory layers with MemGuard"""
    
def display_scenario_intro():
    """Display scenario description with Rich panels"""
    
def run_scenario_with_live_display():
    """Run scenario with real-time event display"""
    
def display_decision_trace(trace_data):
    """Display decision trace with influence scores"""
    
def display_summary(stats, final_decision):
    """Display final summary table"""
    
def main():
    """Main entry point"""
```

**Expected Output:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  MemGuard × FinCompli                                       │
│  Enterprise Compliance Demo                                 │
│                                                             │
│  Demonstrating AI memory observability in a real-world     │
│  financial compliance scenario                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

✅ Local Qwen detected (http://localhost:8080)
✅ MemGuard backend connected (http://localhost:8000)
✅ FinCompli memory stores initialized

┌─ Scenario 02: Structuring Detection ────────────────────────┐
│                                                             │
│  Customer: LEE Wai Ming (ID: CUST-8472)                    │
│  Transaction Pattern: Multiple structured deposits          │
│                                                             │
│  • 2024-07-08: HKD 490,000 (Central Branch)                │
│  • 2024-07-09: HKD 490,000 (Wan Chai Branch)               │
│  • 2024-07-10: HKD 490,000 (Causeway Bay Branch)           │
│                                                             │
│  Total: HKD 1,470,000 split into 3 × 490K                  │
│  Threshold: HKD 500,000 (HKMA reporting requirement)       │
│                                                             │
│  Question: Is this structuring to avoid reporting?          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Running Analysis... ⠋

┌─ Stage 1: Parallel Analysis ─────────────────────────────────┐
│                                                             │
│ [fraud_detection] Analyzing transaction pattern             │
│   🔵 READ    episodic:customer_history                     │
│   🤖 LLM     Qwen analysis...                              │
│   🟢 CREATE  working:fraud_analysis                        │
│              Risk Score: 0.89 (CRITICAL)                   │
│                                                             │
│ [case_history] Searching similar cases                      │
│   🔷 QUERY   episodic:sar_cases                           │
│              Retrieved 3 matches:                          │
│              • SAR-2024-0033 (similarity: 0.88) ⭐        │
│              • SAR-2024-0019 (similarity: 0.72)           │
│              • SAR-2024-0008 (similarity: 0.61)           │
│   🟢 CREATE  working:case_history_analysis                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Stage 2: Compliance Research ───────────────────────────────┐
│                                                             │
│ [compliance_research] Querying regulations                  │
│   🔷 QUERY   semantic:regulations                         │
│              Retrieved 2 regulations:                      │
│              • HKMA §35: STR Reporting Threshold          │
│              • FATF Recommendation 10: Structuring        │
│   🟢 CREATE  working:compliance_findings                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Stage 3: Report Generation ─────────────────────────────────┐
│                                                             │
│ [report_generation] Synthesizing SAR report                 │
│   🔵 READ    working:fraud_analysis                        │
│   🔵 READ    working:case_history_analysis                │
│   🔵 READ    working:compliance_findings                  │
│   🤖 LLM     Generating report...                          │
│   🟢 CREATE  working:sar_report                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─ Decision Trace: Report Generation ──────────────────────────┐
│                                                             │
│ MEMORY IN (Influence Score: 2.53)                          │
│                                                             │
│   episodic:sar_cases                                        │
│   "SAR-2024-0033: Customer structured HKD 1.2M across..."  │
│   Influence: ██████████████████░░ 0.88                     │
│                                                             │
│   semantic:regulations                                      │
│   "HKMA §35: Financial institutions must file STR for..."  │
│   Influence: ███████████████░░░░░ 0.76                     │
│                                                             │
│   working:fraud_analysis                                    │
│   "Risk Score: 0.89 - CRITICAL fraud indicators detected"  │
│   Influence: ██████████████████░░ 0.89                     │
│                                                             │
│                              ↓                              │
│                                                             │
│ AGENT DECISION                                              │
│                                                             │
│   Decision: FILE SAR (Suspicious Activity Report)          │
│   Confidence: HIGH (0.92)                                   │
│                                                             │
│   Reasoning:                                                │
│   • Pattern matches historical case SAR-2024-0033          │
│   • Violates HKMA §35 reporting threshold                 │
│   • Fraud score exceeds critical threshold                 │
│   • Requires immediate compliance review                   │
│                                                             │
│                              ↓                              │
│                                                             │
│ MEMORY OUT                                                  │
│                                                             │
│   working:sar_report                                        │
│   Content Hash: 7f3a9b2c...                                │
│   Size: 2.4 KB                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘

✅ Analysis Complete (8.3 seconds)

┌─ Summary ────────────────────────────────────────────────────┐
│                                                             │
│ Metric                          Value                       │
│ ────────────────────────────────────────────────────────   │
│ Total Memory Events             11                          │
│ Decision Traces                 4                           │
│ Agents Involved                 4                           │
│ Memory Types Used               5                           │
│ Analysis Time                   8.3s                        │
│                                                             │
│ Final Decision                  FILE SAR                    │
│ Risk Level                      CRITICAL (0.93)             │
│ Status                          Awaiting Human Review       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

🎯 Business Outcome:
   AI Agent successfully detected structuring pattern and 
   recommended filing Suspicious Activity Report (SAR).
   
   The decision was based on:
   • 88% similarity to historical confirmed case
   • Clear violation of HKMA reporting threshold
   • Critical fraud risk score (0.89)

🔍 View Full Dashboard: http://localhost:3001
📊 View API Docs: http://localhost:8000/docs

💡 What makes this special?
   Without MemGuard: "AI flagged it. Why? Unknown."
   With MemGuard: Complete decision trace with memory evidence.
```

---

### Task 1.2: Integrate MemGuard with FinCompli Memory Layers

**File:** Create `/Users/chakeswu/cursor/MemguardV1/fincompli-baseline/memguard_wrappers.py`

**Purpose:** Wrap all 5 FinCompli memory types with MemGuard interceptor

**Code:**
```python
"""
MemGuard Wrappers for FinCompli Memory Layers

Wraps all 5 memory types:
1. Episodic (ChromaDB) - Historical cases
2. Semantic (ChromaDB) - Regulations
3. Procedural (SQLite) - SOP rules
4. Working (LangGraph) - Thread state
5. User Preferences (SQLite) - Officer settings
"""

from typing import Any, Dict, List, Optional
from memguard import MemGuardInterceptor, MemoryOp, MemoryType


class MemGuardEpisodicWrapper:
    """Wraps episodic memory (ChromaDB) with MemGuard tracking"""
    
    def __init__(self, inner, interceptor: MemGuardInterceptor):
        self.inner = inner
        self.interceptor = interceptor
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query similar cases"""
        # Record QUERY operation
        self.interceptor.record(
            operation=MemoryOp.QUERY,
            memory_key="sar_cases",
            memory_type=MemoryType.EPISODIC,
            context={
                "query": query_text,
                "top_k": top_k
            }
        )
        
        # Execute actual query
        results = self.inner.query(query_text, top_k)
        
        # Record retrieval results with similarity scores
        self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key="sar_cases",
            memory_type=MemoryType.EPISODIC,
            after_value={
                "results": results,
                "count": len(results)
            },
            context={
                "similarities": [r.get("similarity", 0) for r in results]
            }
        )
        
        return results
    
    def add(self, case_id: str, content: Dict) -> None:
        """Add new case to episodic memory"""
        self.interceptor.record(
            operation=MemoryOp.CREATE,
            memory_key=f"sar_case:{case_id}",
            memory_type=MemoryType.EPISODIC,
            after_value=content
        )
        self.inner.add(case_id, content)


class MemGuardSemanticWrapper:
    """Wraps semantic memory (ChromaDB) with MemGuard tracking"""
    
    def __init__(self, inner, interceptor: MemGuardInterceptor):
        self.inner = inner
        self.interceptor = interceptor
    
    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """Query regulations"""
        self.interceptor.record(
            operation=MemoryOp.QUERY,
            memory_key="regulations",
            memory_type=MemoryType.SEMANTIC,
            context={
                "query": query_text,
                "top_k": top_k
            }
        )
        
        results = self.inner.query(query_text, top_k)
        
        self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key="regulations",
            memory_type=MemoryType.SEMANTIC,
            after_value={
                "results": results,
                "count": len(results)
            },
            context={
                "similarities": [r.get("similarity", 0) for r in results]
            }
        )
        
        return results


class MemGuardProceduralWrapper:
    """Wraps procedural memory (SQLite) with MemGuard tracking"""
    
    def __init__(self, inner, interceptor: MemGuardInterceptor):
        self.inner = inner
        self.interceptor = interceptor
    
    def get_rule(self, rule_name: str) -> Optional[Dict]:
        """Get SOP rule"""
        self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key=f"rule:{rule_name}",
            memory_type=MemoryType.PROCEDURAL
        )
        
        rule = self.inner.get_rule(rule_name)
        
        if rule:
            self.interceptor.record(
                operation=MemoryOp.READ,
                memory_key=f"rule:{rule_name}",
                memory_type=MemoryType.PROCEDURAL,
                after_value=rule
            )
        
        return rule


class MemGuardWorkingWrapper:
    """Wraps working memory (LangGraph state) with MemGuard tracking"""
    
    def __init__(self, interceptor: MemGuardInterceptor):
        self.interceptor = interceptor
        self.data = {}
    
    def write(self, key: str, value: Any) -> None:
        """Write to working memory"""
        before = self.data.get(key)
        self.data[key] = value
        
        operation = MemoryOp.UPDATE if before else MemoryOp.CREATE
        
        self.interceptor.record(
            operation=operation,
            memory_key=key,
            memory_type=MemoryType.WORKING,
            before_value={"value": before} if before else None,
            after_value={"value": value}
        )
    
    def read(self, key: str) -> Any:
        """Read from working memory"""
        value = self.data.get(key)
        
        self.interceptor.record(
            operation=MemoryOp.READ,
            memory_key=key,
            memory_type=MemoryType.WORKING,
            after_value={"value": value} if value else None
        )
        
        return value
```

---

### Task 1.3: Enhanced Terminal Output with Rich

**Key Components:**

1. **Color Scheme:**
```python
OP_COLORS = {
    "create": "green",
    "read": "blue",
    "update": "yellow",
    "delete": "red",
    "query": "cyan",
}

OP_ICONS = {
    "create": "🟢",
    "read": "🔵",
    "update": "🟡",
    "delete": "🔴",
    "query": "🔷",
}

MEMORY_TYPE_COLORS = {
    "episodic": "blue",
    "semantic": "purple",
    "procedural": "cyan",
    "working": "white",
    "user_preferences": "magenta",
}
```

2. **Live Display Update:**
```python
from rich.live import Live
from rich.layout import Layout

def create_live_display():
    """Create live updating layout"""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="events", ratio=2),
        Layout(name="stats", size=8),
    )
    return layout

def update_display(layout, events, stats):
    """Update live display with new events"""
    layout["header"].update(Panel("MemGuard × FinCompli Demo", style="cyan"))
    layout["events"].update(render_events(events))
    layout["stats"].update(render_stats(stats))
```

3. **Influence Score Bar:**
```python
def render_influence_bar(score: float, width: int = 20) -> str:
    """Render influence score as visual bar"""
    filled = int(score * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return f"{bar} {score:.2f}"
```

---

### Task 1.4: Testing Checklist

**Before marking Layer 1 complete:**

- [ ] `python demo.py` runs without errors
- [ ] Local Qwen connection detected (port 8080)
- [ ] MemGuard backend connection detected (port 8000)
- [ ] All 5 memory types instrumented
- [ ] Memory events display in real-time with colors
- [ ] Decision trace shows influence scores
- [ ] Final summary displays correctly
- [ ] Complete in <60 seconds
- [ ] Output is beautiful and clear
- [ ] Business narrative is compelling

---

## Execution Prompt for Layer 1

**Prompt to give to Claude Code:**

```
I need you to implement Layer 1 of the MemGuard demo system.

Read the architecture design: DEMO_ARCHITECTURE.md
Read this implementation guide: LAYER1_IMPLEMENTATION.md

Your tasks:
1. Create demo.py as the main entry point
2. Create fincompli-baseline/memguard_wrappers.py to wrap all 5 memory types
3. Integrate MemGuard SDK with FinCompli Scenario 02
4. Implement beautiful Rich-based terminal output
5. Test the complete flow

Requirements:
- Single command: python demo.py
- Works with local Qwen (http://localhost:8080)
- Runs FinCompli Scenario 02 (Structuring case)
- Beautiful colored terminal output with Rich
- Shows all memory operations in real-time
- Displays decision trace with influence scores
- Completes in ~60 seconds

Key files to create/modify:
- /Users/chakeswu/cursor/MemguardV1/demo.py (NEW)
- /Users/chakeswu/cursor/MemguardV1/fincompli-baseline/memguard_wrappers.py (NEW)
- /Users/chakeswu/cursor/MemguardV1/fincompli-baseline/run_with_memguard.py (MODIFY)

After implementation:
- Test with: python demo.py
- Verify all checklist items
- Show me the terminal output
```

---

**End of Layer 1 Implementation Guide**
