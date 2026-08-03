import pathlib
import sys
from datetime import datetime, timezone


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))

from support_agent.domain import MemoryRecord, Order, PolicyDocument
from support_agent.policy import evaluate_refund_request


TENANT_ID = "acme-dev"


def test_expired_exception_cannot_override_current_refund_policy() -> None:
    order = Order(
        tenant_id=TENANT_ID,
        order_id="ORD-4821",
        customer_id="CUS-1042",
        product="Noise-cancelling headphones",
        status="delivered",
        delivered_at=datetime(2026, 7, 5, 10, tzinfo=timezone.utc),
        payment_status="paid",
        shipping_address={"city": "Hong Kong"},
    )
    policy = PolicyDocument(
        tenant_id=TENANT_ID,
        document_id="refund-policy",
        version="v2",
        effective_from=datetime(2026, 7, 1, tzinfo=timezone.utc),
        policy={"standard_refund_days": 14, "defective_item_action": "manual_review_after_window"},
        status="active",
    )
    expired_exception = MemoryRecord(
        tenant_id=TENANT_ID,
        memory_id="MEM-EXCEPTION-77",
        version_id="MEM-EXCEPTION-77-v1",
        owner_id="CUS-1042",
        kind="refund_exception",
        value={"refund_window_days": 30},
        source_type="support_agent_note",
        source_id="TICKET-8842",
        valid_from=datetime(2026, 6, 15, tzinfo=timezone.utc),
        valid_until=datetime(2026, 7, 20, 23, 59, 59, tzinfo=timezone.utc),
        supersedes_version_id=None,
        trust_level="medium",
        status="expired",
    )

    decision = evaluate_refund_request(
        order=order,
        policy=policy,
        memories=[expired_exception],
        requested_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
        defective_item=True,
    )

    assert decision.outcome == "manual_review"
    assert "expired" in decision.reason.lower()
    assert decision.evidence_memory_version_ids == ("MEM-EXCEPTION-77-v1",)


def test_active_exception_extends_refund_window() -> None:
    order = Order(
        tenant_id=TENANT_ID,
        order_id="ORD-1",
        customer_id="CUS-1",
        product="Keyboard",
        status="delivered",
        delivered_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
        payment_status="paid",
        shipping_address={},
    )
    policy = PolicyDocument(TENANT_ID, "refund-policy", "v2", datetime(2026, 7, 1, tzinfo=timezone.utc), {"standard_refund_days": 14}, "active")
    active_exception = MemoryRecord(TENANT_ID, "MEM-1", "MEM-1-v2", "CUS-1", "refund_exception", {"refund_window_days": 30}, "support_ticket", "T-1", None, datetime(2026, 8, 10, tzinfo=timezone.utc), None, "high", "active")

    decision = evaluate_refund_request(
        order=order,
        policy=policy,
        memories=[active_exception],
        requested_at=datetime(2026, 7, 28, tzinfo=timezone.utc),
        defective_item=False,
    )

    assert decision.outcome == "eligible"
    assert decision.evidence_memory_version_ids == ("MEM-1-v2",)
