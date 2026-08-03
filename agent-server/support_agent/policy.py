"""Deterministic policy checks used before approval-gated support actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .domain import MemoryRecord, Order, PolicyDocument


@dataclass(frozen=True)
class RefundDecision:
    outcome: str
    reason: str
    policy_version: str
    evidence_memory_version_ids: tuple[str, ...]


def evaluate_refund_request(
    *,
    order: Order,
    policy: PolicyDocument,
    memories: list[MemoryRecord],
    requested_at: datetime,
    defective_item: bool,
) -> RefundDecision:
    """Evaluate a refund request using the active policy and valid customer exceptions."""
    if order.status != "delivered" or order.delivered_at is None:
        return RefundDecision("ineligible", "The order has not been delivered.", policy.version, ())

    exception_records = [memory for memory in memories if memory.kind == "refund_exception"]
    evidence_ids = tuple(memory.version_id for memory in exception_records)
    standard_days = int(policy.policy.get("standard_refund_days", 14))
    refund_days = standard_days
    valid_exceptions = []
    expired_exceptions = []

    for memory in exception_records:
        is_active = memory.status == "active"
        is_current = memory.valid_until is None or memory.valid_until >= requested_at
        if is_active and is_current and isinstance(memory.value, dict):
            valid_exceptions.append(memory)
            refund_days = max(refund_days, int(memory.value.get("refund_window_days", standard_days)))
        else:
            expired_exceptions.append(memory)

    deadline = order.delivered_at + timedelta(days=refund_days)
    if requested_at <= deadline:
        if valid_exceptions:
            return RefundDecision("eligible", f"Eligible under active refund exception and policy {policy.version}.", policy.version, evidence_ids)
        return RefundDecision("eligible", f"Eligible within the {standard_days}-day refund window in policy {policy.version}.", policy.version, evidence_ids)

    if defective_item and policy.policy.get("defective_item_action") == "manual_review_after_window":
        detail = " A related refund exception is expired and cannot extend the current window." if expired_exceptions else ""
        return RefundDecision("manual_review", f"Outside the refund window; a defective-item claim requires manual review.{detail}", policy.version, evidence_ids)

    detail = " An expired refund exception was not applied." if expired_exceptions else ""
    return RefundDecision("ineligible", f"Outside the refund window in policy {policy.version}.{detail}", policy.version, evidence_ids)
