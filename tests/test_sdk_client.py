import threading

import pytest

from memguard import DecisionTrace, MemGuard, MemoryEvent, MemoryOp, MemoryType
from memguard.core.interceptor import MemGuardInterceptor


class CaptureTransport:
    def __init__(self):
        self.records = []
        self.ready = threading.Event()

    def _emit_sync(self, record):
        self.records.append(record)
        self.ready.set()


def test_record_retrieval_and_output_capture_visualization_contract():
    transport = CaptureTransport()
    interceptor = MemGuardInterceptor(
        "location-agent",
        transport=transport,
        namespace="acme-dev",
        capture_content=True,
    )
    interceptor.set_session("location-demo-run")

    event_id = interceptor.record_retrieval(
        "profile:current_location",
        {"current_location": "Taipei"},
        source_type="conversation",
        source_id="trip-message-2026-07-01",
        memory_created_at="2026-07-01T09:00:00+00:00",
        memory_last_verified_at="2026-07-01T09:00:00+00:00",
        retrieval_query="Where is the user?",
        retrieval_score=0.93,
        retrieval_rank=1,
        included_in_prompt=True,
        fact_key="current_location",
        max_age_seconds=86400,
    )
    trace = interceptor.record_output(
        user_input="I am currently in New York.",
        output_text="You are currently in Taipei.",
        input_event_ids=[event_id],
        model="deterministic-demo",
        current_facts={"current_location": "New York"},
    )

    assert transport.ready.wait(1)
    event = next(
        record for record in transport.records if isinstance(record, MemoryEvent)
    )
    assert event.operation == MemoryOp.READ
    assert event.memory_type == MemoryType.SEMANTIC
    assert event.context == {
        "evidence_role": "retrieved_memory",
        "source_type": "conversation",
        "source_id": "trip-message-2026-07-01",
        "memory_created_at": "2026-07-01T09:00:00+00:00",
        "memory_last_verified_at": "2026-07-01T09:00:00+00:00",
        "retrieval_query": "Where is the user?",
        "retrieval_score": 0.93,
        "retrieval_rank": 1,
        "included_in_prompt": True,
        "fact_key": "current_location",
        "max_age_seconds": 86400,
    }
    assert trace.user_input == "I am currently in New York."
    assert trace.model == "deterministic-demo"
    assert trace.output_event_ids == []
    assert trace.context == {
        "current_facts": {"current_location": "New York"},
        "evidence_model": "recorded_lineage",
        "causality_claim": "not_proven",
    }


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"retrieval_rank": 0}, "retrieval_rank"),
        ({"retrieval_score": -0.1}, "retrieval_score"),
        ({"retrieval_score": 1.1}, "retrieval_score"),
        ({"max_age_seconds": -1}, "max_age_seconds"),
    ],
)
def test_record_retrieval_rejects_invalid_provenance(kwargs, message):
    interceptor = MemGuardInterceptor("agent", transport=CaptureTransport())

    with pytest.raises(ValueError, match=message):
        interceptor.record_retrieval(
            "profile:current_location",
            {"current_location": "Taipei"},
            source_type="conversation",
            **kwargs,
        )


def test_public_memguard_facade_constructs_and_delegates(monkeypatch):
    from memguard import client as client_module

    transport = CaptureTransport()
    transport.flush = lambda timeout=5.0: timeout == 2.0
    monkeypatch.setattr(
        client_module, "HttpTransport", lambda *args, **kwargs: transport
    )
    guard = MemGuard(
        api_url="http://localhost:8000",
        api_key="token",
        agent_id="location-agent",
        namespace="acme-dev",
        capture_content=True,
    )
    guard.set_session("run-1")

    event_id = guard.record_retrieval(
        "profile:current_location",
        {"current_location": "Taipei"},
        source_type="conversation",
    )

    assert event_id
    assert transport.ready.wait(1)
    assert transport.records[0].session_id == "run-1"
    assert guard.flush(timeout=2.0) is True


def test_public_package_exports_visualization_types():
    assert MemGuard
    assert MemoryType
    assert MemoryOp
    assert MemoryEvent
    assert DecisionTrace
