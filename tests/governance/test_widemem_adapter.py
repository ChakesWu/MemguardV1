from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from memguard.governance import ConflictStatus
from memguard.governance.adapters.widemem import WideMemSignalAdapter


def test_widemem_retrieval_signals_never_become_memguard_trust():
    record = SimpleNamespace(
        memory=SimpleNamespace(
            id="wide-1",
            content="Acme requires SAML SSO.",
            created_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
            metadata={
                "source_type": "crm",
                "writer_id": "alex",
                "data_classification": "secret",
                "allowed_purposes": ["incident_response"],
                "conflict_status": "high",
            },
        ),
        similarity_score=0.84,
        importance_score=0.9,
        temporal_score=0.76,
        final_score=0.83,
    )

    evidence = WideMemSignalAdapter().from_search_result(
        record,
        tenant_id="acme",
    )

    assert evidence.memory_id == "wide-1"
    assert evidence.retrieval.similarity == 0.84
    assert evidence.retrieval.importance == 0.9
    assert evidence.retrieval.recency == 0.76
    assert evidence.retrieval.retrieval_score == 0.83
    assert evidence.metadata["provider"] == "widemem"
    assert "trust_score" not in evidence.metadata
    assert evidence.data_classification.value == "secret"
    assert evidence.allowed_purposes == ("incident_response",)
    assert evidence.conflict_status is ConflictStatus.HIGH


def test_adapter_accepts_widemem_dict_exports_without_importing_widemem():
    evidence = WideMemSignalAdapter().from_mapping(
        {
            "id": "wide-2",
            "tenant_id": "acme",
            "content": "Escalate outages within fifteen minutes.",
            "created_at": "2026-08-01T00:00:00+00:00",
            "source_type": "runbook",
            "writer_id": "platform-owner",
            "similarity": 0.7,
            "importance": 0.8,
            "recency": 0.9,
            "final_score": 0.78,
            "data_classification": "secret",
            "conflict_status": "high",
            "allowed_purposes": ["incident_response"],
        }
    )

    assert evidence.memory_id == "wide-2"
    assert evidence.source_type == "runbook"
    assert evidence.retrieval.retrieved is True
    assert evidence.retrieval.retrieval_score == 0.78
    assert evidence.tenant_id == "acme"
    assert evidence.data_classification.value == "secret"
    assert evidence.conflict_status.value == "high"
    assert evidence.allowed_purposes == ("incident_response",)
