from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from memguard.governance import (
    DataClassification,
    EvidenceEvaluation,
    EvidenceReportBuilder,
    InfluenceResult,
    MemoryEvidence,
    PolicyAction,
    PolicyDecision,
    TrustFactor,
    TrustFactors,
    TrustLevel,
    TrustResult,
)


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


def evaluated(memory: MemoryEvidence, action: PolicyAction) -> EvidenceEvaluation:
    factors = TrustFactors(
        source=TrustFactor(90, "verified source"),
        writer=TrustFactor(80, "known writer"),
        freshness=TrustFactor(70, "recent"),
        conflict=TrustFactor(100, "no conflict"),
        policy_fit=TrustFactor(100, "allowed purpose"),
    )
    trust = TrustResult(86.5, TrustLevel.HIGH, factors, ("source:trusted",), ())
    decision = PolicyDecision(action, action in {PolicyAction.BLOCK, PolicyAction.QUARANTINE}, (f"test:{action.value}",), "test decision")
    influence = InfluenceResult(memory.memory_id, 0.5, True, action is PolicyAction.ALLOW, False, False, ())
    return EvidenceEvaluation(memory, trust, decision, influence)


def test_report_is_auditable_but_does_not_leak_sensitive_content():
    allowed = MemoryEvidence(memory_id="allowed", tenant_id="acme", content="Approved refund policy", source_type="policy")
    secret = MemoryEvidence(
        memory_id="secret",
        tenant_id="acme",
        content="production token is secret-token-value",
        source_type="note",
        data_classification=DataClassification.SECRET,
    )

    report = EvidenceReportBuilder().build("governance-v1", "acme", NOW, (evaluated(allowed, PolicyAction.ALLOW), evaluated(secret, PolicyAction.QUARANTINE)))
    payload = report.to_dict()
    rendered = str(payload)

    assert "secret-token-value" not in rendered
    assert payload["tenant_id"] == "acme"
    assert payload["summary"] == {"allow": 1, "quarantine": 1}
    secret_item = next(item for item in payload["items"] if item["memory_id"] == "secret")
    assert secret_item["content"] == "[redacted]"
    assert len(secret_item["content_hash"]) == 64
    assert secret_item["policy"]["enforced"] is True
    assert secret_item["trust"]["factors"]["source"]["score"] == 90
    assert "secret-token-value" not in repr(report)
    assert "secret-token-value" not in str(asdict(report))


def test_report_is_hash_only_by_default_even_for_allowed_memory():
    allowed = MemoryEvidence(memory_id="allowed", tenant_id="acme", content="Approved refund policy", source_type="policy")
    report = EvidenceReportBuilder().build("governance-v1", "acme", NOW, (evaluated(allowed, PolicyAction.ALLOW),))

    assert report.to_dict()["items"][0]["content"] == "[hash-only]"
