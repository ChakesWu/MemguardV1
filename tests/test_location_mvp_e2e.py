import os
import pathlib
import sys
import tempfile
import threading
import time
from dataclasses import asdict
from unittest.mock import patch


_db_dir = tempfile.TemporaryDirectory(prefix="memguard-location-mvp-")
os.environ["MEMGUARD_DB_PATH"] = os.path.join(_db_dir.name, "events.db")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import TenantPrincipal  # noqa: E402
from app.main import app  # noqa: E402
from memguard import DecisionTrace, MemGuard, MemoryEvent  # noqa: E402
from memguard.demo import run_location_demo  # noqa: E402
from memguard.transport.http import TransportStats  # noqa: E402


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
        return TransportStats(count, count, 0, 0, 0)


def test_location_demo_round_trips_into_stale_conflict_explanation(monkeypatch):
    from memguard import client as client_module

    transport = CaptureTransport()
    monkeypatch.setattr(client_module, "HttpTransport", lambda *args, **kwargs: transport)
    guard = MemGuard(
        api_url="http://localhost:8000",
        api_key="token",
        agent_id="location-agent",
        namespace="acme-dev",
        capture_content=True,
    )
    demo_result = run_location_demo(guard)
    event = next(record for record in transport.records if isinstance(record, MemoryEvent))
    recorded_trace = next(
        record for record in transport.records if isinstance(record, DecisionTrace)
    )
    principal = TenantPrincipal(
        subject="test-user", tenant_id="acme-dev", claims={"sub": "test-user"}
    )

    with patch("app.main.authenticate_bearer_token", return_value=principal):
        client = TestClient(app)
        event_response = client.post(
            "/v1/events",
            json={"events": [asdict(event)]},
            headers={"Authorization": "Bearer test-token"},
        )
        trace_response = client.post(
            "/v1/trace",
            json=asdict(recorded_trace),
            headers={"Authorization": "Bearer test-token"},
        )
        fetched = client.get(
            f"/v1/trace/{demo_result['trace_id']}",
            headers={"Authorization": "Bearer test-token"},
        )

    assert event_response.status_code == 200
    assert trace_response.status_code == 200
    assert fetched.status_code == 200
    trace = fetched.json()
    assert trace["user_input"] == "I am currently in New York. Where am I?"
    assert trace["llm_output"] == "You are currently in Taipei."
    assert trace["explanation"]["status"] == "stale_conflict"
    assert trace["explanation"]["causality_claim"] == "not_proven"
    assert trace["missing_evidence_event_ids"] == []
    finding = trace["explanation"]["findings"][0]
    assert finding["remembered_value"] == "Taipei"
    assert finding["current_value"] == "New York"
    assert finding["included_in_prompt"] is True
