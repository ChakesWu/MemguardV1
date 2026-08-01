"""Deterministic technical validation for the Phase 1A output-first MVP."""

import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch


_db_dir = tempfile.TemporaryDirectory(prefix="memguard-validation-")
os.environ["MEMGUARD_DB_PATH"] = os.path.join(_db_dir.name, "events.db")
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import TenantPrincipal  # noqa: E402
from app.main import app  # noqa: E402


class SoloValidationGateTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.auth_patch = patch(
            "app.main.authenticate_bearer_token",
            return_value=TenantPrincipal(
                subject="test-user", tenant_id="validation-org", claims={"sub": "test-user"}
            ),
        )
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    def _event(self, event_id, memory_key, timestamp, *, metadata=None):
        return {
            "event_id": event_id,
            "agent_id": "validation-agent",
            "operation": "read",
            "memory_key": memory_key,
            "memory_type": "semantic",
            "namespace": "validation-org",
            "session_id": "validation-run",
            "timestamp": timestamp,
            "content_hash": f"hash-{event_id}",
            "context": metadata or {},
        }

    def _trace(self, trace_id, input_event_ids, output="Recorded output"):
        response = self.client.post(
            "/v1/trace",
            json={
                "trace_id": trace_id,
                "agent_id": "validation-agent",
                "namespace": "validation-org",
                "session_id": "validation-run",
                "timestamp": "2026-07-25T12:00:00+00:00",
                "input_event_ids": input_event_ids,
                "output_event_ids": [],
                "output_summary": output,
            },
        )
        self.assertEqual(response.status_code, 200)
        return self.client.get(f"/v1/trace/{trace_id}").json()

    def test_stale_memory_keeps_recorded_timestamp(self):
        self.client.post("/v1/events", json={"events": [
            self._event("stale-old", "preference:billing", "2026-01-01T00:00:00+00:00"),
            self._event("stale-new", "preference:billing", "2026-07-25T11:59:00+00:00"),
        ]})
        trace = self._trace("stale-memory", ["stale-old", "stale-new"])

        evidence = {item["event_id"]: item for item in trace["evidence_items"]}
        self.assertEqual(evidence["stale-old"]["timestamp"], "2026-01-01T00:00:00+00:00")
        self.assertEqual(evidence["stale-new"]["timestamp"], "2026-07-25T11:59:00+00:00")

    def test_conflicting_memory_preserves_both_records(self):
        self.client.post("/v1/events", json={"events": [
            self._event("conflict-a", "preference:contact", "2026-07-25T11:00:00+00:00"),
            self._event("conflict-b", "preference:contact", "2026-07-25T11:01:00+00:00"),
        ]})
        trace = self._trace("conflicting-memory", ["conflict-a", "conflict-b"])

        self.assertEqual([item["event_id"] for item in trace["evidence_items"]], ["conflict-a", "conflict-b"])
        self.assertEqual({item["memory_key"] for item in trace["evidence_items"]}, {"preference:contact"})

    def test_irrelevant_retrieval_preserves_relevance_metadata(self):
        self.client.post("/v1/events", json={"events": [
            self._event(
                "irrelevant-retrieval",
                "profile:favourite-colour",
                "2026-07-25T11:30:00+00:00",
                metadata={"evidence_role": "retrieval", "relevance": "low", "source_type": "vector-search"},
            ),
        ]})
        trace = self._trace("irrelevant-retrieval", ["irrelevant-retrieval"])

        metadata = trace["evidence_items"][0]["metadata"]
        self.assertEqual(metadata["relevance"], "low")
        self.assertEqual(metadata["source_type"], "vector-search")

    def test_missing_retrieval_reports_evidence_gap(self):
        trace = self._trace("missing-retrieval", ["missing-retrieval-event"])

        self.assertEqual(trace["evidence_items"], [])
        self.assertEqual(trace["missing_evidence_event_ids"], ["missing-retrieval-event"])

    def test_untrusted_memory_preserves_trust_and_policy_metadata(self):
        self.client.post("/v1/events", json={"events": [
            self._event(
                "untrusted-memory",
                "external:instruction",
                "2026-07-25T11:45:00+00:00",
                metadata={"source_type": "untrusted-import", "trust_score": 10, "policy_status": "quarantine"},
            ),
        ]})
        trace = self._trace("untrusted-memory", ["untrusted-memory"])

        metadata = trace["evidence_items"][0]["metadata"]
        self.assertEqual(metadata["trust_score"], 10)
        self.assertEqual(metadata["policy_status"], "quarantine")

    def test_frontend_surfaces_metadata_needed_for_debugging(self):
        project_root = pathlib.Path(__file__).parent.parent
        workspace = (
            project_root / "frontend" / "components" / "EvidenceWorkspace.tsx"
        ).read_text()
        dashboard = (project_root / "frontend" / "lib" / "dashboard.ts").read_text()

        self.assertIn("evidenceContextLabel", workspace)
        self.assertIn("source_type", dashboard)
        self.assertIn("relevance", dashboard)
        self.assertIn("trust_score", dashboard)
        self.assertIn("policy_status", dashboard)


if __name__ == "__main__":
    unittest.main()
