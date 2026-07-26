#!/usr/bin/env python3
"""Deterministic LangGraph demo for the Phase 1A output-first trace.

Run the API first (``cd backend && uvicorn app.main:app``), then run this
script.  It records one read, one LangGraph checkpoint write, one explicit
memory write, and a decision trace linking those records to the output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Annotated, TypedDict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from memguard.adapters.langgraph import MemGuardCheckpointer
from memguard.core.event import MemoryOp, MemoryType
from memguard.transport import HttpTransport


class DemoState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    memory_hint: str


def respond(state: DemoState) -> DemoState:
    """Produce a deterministic answer using the recorded memory hint."""
    question = state["messages"][-1].content
    answer = f"Recorded memory says: {state.get('memory_hint', 'no hint')}. Question: {question}"
    return {"messages": [AIMessage(content=answer)]}


def build_graph(checkpointer: MemGuardCheckpointer):
    workflow = StateGraph(DemoState)
    workflow.add_node("respond", respond)
    workflow.add_edge(START, "respond")
    workflow.add_edge("respond", END)
    return workflow.compile(checkpointer=checkpointer)


def run_demo(backend_url: str, tenant_id: str, session_id: str) -> dict:
    # The SDK is fire-and-forget in production. This deterministic demo waits
    # for queued evidence before reporting a trace ID to the user.
    transport = HttpTransport(backend_url, timeout=1.0)
    checkpointer = MemGuardCheckpointer(
        inner=MemorySaver(),
        agent_id="generic-agent",
        namespace=tenant_id,
        transport=transport,
        capture_content=True,
    )
    interceptor = checkpointer.interceptor
    interceptor._emit_async = transport._emit_sync  # type: ignore[method-assign]
    interceptor.set_session(session_id)

    input_event_id = interceptor.record(
        operation=MemoryOp.READ,
        memory_key="profile:language",
        after_value={"language": "Python"},
        memory_type=MemoryType.SEMANTIC,
        source_type="demo-memory",
        evidence_role="retrieval",
    )

    graph = build_graph(checkpointer)
    result = graph.invoke(
        {
            "messages": [HumanMessage(content="Which language should I use for this example?")],
            "memory_hint": "Python",
        },
        {"configurable": {"thread_id": session_id}},
    )
    output_text = result["messages"][-1].content

    output_event_id = interceptor.record(
        operation=MemoryOp.CREATE,
        memory_key="answer:last",
        after_value={"answer": output_text},
        memory_type=MemoryType.WORKING,
        source_type="agent-output",
        evidence_role="resulting_write",
    )

    trace = interceptor.trace_decision(
        input_event_ids=[input_event_id],
        output_event_ids=[output_event_id],
        prompt_text="Which language should I use for this example?",
        output_text=output_text,
        context={
            "evidence_model": "recorded_lineage",
            "why_note": "Evidence links are not model-causal attribution.",
        },
    )
    if not transport.flush(timeout=5):
        raise RuntimeError("Timed out while sending demo evidence to MemGuard")
    return {
        "tenant_id": tenant_id,
        "agent_id": "generic-agent",
        "session_id": session_id,
        "trace_id": trace.trace_id,
        "input_event_id": input_event_id,
        "output_event_id": output_event_id,
        "output": output_text,
        "next_step": f"Open http://localhost:3001/?trace={trace.trace_id} or refresh the output list.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--tenant-id", default="demo-org")
    parser.add_argument("--session-id", default="generic-demo-run")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.backend_url, args.tenant_id, args.session_id), indent=2))


if __name__ == "__main__":
    main()
