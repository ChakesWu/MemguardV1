"""Idempotent local data for the support-agent baseline."""

from __future__ import annotations

from datetime import datetime, timezone

from .domain import Customer, MemoryRecord, Order, PolicyDocument
from .repository import SupportRepository


def seed_baseline_data(repository: SupportRepository, tenant_id: str = "acme-dev") -> None:
    repository.upsert_customer(Customer(tenant_id, "CUS-1042", "Alex Chen", "VIP", "active"))
    repository.upsert_order(Order(tenant_id, "ORD-4821", "CUS-1042", "Noise-cancelling headphones", "delivered", datetime(2026, 7, 5, 10, tzinfo=timezone.utc), "paid", {"city": "Hong Kong"}))
    repository.upsert_policy(PolicyDocument(tenant_id, "refund-policy", "v2", datetime(2026, 7, 1, tzinfo=timezone.utc), {"standard_refund_days": 14, "defective_item_action": "manual_review_after_window"}, "active"))
    try:
        repository.insert_memory(MemoryRecord(tenant_id, "MEM-EXCEPTION-77", "MEM-EXCEPTION-77-v1", "CUS-1042", "refund_exception", {"refund_window_days": 30, "scope": "one_future_order"}, "support_agent_note", "TICKET-8842", datetime(2026, 6, 15, tzinfo=timezone.utc), datetime(2026, 7, 20, 23, 59, 59, tzinfo=timezone.utc), None, "medium", "expired"))
    except Exception:
        pass
    try:
        repository.insert_memory(MemoryRecord(tenant_id, "MEM-SUMMARY-31", "MEM-SUMMARY-31-v1", "CUS-1042", "support_summary", "Customer has a 30-day refund exception.", "agent_generated_summary", "TICKET-8842", datetime(2026, 6, 15, tzinfo=timezone.utc), None, None, "low", "active"))
    except Exception:
        pass
