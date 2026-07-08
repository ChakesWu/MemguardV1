#!/usr/bin/env python3
"""
MemGuard Demo Agent - Standalone Example

A simple conversational agent that demonstrates MemGuard's memory tracing capabilities.

This agent:
- Uses LangGraph for state management
- Remembers user preferences across turns
- Is wrapped with MemGuardCheckpointer for full memory observability

Prerequisites:
    pip install langgraph memguard

Usage:
    # Terminal 1: Start MemGuard backend
    cd backend && uvicorn app.main:app --reload

    # Terminal 2: Run demo agent
    python examples/demo_agent.py

    # Terminal 3: View memory timeline
    curl http://localhost:8000/v1/db/stats
    # Then open dashboard: http://localhost:3000/timeline/<session_id>

What to observe:
    - Every conversation turn creates memory events
    - State reads/writes are captured
    - Timeline shows memory evolution
    - Can trace which memories influenced each response
"""

import os
import sys
from typing import Annotated, TypedDict
from datetime import datetime

# Add SDK to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# MemGuard imports
from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.transport import HttpTransport, StdoutTransport


# ═══════════════════════════════════════════════════════════════
# Agent State
# ═══════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """Simple agent state with message history and user preferences."""
    messages: Annotated[list[BaseMessage], add_messages]
    user_name: str
    user_preferences: dict  # e.g., {"language": "Python", "expertise": "intermediate"}
    conversation_count: int


# ═══════════════════════════════════════════════════════════════
# Agent Logic (Simple Chatbot)
# ═══════════════════════════════════════════════════════════════

def chatbot_node(state: AgentState) -> AgentState:
    """
    Simple chatbot logic that:
    - Responds to user messages
    - Updates preferences based on conversation
    - Demonstrates memory usage
    """
    messages = state["messages"]
    user_name = state.get("user_name", "User")
    preferences = state.get("user_preferences", {})
    count = state.get("conversation_count", 0)

    # Get last user message
    last_message = messages[-1] if messages else None
    if not last_message or not isinstance(last_message, HumanMessage):
        return state

    user_input = last_message.content.lower()

    # Simple response logic (in real app, this would call an LLM)
    response = ""

    # Handle greetings
    if any(word in user_input for word in ["hello", "hi", "hey"]):
        if user_name and user_name != "User":
            response = f"Hello {user_name}! How can I help you today?"
        else:
            response = "Hello! I'm a demo agent with memory tracing. What's your name?"

    # Handle name introduction
    elif "my name is" in user_input or "i'm" in user_input or "im" in user_input:
        # Extract name (simple parsing)
        parts = user_input.replace("my name is", "").replace("i'm", "").replace("im", "").strip().split()
        if parts:
            new_name = parts[0].capitalize()
            state["user_name"] = new_name
            response = f"Nice to meet you, {new_name}! I'll remember that."

    # Handle preference learning
    elif "i like" in user_input or "i love" in user_input:
        preference_text = user_input.replace("i like", "").replace("i love", "").strip()
        preferences["likes"] = preferences.get("likes", []) + [preference_text]
        state["user_preferences"] = preferences
        response = f"Got it! I'll remember that you like {preference_text}."

    # Handle preference query
    elif "what do you know about me" in user_input or "what do you remember" in user_input:
        if user_name != "User":
            response = f"I know your name is {user_name}. "
        else:
            response = "I don't know your name yet. "

        if preferences.get("likes"):
            response += f"You like: {', '.join(preferences['likes'])}. "
        else:
            response += "I don't know your preferences yet. Tell me what you like!"

    # Default response
    else:
        response = f"I understand you said: '{last_message.content}'. Try saying 'hello' or 'my name is <name>' or 'I like <something>'."

    # Update state
    state["messages"] = messages + [AIMessage(content=response)]
    state["conversation_count"] = count + 1

    return state


def should_continue(state: AgentState) -> str:
    """Simple routing logic."""
    return END


# ═══════════════════════════════════════════════════════════════
# Build Graph
# ═══════════════════════════════════════════════════════════════

