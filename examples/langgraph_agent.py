"""
Working example: LangGraph agent with MemGuard memory observability.

This example demonstrates the KEY VALUE of MemGuard:
    1. ZERO changes to agent code — just swap the checkpointer
    2. Every memory read/write is automatically recorded
    3. Trace which memories influenced each decision
    4. Query the decision trace after the fact

To run:
    1. Install LangGraph: pip install langgraph langgraph-checkpoint
    2. pip install -e ../sdk
    3. Start MemGuard backend: cd ../backend && uvicorn app.main:app --reload
    4. python langgraph_agent.py
"""

from __future__ import annotations

import json
import sys
import os

# Add the sdk directory to the path so we can import memguard
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk'))

from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport import StdoutTransport, HttpTransport, FileTransport

# ============================================================================
# Part 1: Define a LangGraph agent — STANDARD code, nothing MemGuard-specific
# ============================================================================

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver


class AgentState(TypedDict):
    """Standard LangGraph state — nothing MemGuard-specific here."""
    messages: Annotated[list, add_messages]
    user_name: str
    user_preferences: dict


def greet_node(state: AgentState) -> dict:
    """Node 1: Greet the user using remembered info."""
    name = state.get("user_name", "there")
    prefs = state.get("user_preferences", {})
    lang = prefs.get("language", "English")

    greeting = f"Hello {name}! I see you prefer {lang}."

    # Store a new memory implicitly via state change
    return {
        "messages": [{"role": "assistant", "content": greeting}],
        "user_preferences": {**prefs, "greeted": True}
    }


def recommend_node(state: AgentState) -> dict:
    """Node 2: Make a recommendation based on remembered preferences."""
    prefs = state.get("user_preferences", {})
    language = prefs.get("language", "Python")
    framework = prefs.get("framework", "FastAPI")

    recommendation = (
        f"Based on your preferences ({language}, {framework}), "
        f"I recommend using {language} with {framework} for this project."
    )

    return {
        "messages": [{"role": "assistant", "content": recommendation}],
        "user_preferences": {**prefs, "last_recommendation": recommendation}
    }


def build_agent(checkpointer=None):
    """Build a standard LangGraph agent. MemGuard-agnostic."""
    graph = StateGraph(AgentState)
    graph.add_node("greet", greet_node)
    graph.add_node("recommend", recommend_node)
    graph.add_edge(START, "greet")
    graph.add_edge("greet", "recommend")
    graph.add_edge("recommend", END)
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# Part 2: Run WITHOUT MemGuard (baseline)
# ============================================================================

print("=" * 70)
print("  PART 1: Running agent WITHOUT MemGuard (baseline)")
print("=" * 70)

standard_checkpointer = MemorySaver()
standard_agent = build_agent(checkpointer=standard_checkpointer)

config = {"configurable": {"thread_id": "session-001"}}
initial_state = {
    "messages": [{"role": "user", "content": "Hi! What should I use?"}],
    "user_name": "Alice",
    "user_preferences": {"language": "Python", "framework": "FastAPI"}
}

print("\nRunning agent...")
result = standard_agent.invoke(initial_state, config)
for msg in result["messages"]:
    print(f"  [{msg['role']}]: {msg['content'][:100]}")

print("\n⚠️  No memory events recorded — can't trace decisions.")


# ============================================================================
# Part 3: Run WITH MemGuard (add 3 lines)
# ============================================================================

print("\n" + "=" * 70)
print("  PART 2: Running agent WITH MemGuard (3-line change)")
print("=" * 70)

# These 3 lines are the ONLY change needed:
mg_checkpointer = MemGuardCheckpointer(
    inner=MemorySaver(),                 # Original checkpointer unchanged
    agent_id="alice-agent",              # Identify this agent
    namespace="acme-corp",               # Tenant/org namespace
    transport=FileTransport("memguard_events.jsonl"),  # Record to file
)

mg_agent = build_agent(checkpointer=mg_checkpointer)
# Agent code is IDENTICAL to Part 1

config2 = {"configurable": {"thread_id": "session-002"}}
initial_state2 = {
    "messages": [{"role": "user", "content": "Hi! What tech should I use?"}],
    "user_name": "Alice",
    "user_preferences": {"language": "Python", "framework": "FastAPI"}
}

print("\nRunning agent (with MemGuard intercepting)...")
result2 = mg_agent.invoke(initial_state2, config2)
for msg in result2["messages"]:
    print(f"  [{msg['role']}]: {msg['content'][:100]}")

# ============================================================================
# Part 4: Read the recorded events
# ============================================================================

print("\n" + "=" * 70)
print("  PART 3: Recorded Memory Events (from JSONL file)")
print("=" * 70)

events_file = "memguard_events.jsonl"
if os.path.exists(events_file):
    events = []
    with open(events_file) as f:
        for line in f:
            events.append(json.loads(line))

    print(f"\nTotal events recorded: {len(events)}\n")

    for i, event in enumerate(events):
        op = event.get("operation", "unknown")
        key = event.get("memory_key", "")
        ts = event.get("timestamp", "")[:19]
        symbol = {"create": "✚", "read": "👁", "update": "✎", "query": "🔍"}.get(op, "?")
        print(f"  [{i+1}] {symbol} {op.upper():8s} | {key:40s} | {ts}")

    # Show which operations happened in order
    print("\n" + "-" * 70)
    print("  Memory operation timeline:")
    print("  The agent READ checkpoint state, then UPDATED it after each node.")
    print("  This gives us full visibility into the agent's memory behavior.")
    print("-" * 70)

    # Calculate operations per type
    from collections import Counter
    op_counts = Counter(e["operation"] for e in events)
    print(f"\n  Operations by type:")
    for op, count in op_counts.items():
        print(f"    {op}: {count}")
else:
    print("  No events file found (expected if transport failed)")

# ============================================================================
# Part 5: Show what MemGuard captured
# ============================================================================

print("\n" + "=" * 70)
print("  PART 4: What MemGuard Tells You")
print("=" * 70)

print("""
  With MemGuard, you can now answer questions like:

  1. "What state did the agent read before making its recommendation?"
     → Check the READ events before the recommend_node

  2. "How did the agent's memory change during this session?"
     → Compare CREATE/UPDATE events in timeline order

  3. "Which node wrote which memory?"
     → Each event has metadata tying it to the graph execution

  4. "Did the agent actually use the remembered user_preferences?"
     → Check if READ events for user_preferences appear before the output

  All of this WITHOUT modifying the agent code.
  Just swap MemorySaver() → MemGuardCheckpointer(inner=MemorySaver(), ...)
""")

# Cleanup
if os.path.exists(events_file):
    os.remove(events_file)

print("Done! ✅")
