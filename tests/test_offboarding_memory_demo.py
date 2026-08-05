"""Acceptance tests for the employee offboarding memory classification demo."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from examples.offboarding_memory_demo import Decision, run_demo


AS_OF = datetime(2026, 8, 5, tzinfo=timezone.utc)


def test_demo_uses_widemem_scores_and_classifies_all_employee_memories(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)

    assert len(report.items) == 30
    assert all(item.widemem.final_score > 0 for item in report.items)
    assert all(0 <= item.widemem.importance <= 1 for item in report.items)
    assert all(0 <= item.widemem.recency <= 1 for item in report.items)


def test_private_memory_is_isolated_even_when_widemem_assigns_high_importance(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    private_memory = report.by_id("personal-medical-coverage")

    assert private_memory.widemem.importance == 1.0
    assert private_memory.decision is Decision.DELETE_OR_ISOLATE
    assert "private" in private_memory.reason.lower()


def test_stale_business_memory_is_archived_not_transferred(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    stale_memory = report.by_id("expired-refund-policy")

    assert stale_memory.widemem.recency < 0.1
    assert stale_memory.decision is Decision.ARCHIVE
    assert "lifecycle:expired" in stale_memory.governance.policy.reason_codes


def test_sensitive_or_ambiguous_memory_requires_human_review(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)

    assert report.by_id("production-api-token").decision is Decision.RESTRICTED_REVIEW
    assert report.by_id("unclear-relationship-note").decision is Decision.RESTRICTED_REVIEW
    queue = report.review_queue()
    assert all(item.decision is Decision.RESTRICTED_REVIEW for item in queue)
    assert [item.widemem.final_score for item in queue] == sorted(
        (item.widemem.final_score for item in queue), reverse=True
    )


def test_current_business_requirement_is_transferred_with_score_explanation(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    requirement = report.by_id("acme-sso-requirement")

    assert requirement.decision is Decision.TRANSFER
    assert requirement.widemem.similarity > 0
    assert requirement.governance.policy.action.value == "allow"


def test_report_redacts_private_and_restricted_content(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    payload = report.to_dict()
    rendered = str(payload)

    assert "secret-token-value" not in rendered
    assert "medical coverage claim" not in rendered
    assert "redacted" in rendered
    assert "secret-token-value" not in repr(report)
    assert "medical coverage claim" not in repr(report)
    assert "secret-token-value" not in str(asdict(report))
    assert "medical coverage claim" not in str(asdict(report))


def test_governance_gate_blocks_private_and_secret_memories_before_prompt(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)

    assert "Acme requires SAML SSO" in report.safe_prompt
    assert "secret-token-value" not in report.safe_prompt
    assert "medical coverage claim" not in report.safe_prompt
    assert "production-api-token" in report.blocked_memory_ids
    assert "personal-medical-coverage" in report.blocked_memory_ids


def test_report_contains_memguard_trust_and_policy_evidence(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    payload = report.to_dict()
    requirement = next(item for item in payload["items"] if item["id"] == "acme-sso-requirement")

    assert requirement["trust"]["score"] is not None
    assert requirement["policy"]["action"] == "allow"
    assert requirement["widemem"]["final_score"] != requirement["trust"]["score"]


def test_as_of_controls_widemem_recency_scores(tmp_path):
    current = run_demo(work_dir=tmp_path / "current", as_of=AS_OF)
    future = run_demo(work_dir=tmp_path / "future", as_of=datetime(2027, 8, 5, tzinfo=timezone.utc))

    assert future.by_id("legacy-vendor-contract").widemem.recency < current.by_id("legacy-vendor-contract").widemem.recency


def test_single_handover_query_produces_distinct_similarity_scores(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)

    assert len({item.widemem.similarity for item in report.items}) > 1


def test_all_synthetic_memories_have_the_expected_governance_decision(tmp_path):
    report = run_demo(work_dir=tmp_path, as_of=AS_OF)
    expected = {
        "acme-sso-requirement": Decision.TRANSFER,
        "northstar-escalation": Decision.TRANSFER,
        "support-triage-runbook": Decision.TRANSFER,
        "acme-integration-owner": Decision.TRANSFER,
        "renewal-risk": Decision.TRANSFER,
        "incident-template": Decision.TRANSFER,
        "billing-exception": Decision.TRANSFER,
        "onboarding-checklist": Decision.TRANSFER,
        "salesforce-sync": Decision.TRANSFER,
        "weekly-status-format": Decision.TRANSFER,
        "contract-renewal-window": Decision.TRANSFER,
        "data-export-limits": Decision.TRANSFER,
        "partner-contact": Decision.TRANSFER,
        "product-feedback": Decision.TRANSFER,
        "training-recording": Decision.TRANSFER,
        "priority-definition": Decision.TRANSFER,
        "legacy-vendor-contract": Decision.ARCHIVE,
        "expired-refund-policy": Decision.ARCHIVE,
        "obsolete-price-list": Decision.ARCHIVE,
        "past-quarter-target": Decision.ARCHIVE,
        "old-migration-plan": Decision.ARCHIVE,
        "personal-medical-coverage": Decision.DELETE_OR_ISOLATE,
        "personal-phone-number": Decision.DELETE_OR_ISOLATE,
        "family-schedule": Decision.DELETE_OR_ISOLATE,
        "private-job-search": Decision.DELETE_OR_ISOLATE,
        "production-api-token": Decision.RESTRICTED_REVIEW,
        "customer-bank-account": Decision.RESTRICTED_REVIEW,
        "passport-scan": Decision.RESTRICTED_REVIEW,
        "unclear-relationship-note": Decision.RESTRICTED_REVIEW,
        "unverified-rumor": Decision.RESTRICTED_REVIEW,
    }

    assert {item.memory.id: item.decision for item in report.items} == expected