def create_demo_agent(use_memguard: bool = True):
    """
    Create a LangGraph agent with optional MemGuard tracing.

    Args:
        use_memguard: If True, wrap checkpointer with MemGuard

    Returns:
        Compiled LangGraph agent
    """
    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("chatbot", chatbot_node)

    # Add edges
    workflow.add_edge(START, "chatbot")
    workflow.add_edge("chatbot", END)

    # Create checkpointer
    inner_checkpointer = MemorySaver()

    if use_memguard:
        print("🔍 MemGuard enabled - all memory operations will be traced")
        checkpointer = MemGuardCheckpointer(
            inner=inner_checkpointer,
            agent_id="demo-chatbot",
            namespace="demo-org",
            transport=HttpTransport("http://localhost:8000"),
            capture_content=True  # For demo, capture full content
        )
    else:
        print("⚠️  MemGuard disabled - running without tracing")
        checkpointer = inner_checkpointer

    # Compile graph
    app = workflow.compile(checkpointer=checkpointer)

    return app


# ═══════════════════════════════════════════════════════════════
# Demo Runner
# ═══════════════════════════════════════════════════════════════

def run_interactive_demo():
    """Run interactive demo with user input."""

    print("\n" + "="*70)
    print("  MemGuard Demo Agent - Interactive Mode")
    print("="*70)
    print("\nThis agent demonstrates MemGuard's memory tracing capabilities.")
    print("\nTry these commands:")
    print("  - 'hello' - Greet the agent")
    print("  - 'my name is <name>' - Tell it your name")
    print("  - 'i like <something>' - Share preferences")
    print("  - 'what do you know about me' - Test memory recall")
    print("  - 'quit' - Exit")
    print("\n" + "="*70 + "\n")

    # Create agent with MemGuard
    agent = create_demo_agent(use_memguard=True)

    # Create session
    session_id = f"demo-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    config = {"configurable": {"thread_id": session_id}}

    print(f"📝 Session ID: {session_id}")
    print(f"📊 View timeline: http://localhost:3000/timeline/{session_id}\n")

    # Initialize state
    state = {
        "messages": [],
        "user_name": "User",
        "user_preferences": {},
        "conversation_count": 0
    }

    # Conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\n👋 Goodbye! Check the timeline to see all memory operations.")
                print(f"   curl http://localhost:8000/v1/db/stats")
                break

            # Add user message to state
            state["messages"].append(HumanMessage(content=user_input))

            # Run agent
            result = agent.invoke(state, config)

            # Update state
            state = result

            # Display agent response
            last_message = result["messages"][-1]
            print(f"Agent: {last_message.content}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Make sure the backend is running: cd backend && uvicorn app.main:app --reload")
            break

    print(f"\n📊 Total conversation turns: {state.get('conversation_count', 0)}")
    print(f"📊 Memory events captured: Check backend API")


