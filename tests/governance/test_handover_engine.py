"""Contract tests for enterprise memory ownership and safe agent handover."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
)
from memguard.governance.handover import (
    HandoverEngine,
    HandoverMemory,
    HandoverOutcome,
    MemoryOwner,
    TransferPolicy,
)


NOW = datetime(2026, 8, 9, tzinfo=timezone.utc)
POLICY = GovernancePolicy(
    policy_id="enterprise-handover-v1",
    source_scores={"company_system": 95, "employee_agent": 70},
    writer_scores={"system": 100, "alex": 80},
    max_age_days={"company_system": 365, "employee_agent": 180},
)
CONTEXT = GovernanceContext("acme", "successor-agent", "employee_handover", NOW)


def record(memory_id: str, content: str, **overrides) -> HandoverMemory:
    values = {
        "evidence": MemoryEvidence(
            memory_id=memory_id,
            tenant_id="acme",
            content=content,
            source_type="employee_agent",
            source_id="alex-support-agent",
            writer_id="alex",
            created_at=NOW - timedelta(days=3),
            verified_at=NOW - timedelta(days=3),
            conflict_status=ConflictStatus.NONE,
            allowed_purposes=("employee_handover",),
            data_classification=DataClassification.INTERNAL,
        ),
        "owner": MemoryOwner.COMPANY,
        "transfer_policy": TransferPolicy.TRANSFER_IF_ALLOWED,
        "business_owner": "Customer Success",
        "source_label": "Alex's support agent",
    }
    values.update(overrides)
    return HandoverMemory(**values)


def test_handover_transfers_company_knowledge_but_never_personal_employee_memory():
    report = HandoverEngine(POLICY).prepare(
        (
            record("northstar-escalation", "Northstar escalations go to the platform on-call channel."),
            record(
                "alex-medical-appointment",
                "Alex has a medical appointment on Thursday.",
                owner=MemoryOwner.EMPLOYEE,
                transfer_policy=TransferPolicy.PROTECT,
                evidence=MemoryEvidence(
                    memory_id="alex-medical-appointment",
                    tenant_id="acme",
                    content="Alex has a medical appointment on Thursday.",
                    source_type="employee_agent",
                    writer_id="alex",
                    created_at=NOW - timedelta(days=1),
                    verified_at=NOW - timedelta(days=1),
                    conflict_status=ConflictStatus.NONE,
                    allowed_purposes=("employee_handover",),
                    data_classification=DataClassification.PRIVATE_EMPLOYEE,
                ),
            ),
        ),
        CONTEXT,
    )

    assert report.by_id("northstar-escalation").outcome is HandoverOutcome.TRANSFERRED
    private = report.by_id("alex-medical-appointment")
    assert private.outcome is HandoverOutcome.PROTECTED
    assert "medical appointment" not in report.successor_prompt
    assert report.summary()["protected"] == 1


def test_handover_redacts_mixed_memory_before_any_review_or_transfer():
    report = HandoverEngine(POLICY).prepare(
        (
            record(
                "acme-mixed-note",
                "Acme needs a security review before renewal. Alex prefers to call the customer personally.",
                transfer_policy=TransferPolicy.REDACT_AND_REVIEW,
                redacted_content="Acme needs a security review before renewal. [Personal employee preference removed]",
            ),
        ),
        CONTEXT,
    )

    item = report.by_id("acme-mixed-note")
    assert item.outcome is HandoverOutcome.REDACTED_FOR_REVIEW
    assert item.redacted_content == "Acme needs a security review before renewal. [Personal employee preference removed]"
    assert "prefers to call" not in report.successor_prompt


def test_company_system_records_are_read_only_sources_not_transfer_candidates():
    source = record(
        "crm-acme-renewal",
        "Acme requires SAML SSO before contract renewal.",
        owner=MemoryOwner.COMPANY_SYSTEM,
        transfer_policy=TransferPolicy.SOURCE_OF_TRUTH,
        source_label="CRM / Acme account",
    )

    report = HandoverEngine(POLICY).prepare((source,), CONTEXT)

    item = report.by_id("crm-acme-renewal")
    assert item.outcome is HandoverOutcome.RETAINED_AT_SOURCE
    assert item.memory.evidence.memory_id not in report.successor_memory_ids
    assert report.source_of_truth_ids == ("crm-acme-renewal",)
