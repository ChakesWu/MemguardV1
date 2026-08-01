import threading
import time

import pytest

from memguard import DecisionTrace, MemGuard, MemoryEvent
from memguard.demo import (
    AGENT_OUTPUT,
    CURRENT_FACTS,
    CURRENT_INPUT,
    TRACE_TIMESTAMP,
    run_location_demo,
)
from memguard.transport.http import TransportStats


class CaptureTransport:
    def __init__(self):
        self.records = []
        self.condition = threading.Condition()

    def _emit_sync(self, record):
        with self.condition:
            self.records.append(record)
            self.condition.notify_all()

    def flush(self, timeout=5.0):
        deadline = time.monotonic() + timeout
        with self.condition:
            while len(self.records) < 2:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self.condition.wait(remaining)
        return True

    def stats(self):
        count = len(self.records)
        return TransportStats(
            queued=count, delivered=count, dropped=0, failed=0, pending=0
        )


def make_client(monkeypatch):
    from memguard import client as client_module

    transport = CaptureTransport()
    monkeypatch.setattr(
        client_module, "HttpTransport", lambda *args, **kwargs: transport
    )
    client = MemGuard(
        api_url="http://localhost:8000",
        api_key="token",
        agent_id="location-agent",
        namespace="acme-dev",
        capture_content=True,
    )
    return client, transport


def test_location_demo_records_complete_deterministic_evidence(monkeypatch):
    client, transport = make_client(monkeypatch)

    result = run_location_demo(client)

    retrievals = [
        record for record in transport.records if isinstance(record, MemoryEvent)
    ]
    traces = [
        record for record in transport.records if isinstance(record, DecisionTrace)
    ]
    assert len(retrievals) == 1
    assert len(traces) == 1
    retrieval = retrievals[0]
    assert retrieval.context["source_type"] == "conversation"
    assert retrieval.context["source_id"] == "trip-message-2026-06-15"
    assert retrieval.context["retrieval_rank"] == 1
    assert retrieval.context["retrieval_score"] == 0.93
    assert retrieval.context["included_in_prompt"] is True
    assert retrieval.context["fact_key"] == "current_location"
    assert retrieval.context["max_age_seconds"] == 86400
    trace = traces[0]
    assert trace.user_input == CURRENT_INPUT
    assert trace.context["current_facts"] == CURRENT_FACTS
    assert trace.output_summary == AGENT_OUTPUT
    assert trace.model == "deterministic-demo"
    assert trace.timestamp == TRACE_TIMESTAMP
    assert result["trace_id"] == trace.trace_id
    assert result["dashboard_url"].endswith(f"/?trace={trace.trace_id}")
    assert result["tenant"] == "acme-dev"


def test_location_demo_fails_loudly_when_evidence_is_incomplete(monkeypatch):
    client, transport = make_client(monkeypatch)
    transport.flush = lambda timeout=5.0: False
    transport.stats = lambda: TransportStats(2, 1, 0, 1, 0)

    with pytest.raises(RuntimeError, match="failed=1"):
        run_location_demo(client)
