"""Phase 1A contract tests for truthful output-first evidence."""

import os
import pathlib
import sys
import tempfile
import unittest


_db_dir = tempfile.TemporaryDirectory(prefix="memguard-phase1a-")
os.environ["MEMGUARD_DB_PATH"] = os.path.join(_db_dir.name, "events.db")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class Phase1AContractTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_missing_trace_returns_not_found(self):
        response = self.client.get("/v1/trace/does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Trace not found"})

        detail_response = self.client.get("/v1/decision-traces/does-not-exist")
        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(detail_response.json(), {"detail": "Trace not found"})

    def test_audit_report_uses_recorded_session_events(self):
        ingest = self.client.post(
            "/v1/events",
            json={
                "events": [
                    {
                        "event_id": "phase1a-read-1",
                        "agent_id": "generic-agent",
                        "operation": "read",
                        "memory_key": "memory:user-preference",
                        "memory_type": "semantic",
                        "namespace": "demo-tenant",
                        "session_id": "run-1",
                        "timestamp": "2026-07-24T00:00:00+00:00",
                        "content_hash": "hash-1",
                    }
                ]
            },
        )
        self.assertEqual(ingest.status_code, 200)

        response = self.client.get("/v1/analysis/audit/run-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metadata"]["total_events"], 1)
        self.assertIn("generic-agent", response.json()["metadata"]["agents"])

    def test_trace_returns_explicit_evidence_items(self):
        ingest = self.client.post(
            "/v1/events",
            json={
                "events": [
                    {
                        "event_id": "phase1a-input-1",
                        "agent_id": "generic-agent",
                        "operation": "read",
                        "memory_key": "memory:language",
                        "memory_type": "semantic",
                        "namespace": "evidence-tenant",
                        "session_id": "evidence-run",
                        "timestamp": "2026-07-24T00:00:00+00:00",
                        "content_hash": "input-hash",
                    },
                    {
                        "event_id": "phase1a-output-1",
                        "agent_id": "generic-agent",
                        "operation": "create",
                        "memory_key": "memory:last-answer",
                        "memory_type": "working",
                        "namespace": "evidence-tenant",
                        "session_id": "evidence-run",
                        "timestamp": "2026-07-24T00:00:01+00:00",
                        "content_hash": "output-hash",
                    },
                ]
            },
        )
        self.assertEqual(ingest.status_code, 200)

        created = self.client.post(
            "/v1/trace",
            json={
                "trace_id": "evidence-trace",
                "agent_id": "generic-agent",
                "namespace": "evidence-tenant",
                "session_id": "evidence-run",
                "timestamp": "2026-07-24T00:00:02+00:00",
                "input_event_ids": ["phase1a-input-1"],
                "output_event_ids": ["phase1a-output-1"],
                "output_summary": "The agent selected Python.",
            },
        )
        self.assertEqual(created.status_code, 200)

        response = self.client.get("/v1/trace/evidence-trace")

        self.assertEqual(response.status_code, 200)
        evidence = response.json()["evidence_items"]
        self.assertEqual([item["event_id"] for item in evidence], ["phase1a-input-1", "phase1a-output-1"])
        self.assertEqual([item["side"] for item in evidence], ["input", "output"])

    def test_frontend_trace_path_has_no_hard_coded_evidence_rows(self):
        page = (pathlib.Path(__file__).parent.parent / "frontend" / "app" / "page.tsx").read_text()
        self.assertIn("evidence_items", page)
        self.assertNotIn("FINCOMPLI", page)
        self.assertNotIn("input_memory_ids.map", page)
        self.assertNotIn("output_memory_ids.map", page)

    def test_generic_demo_flushes_queued_evidence_before_returning(self):
        demo = (pathlib.Path(__file__).parent.parent / "examples" / "generic_trace_demo.py").read_text()
        self.assertIn("transport.flush(timeout=5)", demo)

    def test_missing_linked_event_is_reported_without_fabricated_evidence(self):
        created = self.client.post(
            "/v1/trace",
            json={
                "trace_id": "missing-evidence-trace",
                "agent_id": "generic-agent",
                "namespace": "evidence-tenant",
                "session_id": "evidence-run",
                "input_event_ids": ["not-persisted"],
                "output_event_ids": [],
            },
        )
        self.assertEqual(created.status_code, 200)

        response = self.client.get("/v1/trace/missing-evidence-trace")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["evidence_items"], [])
        self.assertEqual(response.json()["missing_evidence_event_ids"], ["not-persisted"])


if __name__ == "__main__":
    unittest.main()
