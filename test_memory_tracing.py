#!/usr/bin/env python3
"""
Test script demonstrating MemGuard's core memory tracing functionality.

This script shows:
1. How to write memories to the agent
2. How to run the agent with those memories
3. How to trace which memories influenced each decision
4. How to see the memory influence scores
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
TENANT_ID = "test-tenant"
AGENT_ID = "test-agent"
SESSION_ID = "session-001"


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def write_memory(content: str, source_type: str = "system"):
    """Write a memory to the agent."""
    response = requests.post(
        f"{BASE_URL}/v1/memory/write",
        json={
            "tenant_id": TENANT_ID,
            "agent_id": AGENT_ID,
            "content": content,
            "source_type": source_type,
            "session_id": SESSION_ID
        }
    )
    return response.json()


def run_agent(user_input: str):
    """Run the agent with user input."""
    response = requests.post(
        f"{BASE_URL}/v1/agent/run",
        json={
            "tenant_id": TENANT_ID,
            "agent_id": AGENT_ID,
            "input": user_input,
            "session_id": SESSION_ID
        }
    )
    return response.json()


def get_decision_trace(trace_id: str):
    """Get the decision trace for a specific trace_id."""
    response = requests.get(f"{BASE_URL}/v1/trace/{trace_id}")
    return response.json()


def get_memory_influence(memory_id: str):
    """Get the influence history for a specific memory."""
    response = requests.get(f"{BASE_URL}/v1/memory/{memory_id}/influence")
    return response.json()


def main():
    print_section("MemGuard Memory Tracing Demo")

    # Step 1: Seed some memories
    print_section("Step 1: Writing memories to agent")

    memories = [
        "The user's name is Alice and she works as a software engineer",
        "Alice prefers Python over JavaScript for backend development",
        "Alice is currently working on a microservices project using FastAPI",
        "Alice mentioned she has 5 years of experience in distributed systems",
        "Alice's favorite database is PostgreSQL"
    ]

    memory_ids = []
    for mem in memories:
        result = write_memory(mem, source_type="system")
        memory_ids.append(result["memory_id"])
        print(f"✓ Memory written: {mem[:60]}...")
        print(f"  Memory ID: {result['memory_id']}")
        print(f"  Trust Score: {result['event']['trust_score']}")

    time.sleep(0.5)  # Small delay for clarity

    # Step 2: Run agent with a question
    print_section("Step 2: Running agent with user question")

    user_question = "What programming language does the user prefer for backend work?"
    print(f"User Question: {user_question}\n")

    agent_result = run_agent(user_question)

    print(f"Agent Answer: {agent_result['answer']}\n")
    print(f"Trace ID: {agent_result['trace_id']}")
    print(f"Retrieved {len(agent_result['retrieved_memory_ids'])} memories")

    # Step 3: Examine the decision trace
    print_section("Step 3: Analyzing Decision Trace")

    trace_id = agent_result['trace_id']
    trace = get_decision_trace(trace_id)

    print(f"Trace ID: {trace['trace_id']}")
    print(f"Timestamp: {trace['timestamp']}")
    print(f"User Input: {trace['user_input']}")
    print(f"LLM Model: {trace['llm_model']}")
    print(f"\nTotal Influence Score: {trace['total_influence_score']} (0=no memory, 1=heavily influenced)\n")

    print("Memory Influence Breakdown:")
    print("-" * 80)

    # Sort memories by influence score
    influence_scores = trace['memory_influence_scores']
    sorted_influences = sorted(influence_scores.items(), key=lambda x: x[1], reverse=True)

    for memory_id, score in sorted_influences:
        print(f"  Memory ID: {memory_id}")
        print(f"  Influence Score: {score:.3f}")

        # Find the actual memory content
        for i, mid in enumerate(memory_ids):
            if mid == memory_id:
                print(f"  Content: {memories[i]}")
                break
        print()

    # Step 4: Check memory influence history
    print_section("Step 4: Memory Influence History")

    # Pick the most influential memory
    if sorted_influences:
        top_memory_id = sorted_influences[0][0]
        print(f"Checking influence history for memory: {top_memory_id}\n")

        influence_history = get_memory_influence(top_memory_id)

        print(f"This memory has influenced {influence_history['total_influences']} decision(s)")
        print("-" * 80)

        for decision in influence_history['decisions']:
            print(f"\nDecision Trace ID: {decision['trace_id']}")
            print(f"Timestamp: {decision['timestamp']}")
            print(f"User Input: {decision['user_input']}")
            print(f"Influence Score: {decision['influence_score']:.3f}")
            print(f"Total Memories Used: {decision['total_memories_used']}")
            print(f"Output Preview: {decision['llm_output_preview']}")

    # Step 5: Run another question to see different influence patterns
    print_section("Step 5: Running another agent query")

    user_question_2 = "Tell me about the user's database preferences"
    print(f"User Question: {user_question_2}\n")

    agent_result_2 = run_agent(user_question_2)

    print(f"Agent Answer: {agent_result_2['answer']}\n")
    print(f"Trace ID: {agent_result_2['trace_id']}")

    trace_2 = get_decision_trace(agent_result_2['trace_id'])
    print(f"\nTotal Influence Score: {trace_2['total_influence_score']}")
    print("\nMemory Influence Scores:")
    for memory_id, score in sorted(trace_2['memory_influence_scores'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {memory_id}: {score:.3f}")

    print_section("Demo Complete!")
    print("✓ Demonstrated memory write")
    print("✓ Demonstrated agent decision-making with memory")
    print("✓ Demonstrated decision trace analysis")
    print("✓ Demonstrated memory influence scoring")
    print("✓ Demonstrated memory influence history tracking")
    print("\nYou can now trace exactly which memories influenced each agent decision!")


if __name__ == "__main__":
    try:
        # Check if server is running
        requests.get(f"{BASE_URL}/health", timeout=2)
        main()
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to MemGuard backend.")
        print(f"Please ensure the backend is running at {BASE_URL}")
        print("\nStart it with:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
