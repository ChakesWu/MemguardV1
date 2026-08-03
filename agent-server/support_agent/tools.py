"""LangGraph tools for customer support, with human approval before business writes."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from langchain.tools import ToolRuntime, tool
from langgraph.types import interrupt

from .policy import evaluate_refund_request
from .repository import SupportRepository


def _context_value(runtime: ToolRuntime, name: str) -> str:
    context = runtime.context or {}
    value = context.get(name) if isinstance(context, dict) else getattr(context, name, None)
    if not value:
        raise ValueError(f"Missing trusted {name} in runtime context")
    return str(value)


def _idempotency_key(runtime: ToolRuntime, order_id: str, reason: str) -> str:
    if runtime.tool_call_id:
        return f"request_refund:{runtime.tool_call_id}"
    payload = f"{_context_value(runtime, 'tenant_id')}:{_context_value(runtime, 'actor_id')}:{order_id}:{reason}"
    return f"request_refund:{hashlib.sha256(payload.encode()).hexdigest()}"


def build_support_tools(repository: SupportRepository):
    """Build tenant-scoped LangChain tools. Tenant and actor only come from graph runtime context."""

    @tool
    def get_order(order_id: str, runtime: ToolRuntime) -> dict[str, Any]:
        """Look up the current order facts for an order ID."""
        tenant_id = _context_value(runtime, "tenant_id")
        order = repository.get_order(tenant_id, order_id)
        if not order:
            return {"status": "not_found", "order_id": order_id}
        return {
            "status": "found",
            "order_id": order.order_id,
            "customer_id": order.customer_id,
            "product": order.product,
            "order_status": order.status,
            "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
            "payment_status": order.payment_status,
        }

    @tool
    def request_refund(order_id: str, reason: str, defective_item: bool, runtime: ToolRuntime) -> dict[str, Any]:
        """Request a refund or manual review. A human must approve before any business record is written."""
        tenant_id = _context_value(runtime, "tenant_id")
        actor_id = _context_value(runtime, "actor_id")
        order = repository.get_order(tenant_id, order_id)
        if not order:
            return {"status": "not_found", "order_id": order_id}
        policy = repository.get_active_policy(tenant_id, "refund-policy")
        if not policy:
            return {"status": "blocked", "reason": "No active refund policy is available."}

        decision = evaluate_refund_request(
            order=order,
            policy=policy,
            memories=repository.memories_for_owner(tenant_id, order.customer_id, "refund_exception"),
            requested_at=datetime.now(timezone.utc),
            defective_item=defective_item,
        )
        if decision.outcome == "ineligible":
            return {"status": "ineligible", "reason": decision.reason, "policy_version": decision.policy_version}

        approval = interrupt(
            {
                "kind": "approval_required",
                "action": "request_refund",
                "arguments": {"order_id": order_id, "reason": reason, "defective_item": defective_item},
                "policy_decision": decision.outcome,
                "policy_version": decision.policy_version,
                "evidence_memory_version_ids": decision.evidence_memory_version_ids,
                "allowed_decisions": ["approve", "edit", "reject"],
            }
        )
        if not isinstance(approval, dict):
            return {"status": "rejected", "reason": "Approval response was invalid."}
        if approval.get("decision") == "reject":
            return {"status": "rejected", "reason": "The human reviewer rejected this request."}
        if approval.get("decision") == "edit":
            return {"status": "needs_revision", "reason": "The human reviewer requested changes before approval."}
        if approval.get("decision") != "approve":
            return {"status": "rejected", "reason": "Approval response was invalid."}

        status = "manual_review_requested" if decision.outcome == "manual_review" else "refund_requested"
        action = repository.create_action_once(
            tenant_id=tenant_id,
            idempotency_key=_idempotency_key(runtime, order_id, reason),
            action_type="request_refund",
            order_id=order_id,
            payload={
                "reason": reason,
                "defective_item": defective_item,
                "requested_by": actor_id,
                "policy_version": decision.policy_version,
                "evidence_memory_version_ids": decision.evidence_memory_version_ids,
            },
            status=status,
        )
        return {"status": action.status, "action_id": action.action_id, "order_id": order_id, "reason": decision.reason}

    return (get_order, request_refund)
