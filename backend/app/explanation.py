"""Deterministic, evidence-backed explanations for agent outputs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SEVERITY = {
    "observed": 0,
    "stale": 1,
    "conflict": 2,
    "stale_conflict": 3,
    "evidence_gap": 4,
}


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalized(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def _summary(status: str, findings: list[dict[str, Any]]) -> str:
    if findings and all(
        finding.get("included_in_prompt") is False for finding in findings
    ):
        return (
            "The memory was retrieved but excluded from model context; "
            "it was not available to the generation step."
        )
    if status == "stale_conflict":
        return (
            "A retrieved memory conflicted with the current fact and exceeded "
            "its declared freshness limit."
        )
    if status == "conflict":
        return "A retrieved memory conflicted with the current fact."
    if status == "stale":
        return "A retrieved memory exceeded its declared freshness limit."
    if findings:
        return (
            "Retrieved memory provenance was observed; no additional deterministic "
            "finding was available."
        )
    return "No retrieved-memory comparison was available for this output."


def explain_trace(
    trace: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    missing_evidence_event_ids: list[str],
) -> dict[str, Any]:
    """Build a truthful explanation from persisted trace evidence only."""
    metadata = trace.get("metadata") or {}
    current_facts = metadata.get("current_facts") or {}
    trace_time = _parse_time(trace.get("timestamp"))
    findings: list[dict[str, Any]] = []

    for item in evidence_items:
        item_metadata = item.get("metadata") or {}
        if item.get("side") != "input":
            continue
        if item_metadata.get("evidence_role") != "retrieved_memory":
            continue

        fact_key = item_metadata.get("fact_key")
        finding: dict[str, Any] = {
            "kind": "observed",
            "event_id": item.get("event_id", ""),
            "memory_key": item.get("memory_key", ""),
        }
        for key in (
            "fact_key",
            "source_type",
            "source_id",
            "retrieval_rank",
            "retrieval_score",
            "included_in_prompt",
            "memory_created_at",
            "memory_last_verified_at",
            "max_age_seconds",
        ):
            if item_metadata.get(key) is not None:
                finding[key] = item_metadata[key]

        conflict = False
        captured = item_metadata.get("_after_value")
        if (
            fact_key
            and isinstance(captured, dict)
            and fact_key in captured
            and fact_key in current_facts
            and captured[fact_key] is not None
            and current_facts[fact_key] is not None
        ):
            remembered_value = captured[fact_key]
            current_value = current_facts[fact_key]
            finding["remembered_value"] = remembered_value
            finding["current_value"] = current_value
            conflict = _normalized(remembered_value) != _normalized(current_value)

        stale = False
        verified_at = _parse_time(item_metadata.get("memory_last_verified_at"))
        max_age = item_metadata.get("max_age_seconds")
        if (
            trace_time is not None
            and verified_at is not None
            and isinstance(max_age, (int, float))
            and not isinstance(max_age, bool)
        ):
            age_seconds = max(0, int((trace_time - verified_at).total_seconds()))
            finding["age_seconds"] = age_seconds
            stale = age_seconds > max_age

        if stale and conflict:
            finding["kind"] = "stale_conflict"
        elif conflict:
            finding["kind"] = "conflict"
        elif stale:
            finding["kind"] = "stale"
        findings.append(finding)

    if missing_evidence_event_ids:
        status = "evidence_gap"
        summary = (
            "Some linked evidence records are missing, so this output explanation "
            "is incomplete."
        )
    else:
        status = max(
            (finding["kind"] for finding in findings),
            key=lambda kind: _SEVERITY[kind],
            default="observed",
        )
        summary = _summary(status, findings)

    return {
        "basis": "recorded_evidence",
        "causality_claim": "not_proven",
        "status": status,
        "summary": summary,
        "findings": findings,
        "missing_evidence_event_ids": list(missing_evidence_event_ids),
    }
