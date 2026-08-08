import json
import pathlib
import sys
import threading
from uuid import UUID


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.auth import TenantPrincipal
import pytest

from app.agent_proxy import (
    _governed_output_from_sse,
    _persist_governed_output,
    extract_sse_payloads,
    create_tenant_thread_id,
    governed_output_records,
    inject_trusted_agent_context,
    is_allowed_thread_path,
)


def test_agent_proxy_decodes_crlf_delimited_sse_payloads() -> None:
    payload = {"values": {"messages": []}}
    buffer, payloads = extract_sse_payloads(b"", f"event: values\r\ndata: {json.dumps(payload)}\r\n\r\n".encode())

    assert buffer == b""
    assert payloads == [payload]


def test_persist_governed_output_persists_events_and_trace() -> None:
    report = {
        "items": [{"memory_id": "order:ORD-4821", "source": {"type": "support_order_db", "id": "ORD-4821"}}],
        "output_evidence": {"valid_links": [{
            "memory_id": "order:ORD-4821", "role": "factual_support",
            "trust": {"score": 91.5, "level": "high"}, "policy": {"action": "allow"},
            "influence": {"score": 1.0}, "prompt_included": True,
        }]},
    }

    class Gateway:
        def __init__(self) -> None:
            self._lock = threading.Lock()
            self.events = []
            self.persisted_events = []
            self.persisted_traces = []

        def _persist_event(self, event) -> None:
            self.persisted_events.append(event)

        def create_decision_trace(self, trace) -> None:
            pass

        def _persist_trace(self, trace) -> None:
            self.persisted_traces.append(trace)

    gateway = Gateway()
    _persist_governed_output(gateway, tenant_id="acme-dev", agent_id="customer_support_agent", session_id="thread-1", user_input="Refund ORD-4821", answer="ORD-4821 was delivered.", report=report)

    assert len(gateway.persisted_events) == 1
    assert len(gateway.persisted_traces) == 1


def test_agent_proxy_extracts_evidence_from_langgraph_values_state() -> None:
    report = {"output_evidence": {"valid_links": []}}
    payload = {"values": {"messages": [{
        "type": "ai",
        "content": "ORD-4821 was delivered.",
        "additional_kwargs": {"memguard_output_evidence": report},
    }]}}

    assert _governed_output_from_sse(payload) == ("ORD-4821 was delivered.", report)


def test_governed_output_records_create_console_read_evidence() -> None:
    report = {
        "items": [{"memory_id": "order:ORD-4821", "source": {"type": "support_order_db", "id": "ORD-4821"}}],
        "output_evidence": {
            "valid_links": [{
                "memory_id": "order:ORD-4821",
                "role": "factual_support",
                "trust": {"score": 91.5, "level": "high"},
                "policy": {"action": "allow"},
                "influence": {"score": 1.0},
                "prompt_included": True,
            }],
        },
    }

    events, trace = governed_output_records(
        tenant_id="acme-dev",
        agent_id="customer_support_agent",
        session_id="thread-1",
        user_input="Refund ORD-4821",
        answer="ORD-4821 was delivered.",
        report=report,
    )

    assert len(events) == 1
    assert events[0].event_type == "read"
    assert events[0].memory_id == "order:ORD-4821"
    assert events[0].trust_score == 91.5
    assert events[0].metadata["evidence_role"] == "factual_support"
    assert trace.tenant_id == "acme-dev"
    assert trace.session_id == "thread-1"
    assert trace.input_memory_events == [events[0].event_id]


def test_agent_proxy_overwrites_browser_supplied_identity() -> None:
    principal = TenantPrincipal(
        subject="keycloak-user-123",
        tenant_id="acme-dev",
        claims={"sub": "keycloak-user-123", "tenant_id": "acme-dev"},
    )
    payload = {
        "input": {"messages": [{"role": "user", "content": "Refund ORD-4821"}]},
        "config": {"configurable": {"tenant_id": "other-tenant", "actor_id": "attacker", "ui_mode": "chat"}},
        "context": {"tenant_id": "other-tenant", "actor_id": "attacker"},
    }

    secured = inject_trusted_agent_context(payload, principal)

    assert "config" not in secured
    assert secured["context"] == {"tenant_id": "acme-dev", "actor_id": "keycloak-user-123"}


def test_agent_proxy_does_not_mutate_original_browser_payload() -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    payload = {"config": {"configurable": {"tenant_id": "other-tenant"}}}

    inject_trusted_agent_context(payload, principal)

    assert payload["config"]["configurable"]["tenant_id"] == "other-tenant"


def test_agent_proxy_generates_thread_ids_owned_by_the_token_tenant() -> None:
    acme = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    other = TenantPrincipal(subject="user-2", tenant_id="other-tenant", claims={})
    thread_id = create_tenant_thread_id(acme)

    UUID(thread_id)
    assert is_allowed_thread_path(f"threads/{thread_id}/history", acme)
    assert not is_allowed_thread_path(f"threads/{thread_id}/history", other)


@pytest.mark.parametrize("path", ["threads/search", "threads/count", "threads/prune"])
def test_agent_proxy_blocks_global_thread_enumeration(path: str) -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})

    assert not is_allowed_thread_path(path, principal)


def test_agent_proxy_rejects_dot_segments_that_could_normalize_to_global_routes() -> None:
    principal = TenantPrincipal(subject="user-1", tenant_id="acme-dev", claims={})
    thread_id = create_tenant_thread_id(principal)

    assert not is_allowed_thread_path(f"threads/{thread_id}/../search", principal)