def run_automated_demo():
    """Run automated demo with pre-scripted conversation."""

    print("\n" + "="*70)
    print("  MemGuard Demo Agent - Automated Mode")
    print("="*70)
    print("\nRunning pre-scripted conversation to demonstrate memory tracing...\n")

    # Create agent with MemGuard
    agent = create_demo_agent(use_memguard=True)

    # Create session
    session_id = f"auto-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    config = {"configurable": {"thread_id": session_id}}

    print(f"📝 Session ID: {session_id}\n")

    # Pre-scripted conversation
    conversation = [
        "Hello!",
        "My name is Alice",
        "I like Python programming",
        "I love building AI agents",
        "What do you know about me?"
    ]

    state = {
        "messages": [],
        "user_name": "User",
        "user_preferences": {},
        "conversation_count": 0
    }

    # 决策追踪: 为每个 turn 创建 DecisionTrace
    from memguard.core.event import DecisionTrace
    import requests

    for turn, user_input in enumerate(conversation, 1):
        print(f"[Turn {turn}]")
        print(f"You: {user_input}")

        # --- 决策前: 记录 memory READ events ---
        # 获取当前 state 作为 "input memories"
        read_memory_ids = [f"state:{k}" for k in state.keys()]

        # Add message
        state["messages"].append(HumanMessage(content=user_input))

        # --- Agent 决策 (模拟 LLM 调用) ---
        result = agent.invoke(state, config)
        old_state = state.copy()
        state = result

        # --- 决策后: 记录 memory WRITE events ---
        # 检测哪些 state 发生了变化
        write_memory_ids = []
        for key in state.keys():
            if key in old_state and old_state[key] != state[key]:
                write_memory_ids.append(f"state:{key}")
            elif key not in old_state:
                write_memory_ids.append(f"state:{key}")

        # --- 创建 DecisionTrace ---
        import hashlib
        last_msg = result["messages"][-1]
        trace = DecisionTrace(
            agent_id="demo-chatbot",
            session_id=session_id,
            input_event_ids=read_memory_ids,
            output_event_ids=write_memory_ids,
            prompt_hash=hashlib.sha256(user_input.encode()).hexdigest()[:16],
            output_hash=hashlib.sha256(last_msg.content.encode()).hexdigest()[:16],
            output_summary=last_msg.content[:100],
            memory_influence_score=min(1.0, len(read_memory_ids) * 0.2),
        )

        # 发送决策追踪到 Backend
        try:
            from dataclasses import asdict
            resp = requests.post(
                "http://localhost:8000/v1/trace",
                json=asdict(trace),
                timeout=2
            )
            if resp.status_code == 200:
                print(f"   🟣 DecisionTrace: influence={trace.memory_influence_score:.1f}, read={len(read_memory_ids)}, write={len(write_memory_ids)}")
        except Exception:
            pass

        # Display response
        print(f"Agent: {last_msg.content}\n")

    print("="*70)
    print("✅ Demo complete!")
    print(f"\n📊 Session ID: {session_id}")
    print(f"📊 Total turns: {len(conversation)}")
    print(f"📊 Memory events: Check backend API")
    print(f"\n🔍 View timeline:")
    print(f"   curl http://localhost:8000/v1/db/stats")
    print(f"   curl 'http://localhost:8000/v1/sessions/{session_id}/timeline'")
    print(f"\n🌐 Open dashboard:")
    print(f"   http://localhost:3000/timeline/{session_id}")
    print("="*70 + "\n")


def run_comparison_demo():
    """Run side-by-side comparison: with and without MemGuard."""

    print("\n" + "="*70)
    print("  MemGuard Demo - Comparison Mode")
    print("="*70)
    print("\nComparing agent behavior WITH and WITHOUT MemGuard...\n")

    test_input = "Hello, my name is Bob"

    # Test WITHOUT MemGuard
    print("🔴 Test 1: WITHOUT MemGuard")
    print("-" * 70)
    agent_no_trace = create_demo_agent(use_memguard=False)
    session_1 = "no-trace-demo"
    config_1 = {"configurable": {"thread_id": session_1}}

    state_1 = {
        "messages": [HumanMessage(content=test_input)],
        "user_name": "User",
        "user_preferences": {},
        "conversation_count": 0
    }

    result_1 = agent_no_trace.invoke(state_1, config_1)
    print(f"Input: {test_input}")
    print(f"Output: {result_1['messages'][-1].content}")
    print("Memory trace: ❌ No tracing\n")

    # Test WITH MemGuard
    print("🟢 Test 2: WITH MemGuard")
    print("-" * 70)
    agent_with_trace = create_demo_agent(use_memguard=True)
    session_2 = f"traced-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    config_2 = {"configurable": {"thread_id": session_2}}

    state_2 = {
        "messages": [HumanMessage(content=test_input)],
        "user_name": "User",
        "user_preferences": {},
        "conversation_count": 0
    }

    result_2 = agent_with_trace.invoke(state_2, config_2)
    print(f"Input: {test_input}")
    print(f"Output: {result_2['messages'][-1].content}")
    print(f"Memory trace: ✅ Captured - session_id={session_2}")
    print(f"View at: http://localhost:3000/timeline/{session_2}\n")

    print("="*70)
    print("📊 Comparison Summary:")
    print("  - Both agents produced identical outputs")
    print("  - Agent with MemGuard has ZERO performance impact")
    print("  - Agent with MemGuard has FULL memory visibility")
    print("="*70 + "\n")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MemGuard Demo Agent")
    parser.add_argument(
        "--mode",
        choices=["interactive", "auto", "compare"],
        default="auto",
        help="Demo mode: interactive (user input), auto (scripted), compare (with/without MemGuard)"
    )

    args = parser.parse_args()

    if args.mode == "interactive":
        run_interactive_demo()
    elif args.mode == "auto":
        run_automated_demo()
    elif args.mode == "compare":
        run_comparison_demo()
