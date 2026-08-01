import os
import pathlib
import sys
import tempfile
from unittest.mock import patch


_db_dir = tempfile.TemporaryDirectory(prefix="memguard-trace-ingestion-")
os.environ["MEMGUARD_DB_PATH"] = os.path.join(_db_dir.name, "events.db")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import TenantPrincipal  # noqa: E402
from app.main import app, gateway  # noqa: E402


def test_trace_ingestion_persists_explicit_output_context_once():
    principal = TenantPrincipal(
        subject="test-user", tenant_id="acme-dev", claims={"sub": "test-user"}
    )
    payload = {
        "trace_id": "trace-location-demo",
        "agent_id": "location-agent",
        "session_id": "location-demo-run",
        "namespace": "acme-dev",
        "timestamp": "2026-08-01T12:00:00+00:00",
        "input_event_ids": ["retrieval-location-taipei"],
        "output_event_ids": [],
        "prompt_hash": "prompt-hash",
        "output_hash": "output-hash",
        "output_summary": "You are currently in Taipei.",
        "user_input": "I am currently in New York.",
        "model": "deterministic-demo",
        "memory_influence_score": 0.0,
        "context": {
            "current_facts": {"current_location": "New York"},
            "evidence_model": "recorded_lineage",
            "causality_claim": "not_proven",
        },
    }

    with patch("app.main.authenticate_bearer_token", return_value=principal):
        client = TestClient(app)
        created = client.post(
            "/v1/trace", json=payload, headers={"Authorization": "Bearer test-token"}
        )
        fetched = client.get(
            "/v1/trace/trace-location-demo",
            headers={"Authorization": "Bearer test-token"},
        )

    assert created.status_code == 200
    assert fetched.status_code == 200
    trace = fetched.json()
    assert trace["user_input"] == "I am currently in New York."
    assert trace["llm_model"] == "deterministic-demo"
    assert trace["metadata"] == payload["context"]

    with gateway.database.connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM decision_traces WHERE trace_id = ?",
            ("trace-location-demo",),
        ).fetchone()
    assert row["count"] == 1
