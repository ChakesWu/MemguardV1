from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    EvidenceEvaluation,
    EvidenceReportBuilder,
    InfluenceResult,
    MemoryEvidence,
    MemoryGovernanceEngine,
    GovernanceContext,
    GovernancePolicy,
    RetrievalSignals,
    PolicyAction,
    PolicyDecision,
    TrustFactor,
    TrustFactors,
    TrustLevel,
    TrustResult,
)
from memguard.governance.models import OutputCitation


NOW = datetime(2026, 8, 5, tzinfo=timezone.utc)


POLICY = GovernancePolicy(
    policy_id="governance-v1",
    source_scores={"crm": 100},
    writer_scores={"crm-sync": 100},
    max_age_days={"crm": 365},
)
CONTEXT = GovernanceContext("acme", "support-agent", "customer_support", NOW)


def governed_memory(memory_id: str, content: str, *, classification=DataClassification.INTERNAL) -> MemoryEvidence:
    return MemoryEvidence(
        memory_id=memory_id,
        tenant_id="acme",
        content=content,
        source_type="crm",
        writer_id="crm-sync",
        created_at=NOW,
        verified_at=NOW,
        conflict_status=ConflictStatus.NONE,
        data_classification=classification,
        allowed_purposes=("customer_support",),
        retrieval=RetrievalSignals(similarity=0.9, retrieved=True),
    )


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


def test_report_serializes_valid_output_evidence():
    engine = MemoryGovernanceEngine(POLICY)
    run = engine.evaluate_and_build_prompt(
        "When does Northstar renew?",
        (governed_memory("crm-104", "Renewal date: October"),),
        CONTEXT,
    )
    answer = "Northstar renews in October."
    result = engine.link_output_evidence(
        run,
        answer=answer,
        citations=(OutputCitation(0, len(answer), answer, "crm-104", "Renewal date: October", "factual_support"),),
    )

    payload = run.report.to_dict(output_evidence=result)

    assert payload["output_evidence"]["summary"] == {
        "valid_links": 1,
        "invalid_citations": 0,
        "evidence_gaps": 0,
    }
    assert payload["output_evidence"]["valid_links"][0]["evidence_quote"] == "Renewal date: October"
    assert payload["output_evidence"]["valid_links"][0]["trust"]["level"] == "high"


def test_report_redacts_valid_output_evidence_for_restricted_memory():
    engine = MemoryGovernanceEngine(POLICY)
    run = engine.evaluate_and_build_prompt(
        "When does Northstar renew?",
        (governed_memory("crm-104", "Renewal date: October", classification=DataClassification.RESTRICTED),),
        CONTEXT,
    )
    answer = "Northstar renews in October."
    result = engine.link_output_evidence(
        run,
        answer=answer,
        citations=(OutputCitation(0, len(answer), answer, "crm-104", "Renewal date: October", "factual_support"),),
    )

    payload = run.report.to_dict(output_evidence=result)

    assert run.by_id("crm-104").policy.action is PolicyAction.REVIEW_REQUIRED
    assert payload["items"][0]["content"] == "[redacted]"
    assert payload["output_evidence"]["valid_links"][0]["evidence_quote"] == "[redacted]"


def test_report_never_serializes_unvalidated_evidence_quotes():
    engine = MemoryGovernanceEngine(POLICY)
    run = engine.evaluate_and_build_prompt(
        "When does Northstar renew?",
        (governed_memory("crm-104", "Renewal date: October"),),
        CONTEXT,
    )
    raw_quote = "production token: secret-token-value"
    result = engine.link_output_evidence(
        run,
        answer="Northstar",
        citations=(OutputCitation(0, 9, "Northstar", "crm-104", raw_quote, "factual_support"),),
    )

    payload = run.report.to_dict(output_evidence=result)

    assert result.valid_links == ()
    assert raw_quote not in repr(result)
    assert raw_quote not in repr(payload)
    assert payload["output_evidence"]["invalid_citations"][0]["reason_codes"] == ["evidence:quote_not_found"]
