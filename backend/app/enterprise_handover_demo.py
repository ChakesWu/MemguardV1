"""A real, deterministic enterprise offboarding scenario for the MemGuard console."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    GovernanceContext,
    GovernancePolicy,
    HandoverEngine,
    HandoverMemory,
    MemoryEvidence,
    MemoryOwner,
    TransferPolicy,
)


def _memory(
    memory_id: str,
    content: str,
    *,
    tenant_id: str,
    source_type: str,
    source_id: str,
    writer_id: str,
    owner: MemoryOwner,
    transfer_policy: TransferPolicy,
    business_owner: str,
    source_label: str,
    classification: DataClassification = DataClassification.INTERNAL,
    age_days: int = 2,
    valid_for_days: int | None = 180,
    redacted_content: str | None = None,
) -> HandoverMemory:
    now = datetime.now(timezone.utc)
    created_at = now - timedelta(days=age_days)
    valid_until = created_at + timedelta(days=valid_for_days) if valid_for_days is not None else None
    return HandoverMemory(
        evidence=MemoryEvidence(
            memory_id=memory_id,
            tenant_id=tenant_id,
            content=content,
            source_type=source_type,
            source_id=source_id,
            writer_id=writer_id,
            created_at=created_at,
            verified_at=created_at,
            valid_until=valid_until,
            conflict_status=ConflictStatus.NONE,
            allowed_purposes=("employee_handover",),
            data_classification=classification,
        ),
        owner=owner,
        transfer_policy=transfer_policy,
        business_owner=business_owner,
        source_label=source_label,
        redacted_content=redacted_content,
    )


def build_enterprise_handover_demo(tenant_id: str) -> dict:
    """Return a policy-evaluated handover manifest; no synthetic trust scores are used."""
    now = datetime.now(timezone.utc)
    policy = GovernancePolicy(
        policy_id="enterprise-handover-v1",
        source_scores={"company_system": 95.0, "employee_agent": 70.0},
        writer_scores={"system": 100.0, "alex": 80.0},
        max_age_days={"company_system": 365, "employee_agent": 180},
    )
    records = (
        _memory(
            "crm-acme-renewal-requirement",
            "Acme requires SAML SSO and SCIM provisioning before its renewal can close.",
            tenant_id=tenant_id,
            source_type="company_system",
            source_id="CRM:ACME-104",
            writer_id="system",
            owner=MemoryOwner.COMPANY_SYSTEM,
            transfer_policy=TransferPolicy.SOURCE_OF_TRUTH,
            business_owner="Revenue Operations",
            source_label="CRM / Acme account",
        ),
        _memory(
            "policy-escalation-response",
            "Production outages for enterprise accounts must be routed to Platform On-call within 15 minutes.",
            tenant_id=tenant_id,
            source_type="company_system",
            source_id="POLICY:INC-12",
            writer_id="system",
            owner=MemoryOwner.COMPANY_SYSTEM,
            transfer_policy=TransferPolicy.SOURCE_OF_TRUTH,
            business_owner="Support Operations",
            source_label="Published incident policy",
        ),
        _memory(
            "northstar-escalation-playbook",
            "Northstar outage escalations use the Platform On-call channel and include customer impact, owner, and next update time.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-support",
            writer_id="alex",
            owner=MemoryOwner.COMPANY,
            transfer_policy=TransferPolicy.TRANSFER_IF_ALLOWED,
            business_owner="Customer Success",
            source_label="Alex's support agent",
        ),
        _memory(
            "acme-integration-owner",
            "Acme integration questions are owned by the Enterprise Success team; coordinate the security review with Legal.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-support",
            writer_id="alex",
            owner=MemoryOwner.TEAM,
            transfer_policy=TransferPolicy.TRANSFER_IF_ALLOWED,
            business_owner="Enterprise Success",
            source_label="Alex's support agent",
        ),
        _memory(
            "alex-recurring-medical-care",
            "Alex has a recurring specialist appointment for a diagnosed medical condition every Thursday afternoon.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-private",
            writer_id="alex",
            owner=MemoryOwner.EMPLOYEE,
            transfer_policy=TransferPolicy.PROTECT,
            business_owner="Alex Chen",
            source_label="Alex's private agent memory",
            classification=DataClassification.PRIVATE_EMPLOYEE,
            redacted_content="Recurring medical-care schedule — exact diagnosis and appointment details protected.",
        ),
        _memory(
            "alex-family-caregiving",
            "Alex is unavailable on Tuesday mornings to care for a named family member receiving ongoing treatment.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-private",
            writer_id="alex",
            owner=MemoryOwner.EMPLOYEE,
            transfer_policy=TransferPolicy.PROTECT,
            business_owner="Alex Chen",
            source_label="Alex's private agent memory",
            classification=DataClassification.PRIVATE_EMPLOYEE,
            redacted_content="Family caregiving availability — family member and care details protected.",
        ),
        _memory(
            "acme-mixed-note",
            "Acme needs a security review before renewal. Alex prefers to call the customer personally after work.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-support",
            writer_id="alex",
            owner=MemoryOwner.COMPANY,
            transfer_policy=TransferPolicy.REDACT_AND_REVIEW,
            business_owner="Customer Success",
            source_label="Alex's support agent",
            redacted_content="Acme needs a security review before renewal. [Personal employee preference removed]",
        ),
        _memory(
            "migration-api-token",
            "Production API token for the migration service: secret-token-value.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-support",
            writer_id="alex",
            owner=MemoryOwner.COMPANY,
            transfer_policy=TransferPolicy.TRANSFER_IF_ALLOWED,
            business_owner="Platform Security",
            source_label="Alex's support agent",
            classification=DataClassification.SECRET,
        ),
        _memory(
            "legacy-refund-policy",
            "The 2024 refund policy allowed every customer a 30-day refund window.",
            tenant_id=tenant_id,
            source_type="employee_agent",
            source_id="AGENT:alex-support",
            writer_id="alex",
            owner=MemoryOwner.COMPANY,
            transfer_policy=TransferPolicy.TRANSFER_IF_ALLOWED,
            business_owner="Support Operations",
            source_label="Alex's support agent",
            age_days=420,
            valid_for_days=180,
        ),
    )
    report = HandoverEngine(policy).prepare(
        records,
        GovernanceContext(
            tenant_id=tenant_id,
            agent_id="successor-enterprise-agent",
            purpose="employee_handover",
            evaluated_at=now,
            actor_id="offboarding-manager",
        ),
    )
    return {
        "tenant_id": tenant_id,
        "generated_at": now.isoformat(),
        "policy_id": policy.policy_id,
        **report.to_dict(),
    }
