#!/usr/bin/env python3
"""Classify a departing employee's Widemem records for safe agent handover."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SDK_ROOT = ROOT / "sdk"
WIDEMEM_ROOT = ROOT / "widemem-ai"
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))
if str(WIDEMEM_ROOT) not in sys.path:
    sys.path.insert(0, str(WIDEMEM_ROOT))

from memguard.governance import (
    ConflictStatus,
    DataClassification,
    EvidenceEvaluation,
    GovernanceContext,
    GovernancePolicy,
    MemoryEvidence,
    MemoryGovernanceEngine,
    PolicyAction,
    RetrievalSignals,
)

from widemem.core.memory import WideMemory
from widemem.core.types import EmbeddingConfig, LLMConfig, MemoryConfig, VectorStoreConfig
from widemem.providers.embeddings.base import BaseEmbedder
from widemem.providers.llm.base import BaseLLM
from widemem.retrieval.temporal import score_and_rank
from widemem.storage.vector.faiss_store import FAISSVectorStore


EMPLOYEE_ID = "departing-support-agent"
STALE_AFTER_DAYS = 180
HANDOVER_QUERY = "employee handover support customer business requirements project policy process private personal sensitive credential"


class Decision(str, Enum):
    TRANSFER = "transfer"
    ARCHIVE = "archive"
    DELETE_OR_ISOLATE = "delete_or_isolate"
    RESTRICTED_REVIEW = "restricted_review"


@dataclass(frozen=True)
class EmployeeMemory:
    id: str
    content: str
    importance: float
    created_at: datetime


@dataclass(frozen=True)
class WidememScore:
    similarity: float
    importance: float
    recency: float
    final_score: float


@dataclass(frozen=True)
class ClassifiedMemory:
    memory: EmployeeMemory
    widemem: WidememScore
    decision: Decision
    reason: str
    governance: EvidenceEvaluation


@dataclass(frozen=True)
class OffboardingReport:
    generated_at: datetime
    items: tuple[ClassifiedMemory, ...]
    safe_prompt: str
    blocked_memory_ids: tuple[str, ...]
    governance_report: dict

    def by_id(self, memory_id: str) -> ClassifiedMemory:
        return next(item for item in self.items if item.memory.id == memory_id)

    def summary(self) -> dict[str, int]:
        return {decision.value: sum(item.decision is decision for item in self.items) for decision in Decision}

    def review_queue(self) -> tuple[ClassifiedMemory, ...]:
        pending = (item for item in self.items if item.decision is Decision.RESTRICTED_REVIEW)
        return tuple(sorted(pending, key=lambda item: item.widemem.final_score, reverse=True))

    def to_dict(self) -> dict:
        governance_by_id = {item["memory_id"]: item for item in self.governance_report["items"]}
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary(),
            "review_queue": [item.memory.id for item in self.review_queue()],
            "included_memory_ids": [
                item.memory.id for item in self.items if item.memory.id not in self.blocked_memory_ids
            ],
            "blocked_memory_ids": list(self.blocked_memory_ids),
            "items": [
                {
                    "id": item.memory.id,
                    "content": _display_content(item),
                    "decision": item.decision.value,
                    "reason": item.reason,
                    "widemem": asdict(item.widemem),
                    "trust": governance_by_id[item.memory.id]["trust"],
                    "policy": governance_by_id[item.memory.id]["policy"],
                    "influence": governance_by_id[item.memory.id]["influence"],
                }
                for item in self.items
            ],
        }


class DeterministicEmbedder(BaseEmbedder):
    """Small local embedder for a network-free, repeatable demo."""

    def __init__(self, dimensions: int = 96) -> None:
        super().__init__(EmbeddingConfig(dimensions=dimensions), max_retries=1, retry_delay=0)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


class NoOpLLM(BaseLLM):
    def __init__(self) -> None:
        super().__init__(LLMConfig(provider="openai", model="offboarding-demo"), max_retries=1, retry_delay=0)

    def _generate(self, prompt: str, system: str | None = None) -> str:
        return "{}"

    def _generate_json(self, prompt: str, system: str | None = None) -> dict:
        return {"facts": []}


def _at(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


def employee_memories() -> tuple[EmployeeMemory, ...]:
    return (
        EmployeeMemory("acme-sso-requirement", "Business: Acme requires SAML SSO and SCIM provisioning before contract renewal.", 10, _at(2026, 7, 29)),
        EmployeeMemory("northstar-escalation", "Business: Northstar outage escalations go to the platform on-call channel within fifteen minutes.", 9, _at(2026, 7, 24)),
        EmployeeMemory("support-triage-runbook", "Business: Use the support triage runbook for duplicate charge investigations.", 8, _at(2026, 7, 17)),
        EmployeeMemory("acme-integration-owner", "Business: Acme integration questions are owned by the Enterprise Success team.", 8, _at(2026, 7, 16)),
        EmployeeMemory("renewal-risk", "Business: Contoso renewal is at risk until their audit export latency is resolved.", 9, _at(2026, 7, 11)),
        EmployeeMemory("incident-template", "Business: Use the incident template with impact, timeline, owner, and next update time.", 7, _at(2026, 7, 8)),
        EmployeeMemory("billing-exception", "Business: Finance approved a one-time invoice consolidation for Globex in August.", 8, _at(2026, 7, 5)),
        EmployeeMemory("onboarding-checklist", "Business: Enterprise onboarding requires legal review before production access is enabled.", 8, _at(2026, 7, 1)),
        EmployeeMemory("salesforce-sync", "Business: Update the Salesforce case after each customer-facing escalation.", 7, _at(2026, 6, 29)),
        EmployeeMemory("weekly-status-format", "Business: Weekly account status updates include blockers, owner, ETA, and customer impact.", 6, _at(2026, 6, 23)),
        EmployeeMemory("contract-renewal-window", "Business: Renewal notice must be sent ninety days before the contract end date.", 8, _at(2026, 6, 18)),
        EmployeeMemory("data-export-limits", "Business: Standard data exports support one million records per job.", 7, _at(2026, 6, 12)),
        EmployeeMemory("partner-contact", "Business: Escalate CloudBridge connector failures to the partner support queue.", 7, _at(2026, 6, 4)),
        EmployeeMemory("product-feedback", "Business: Customers repeatedly request CSV columns for source and retention policy.", 6, _at(2026, 5, 28)),
        EmployeeMemory("training-recording", "Business: The new-agent training recording covers case assignment and SLA updates.", 6, _at(2026, 5, 19)),
        EmployeeMemory("priority-definition", "Business: P1 means a production outage affecting more than one customer.", 9, _at(2026, 5, 12)),
        EmployeeMemory("legacy-vendor-contract", "Business: The old Telemetric vendor contract ended and should not be renewed.", 7, _at(2026, 1, 15)),
        EmployeeMemory("expired-refund-policy", "Business: The 2024 refund policy allowed a thirty-day window for all customers.", 8, _at(2024, 11, 1)),
        EmployeeMemory("obsolete-price-list", "Business: The 2024 price list quoted the retired Starter plan.", 7, _at(2024, 8, 5)),
        EmployeeMemory("past-quarter-target", "Business: The Q1 2025 support target was first response within four hours.", 5, _at(2025, 1, 5)),
        EmployeeMemory("old-migration-plan", "Business: The 2024 migration plan used the deprecated import API.", 6, _at(2024, 7, 1)),
        EmployeeMemory("personal-medical-coverage", "Private: My medical coverage claim is pending with a clinic.", 10, _at(2026, 8, 1)),
        EmployeeMemory("personal-phone-number", "Private: My personal phone number is 555-0108 for weekend messages.", 9, _at(2026, 7, 30)),
        EmployeeMemory("family-schedule", "Private: My family schedule requires me to leave early on Thursdays.", 7, _at(2026, 7, 22)),
        EmployeeMemory("private-job-search", "Private: I am interviewing with another company next month.", 9, _at(2026, 7, 20)),
        EmployeeMemory("production-api-token", "Business: Production API token for the migration service is stored in this note: secret-token-value.", 10, _at(2026, 7, 31)),
        EmployeeMemory("customer-bank-account", "Business: Customer bank account details were shared during the billing dispute.", 10, _at(2026, 7, 18)),
        EmployeeMemory("passport-scan", "Business: A passport scan was attached to the enterprise verification case.", 10, _at(2026, 7, 14)),
        EmployeeMemory("unclear-relationship-note", "Unclear: maybe the customer prefers the old workflow, but this was not confirmed.", 5, _at(2026, 7, 26)),
        EmployeeMemory("unverified-rumor", "Unclear: possibly the vendor will discontinue the connector soon.", 5, _at(2026, 7, 9)),
    )


def _governance_metadata(memory: EmployeeMemory, as_of: datetime) -> dict:
    content = memory.content.lower()
    if any(signal in content for signal in ("private:", "personal:", "my medical", "my family", "interviewing")):
        return {
            "source_type": "employee_note",
            "writer_id": "alex",
            "conflict_status": ConflictStatus.NONE,
            "allowed_purposes": ("employee_handover",),
            "data_classification": DataClassification.PRIVATE_EMPLOYEE,
        }
    if any(signal in content for signal in ("token", "secret", "password", "credential")):
        return {
            "source_type": "company_record",
            "writer_id": "alex",
            "conflict_status": ConflictStatus.NONE,
            "allowed_purposes": ("employee_handover",),
            "data_classification": DataClassification.SECRET,
        }
    if any(signal in content for signal in ("bank account", "passport")):
        return {
            "source_type": "company_record",
            "writer_id": "alex",
            "conflict_status": ConflictStatus.NONE,
            "allowed_purposes": ("employee_handover",),
            "data_classification": DataClassification.RESTRICTED,
        }
    if any(signal in content for signal in ("unclear:", "maybe", "possibly", "not confirmed")):
        return {
            "source_type": "unverified_note",
            "writer_id": None,
            "conflict_status": ConflictStatus.UNKNOWN,
            "allowed_purposes": None,
            "data_classification": DataClassification.INTERNAL,
        }
    return {
        "source_type": "company_record",
        "writer_id": "alex",
        "conflict_status": ConflictStatus.NONE,
        "allowed_purposes": ("employee_handover",),
        "data_classification": DataClassification.INTERNAL,
        "valid_until": memory.created_at + timedelta(days=STALE_AFTER_DAYS),
    }


def _governance_evidence(memory: EmployeeMemory, score: WidememScore, as_of: datetime) -> MemoryEvidence:
    metadata = _governance_metadata(memory, as_of)
    return MemoryEvidence(
        memory_id=memory.id,
        tenant_id="demo-company",
        content=memory.content,
        created_at=memory.created_at,
        verified_at=memory.created_at,
        retrieval=RetrievalSignals(
            similarity=score.similarity,
            importance=score.importance,
            recency=score.recency,
            retrieval_score=score.final_score,
            retrieved=True,
        ),
        **metadata,
    )


def _governance_policy() -> GovernancePolicy:
    return GovernancePolicy(
        policy_id="employee-handover-v1",
        source_scores={"company_record": 90.0, "employee_note": 70.0},
        writer_scores={"alex": 80.0},
        max_age_days={"company_record": STALE_AFTER_DAYS, "employee_note": 365},
    )


def _offboarding_decision(evaluation: EvidenceEvaluation) -> Decision:
    action = evaluation.policy.action
    reasons = set(evaluation.policy.reason_codes)
    if "classification:private_employee" in reasons:
        return Decision.DELETE_OR_ISOLATE
    if action is PolicyAction.BLOCK and any(reason.startswith("lifecycle:") for reason in reasons):
        return Decision.ARCHIVE
    if action in {PolicyAction.QUARANTINE, PolicyAction.REVIEW_REQUIRED}:
        return Decision.RESTRICTED_REVIEW
    if action is PolicyAction.BLOCK:
        return Decision.DELETE_OR_ISOLATE
    return Decision.TRANSFER


def _display_content(item: ClassifiedMemory) -> str:
    if item.decision is Decision.DELETE_OR_ISOLATE:
        return "[redacted: private employee information]"
    if item.decision is Decision.RESTRICTED_REVIEW:
        return "[redacted: restricted review required]"
    return item.memory.content


def _open_widemem(work_dir: Path) -> WideMemory:
    work_dir.mkdir(parents=True, exist_ok=True)
    embedder = DeterministicEmbedder()
    vector_store = FAISSVectorStore(VectorStoreConfig(path=str(work_dir / "vectors")), dimensions=embedder.dimensions)
    return WideMemory(
        config=MemoryConfig(history_db_path=str(work_dir / "history.db")),
        llm=NoOpLLM(),
        embedder=embedder,
        vector_store=vector_store,
    )


def _import_records(memory: WideMemory, records: Iterable[EmployeeMemory]) -> None:
    payload = {
        "memories": [
            {
                "id": record.id,
                "content": record.content,
                "importance": record.importance,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.created_at.isoformat(),
                "user_id": EMPLOYEE_ID,
                "agent_id": EMPLOYEE_ID,
            }
            for record in records
        ]
    }
    memory.import_json(json.dumps(payload))


def _scores(memory: WideMemory, records: Iterable[EmployeeMemory], as_of: datetime) -> dict[str, WidememScore]:
    results = memory.search(HANDOVER_QUERY, user_id=EMPLOYEE_ID, top_k=100)
    scoring, similarity_first = memory._adapt_scoring(HANDOVER_QUERY, memory.config.scoring)
    ranked = score_and_rank(
        list(results),
        config=scoring,
        now=as_of,
        similarity_first=similarity_first,
        similarity_boost=memory.config.get_retrieval_preset()["similarity_boost"],
    )
    by_content = {
        result.memory.content: WidememScore(
            similarity=result.similarity_score,
            importance=result.importance_score,
            recency=result.temporal_score,
            final_score=result.final_score,
        )
        for result in ranked
    }
    scores = {}
    for record in records:
        score = by_content.get(record.content)
        if score is None:
            raise RuntimeError(f"Widemem did not retrieve expected memory: {record.id}")
        scores[record.id] = score
    return scores


def run_demo(work_dir: Path | str, as_of: datetime | None = None) -> OffboardingReport:
    report_time = as_of or datetime.now(timezone.utc)
    records = employee_memories()
    memory = _open_widemem(Path(work_dir))
    try:
        _import_records(memory, records)
        scores = _scores(memory, records, report_time)
        engine = MemoryGovernanceEngine(_governance_policy())
        governance_run = engine.evaluate_and_build_prompt(
            "Prepare a safe customer-support handover for the next employee.",
            (_governance_evidence(record, scores[record.id], report_time) for record in records),
            GovernanceContext(
                tenant_id="demo-company",
                agent_id="successor-support-agent",
                purpose="employee_handover",
                evaluated_at=report_time,
            ),
        )
        evaluations = {item.evidence.memory_id: item for item in governance_run.evaluations}
        items = []
        for record in records:
            score = scores[record.id]
            evaluation = evaluations[record.id]
            decision = _offboarding_decision(evaluation)
            retains_content = evaluation.policy.action in {PolicyAction.ALLOW, PolicyAction.WARN}
            safe_record = record if retains_content else replace(record, content="[redacted: governed content]")
            safe_evaluation = evaluation if retains_content else replace(
                evaluation,
                evidence=replace(evaluation.evidence, content=None),
            )
            items.append(ClassifiedMemory(safe_record, score, decision, evaluation.policy.explanation, safe_evaluation))
        return OffboardingReport(
            generated_at=report_time,
            items=tuple(items),
            safe_prompt=governance_run.gate.prompt,
            blocked_memory_ids=governance_run.gate.blocked_memory_ids,
            governance_report=governance_run.report.to_dict(),
        )
    finally:
        memory.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".offboarding-demo")
    parser.add_argument("--json", action="store_true", help="Print the full decision report as JSON.")
    args = parser.parse_args()
    report = run_demo(args.work_dir)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return
    print(json.dumps(report.summary(), indent=2))
    for item in report.items:
        print(f"{item.decision.value:20} {item.memory.id:28} score={item.widemem.final_score:.3f} {item.reason}")


if __name__ == "__main__":
    main()
