"""Deterministic demo fixtures for memory-output visualization."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .client import MemGuard


CURRENT_INPUT = "I am currently in New York. Where am I?"
CURRENT_FACTS = {"current_location": "New York"}
RETRIEVED_MEMORY = {"current_location": "Taipei"}
AGENT_OUTPUT = "You are currently in Taipei."
MEMORY_CREATED_AT = "2026-06-15T09:00:00+00:00"
MEMORY_LAST_VERIFIED_AT = "2026-06-15T09:00:00+00:00"
TRACE_TIMESTAMP = "2026-08-01T12:00:00+00:00"


def run_location_demo(
    client: MemGuard, dashboard_url: str = "http://localhost:3001"
) -> dict[str, Any]:
    """Record a repeatable stale-memory conflict without an external model."""
    session_id = "location-demo-run"
    client.set_session(session_id)
    retrieval_event_id = client.record_retrieval(
        "profile:current_location",
        RETRIEVED_MEMORY,
        source_type="conversation",
        source_id="trip-message-2026-06-15",
        memory_created_at=MEMORY_CREATED_AT,
        memory_last_verified_at=MEMORY_LAST_VERIFIED_AT,
        retrieval_query="Where is the user currently located?",
        retrieval_score=0.93,
        retrieval_rank=1,
        included_in_prompt=True,
        fact_key="current_location",
        max_age_seconds=86400,
    )
    trace = client.record_output(
        user_input=CURRENT_INPUT,
        output_text=AGENT_OUTPUT,
        input_event_ids=[retrieval_event_id],
        model="deterministic-demo",
        current_facts=CURRENT_FACTS,
        timestamp=TRACE_TIMESTAMP,
    )

    flushed = client.flush(timeout=5.0)
    status = client.delivery_status()
    if not flushed or not status.evidence_complete:
        raise RuntimeError(
            "MemGuard evidence delivery incomplete: "
            f"queued={status.queued} delivered={status.delivered} "
            f"dropped={status.dropped} failed={status.failed} "
            f"pending={status.pending}"
        )

    delivery = asdict(status)
    delivery["evidence_complete"] = status.evidence_complete
    return {
        "tenant": client.namespace,
        "agent": client.agent_id,
        "session": session_id,
        "input": CURRENT_INPUT,
        "retrieved_value": RETRIEVED_MEMORY,
        "output": AGENT_OUTPUT,
        "trace_id": trace.trace_id,
        "delivery": delivery,
        "dashboard_url": f"{dashboard_url.rstrip('/')}/?trace={trace.trace_id}",
    }
