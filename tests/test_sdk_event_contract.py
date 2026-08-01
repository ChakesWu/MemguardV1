import threading

from memguard.core.event import DecisionTrace, MemoryOp
from memguard.core.interceptor import MemGuardInterceptor


class CaptureTransport:
    def __init__(self):
        self.event = None
        self.ready = threading.Event()

    def _emit_sync(self, event):
        self.event = event
        self.ready.set()


def test_hash_only_record_keeps_hash_but_removes_content():
    transport = CaptureTransport()
    guard = MemGuardInterceptor("agent", transport=transport, capture_content=False)

    guard.record(MemoryOp.READ, "profile:location", after_value={"city": "Taipei"})

    assert transport.ready.wait(1)
    assert transport.event.after_value is None
    assert transport.event.content_hash


def test_canonical_hash_ignores_mapping_insertion_order():
    first = MemGuardInterceptor._hash_content({"city": "Taipei", "country": "Taiwan"})
    second = MemGuardInterceptor._hash_content({"country": "Taiwan", "city": "Taipei"})

    assert first == second


def test_content_capture_uses_same_hash_as_hash_only_mode():
    private_transport = CaptureTransport()
    visible_transport = CaptureTransport()
    value = {"current_location": "Taipei"}

    MemGuardInterceptor(
        "agent", transport=private_transport, capture_content=False
    ).record(MemoryOp.READ, "profile:location", after_value=value)
    MemGuardInterceptor(
        "agent", transport=visible_transport, capture_content=True
    ).record(MemoryOp.READ, "profile:location", after_value=value)

    assert private_transport.ready.wait(1)
    assert visible_transport.ready.wait(1)
    assert visible_transport.event.after_value == value
    assert private_transport.event.content_hash == visible_transport.event.content_hash


def test_decision_trace_has_display_fields():
    trace = DecisionTrace(user_input="I am in New York", model="demo-model")

    assert trace.user_input == "I am in New York"
    assert trace.model == "demo-model"
