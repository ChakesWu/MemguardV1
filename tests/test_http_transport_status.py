import queue
import threading

from memguard.core.event import DecisionTrace, MemoryEvent, MemoryOp
from memguard.transport.http import HttpTransport


def memory_event(key: str) -> MemoryEvent:
    return MemoryEvent(operation=MemoryOp.READ, memory_key=key)


def test_successful_batch_counts_records_as_queued_and_delivered(monkeypatch):
    transport = HttpTransport(batch_wait=0.02)
    monkeypatch.setattr(transport, "_post", lambda path, payload: None)

    transport._emit_sync(memory_event("one"))
    transport._emit_sync(memory_event("two"))

    assert transport.flush(timeout=1)
    stats = transport.stats()
    assert stats.queued == 2
    assert stats.delivered == 2
    assert stats.failed == 0
    assert stats.pending == 0
    assert stats.evidence_complete is True


def test_final_retry_failure_counts_every_failed_record(monkeypatch):
    transport = HttpTransport(batch_wait=0.02)

    def fail(_path, _payload):
        raise OSError("offline")

    monkeypatch.setattr(transport, "_post", fail)
    transport._emit_sync(memory_event("one"))
    transport._emit_sync(memory_event("two"))

    assert transport.flush(timeout=1)
    stats = transport.stats()
    assert stats.failed == 2
    assert stats.delivered == 0
    assert stats.evidence_complete is False


def test_queue_overflow_counts_dropped_record(monkeypatch):
    transport = HttpTransport()

    def full(_event):
        raise queue.Full

    monkeypatch.setattr(transport._queue, "put_nowait", full)
    transport._emit_sync(memory_event("dropped"))

    stats = transport.stats()
    assert stats.queued == 1
    assert stats.dropped == 1
    assert stats.pending == 0
    assert stats.evidence_complete is False


def test_flush_returns_false_while_record_is_pending(monkeypatch):
    transport = HttpTransport(batch_wait=0)
    started = threading.Event()
    release = threading.Event()

    def block(_path, _payload):
        started.set()
        release.wait(1)

    monkeypatch.setattr(transport, "_post", block)
    transport._emit_sync(DecisionTrace())

    assert started.wait(1)
    assert transport.flush(timeout=0.01) is False
    assert transport.stats().pending == 1

    release.set()
    assert transport.flush(timeout=1) is True
    assert transport.stats().evidence_complete is True
