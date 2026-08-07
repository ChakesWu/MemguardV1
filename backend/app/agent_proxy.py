"""Authenticated reverse proxy for the private LangGraph Agent Server."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from collections.abc import AsyncIterator
from copy import deepcopy
from re import fullmatch
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .auth import TenantPrincipal
from .services import DecisionTrace, MemoryEvent


router = APIRouter(prefix="/v1/agent-server", tags=["customer-support-agent"])
_HOP_BY_HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}


def governed_output_records(*, tenant_id: str, agent_id: str, session_id: str, user_input: str, answer: str, report: dict[str, Any]) -> tuple[list[MemoryEvent], DecisionTrace]:
    """Convert validated agent output evidence into the console's canonical records."""
    items = {item.get("memory_id"): item for item in report.get("items", []) if isinstance(item, dict)}
    links = report.get("output_evidence", {}).get("valid_links", [])
    trace_id = str(uuid4())
    events = []
    scores: dict[str, float] = {}
    for link in links if isinstance(links, list) else []:
        if not isinstance(link, dict) or link.get("prompt_included") is not True:
            continue
        memory_id = link.get("memory_id")
        trust = link.get("trust") if isinstance(link.get("trust"), dict) else {}
        policy = link.get("policy") if isinstance(link.get("policy"), dict) else {}
        influence = link.get("influence") if isinstance(link.get("influence"), dict) else {}
        item = items.get(memory_id) if isinstance(memory_id, str) else None
        source = item.get("source", {}) if isinstance(item, dict) else {}
        if not isinstance(memory_id, str) or not isinstance(trust.get("score"), (int, float)):
            continue
        event = MemoryEvent(
            event_id=str(uuid4()), tenant_id=tenant_id, agent_id=agent_id, memory_id=memory_id,
            trace_id=trace_id, event_type="read", source_type=str(source.get("type") or "governed_memory"),
            content="", content_hash="", policy_decision=str(policy.get("action") or "review_required"),
            trust_score=float(trust["score"]), created_at=datetime.now(timezone.utc).isoformat(),
            metadata={"evidence_role": link.get("role"), "source_id": source.get("id"), "trust_level": trust.get("level"), "policy_status": policy.get("action"), "influence_score": influence.get("score"), "prompt_included": True},
        )
        events.append(event)
        scores[memory_id] = float(influence.get("score") or 0.0)
    trace = DecisionTrace(
        trace_id=trace_id, tenant_id=tenant_id, agent_id=agent_id, session_id=session_id,
        timestamp=datetime.now(timezone.utc).isoformat(), input_memory_ids=[event.memory_id for event in events],
        input_memory_events=[event.event_id for event in events], user_input=user_input,
        llm_prompt_hash=sha256(user_input.encode()).hexdigest(), llm_output=answer,
        llm_output_hash=sha256(answer.encode()).hexdigest(), llm_model="customer_support_agent",
        output_memory_ids=[], output_memory_events=[], memory_influence_scores=scores,
        total_influence_score=round(sum(scores.values()) / len(scores), 3) if scores else 0.0,
        metadata={"governed_output_evidence": True},
    )
    return events, trace


def _governed_output_from_sse(payload: Any) -> tuple[str, dict[str, Any]] | None:
    if not isinstance(payload, dict):
        return None
    candidates = [payload, payload.get("data")]
    for candidate in candidates:
        messages = candidate.get("messages") if isinstance(candidate, dict) else None
        if not isinstance(messages, list):
            continue
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue
            metadata = message.get("additional_kwargs")
            report = metadata.get("memguard_output_evidence") if isinstance(metadata, dict) else None
            content = message.get("content")
            if isinstance(content, str) and isinstance(report, dict):
                return content, report
    return None


def _persist_governed_output(gateway: Any, *, tenant_id: str, agent_id: str, session_id: str, user_input: str, answer: str, report: dict[str, Any]) -> None:
    events, trace = governed_output_records(tenant_id=tenant_id, agent_id=agent_id, session_id=session_id, user_input=user_input, answer=answer, report=report)
    if not events:
        return
    with gateway._lock:
        gateway.events.extend(events)
    for event in events:
        gateway._persist_event(event)
    gateway.create_decision_trace(trace)


def inject_trusted_agent_context(payload: dict[str, Any], principal: TenantPrincipal) -> dict[str, Any]:
    """Return a copy with trusted LangGraph context replacing browser identity."""
    secured = deepcopy(payload)
    config = secured.get("config") if isinstance(secured.get("config"), dict) else {}
    # LangGraph 0.6+ rejects requests that include both configurable and
    # context. Context is the supported, server-authoritative identity path.
    config = {key: value for key, value in config.items() if key != "configurable"}
    if config:
        secured["config"] = config
    else:
        secured.pop("config", None)
    secured["context"] = {"tenant_id": principal.tenant_id, "actor_id": principal.subject}
    return secured


def _tenant_thread_prefix(principal: TenantPrincipal) -> str:
    """Return the tenant-bound hexadecimal prefix embedded in a UUID thread ID."""
    return sha256(principal.tenant_id.encode()).hexdigest()[:16]


def create_tenant_thread_id(principal: TenantPrincipal) -> str:
    # LangGraph validates thread IDs as UUIDs. Keep the first 64 bits bound to
    # the tenant, while retaining 64 random bits so every conversation is unique.
    raw_uuid = _tenant_thread_prefix(principal) + uuid4().hex[16:]
    return str(UUID(raw_uuid))


def is_allowed_thread_path(path: str, principal: TenantPrincipal) -> bool:
    """Only permit exact, tenant-owned thread routes used by the Agent Chat UI."""
    segments = [segment for segment in path.split("/") if segment]
    if not segments or segments[0] != "threads":
        return False
    if len(segments) == 1:
        return True
    thread_id = segments[1]
    prefix = _tenant_thread_prefix(principal)
    if not fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", thread_id):
        return False
    if not thread_id.replace("-", "").startswith(prefix):
        return False
    return tuple(segments[2:]) in {
        (),
        ("state",),
        ("history",),
        ("runs", "stream"),
    }


def _create_thread_payload(payload: dict[str, Any], principal: TenantPrincipal) -> dict[str, Any]:
    secured = deepcopy(payload)
    metadata = secured.get("metadata") if isinstance(secured.get("metadata"), dict) else {}
    secured["thread_id"] = create_tenant_thread_id(principal)
    secured["metadata"] = {**metadata, "tenant_id": principal.tenant_id, "actor_id": principal.subject}
    return secured


def _upstream_url(path: str, query: str) -> str:
    base_url = os.getenv("LANGGRAPH_AGENT_URL", "http://agent-server:2024").rstrip("/")
    suffix = f"/{path}" if path else ""
    return f"{base_url}{suffix}{'?' + query if query else ''}"


def _proxy_request_headers(request: Request) -> dict[str, str]:
    return {
        name: value
        for name, value in request.headers.items()
        if name.lower() not in _HOP_BY_HOP_HEADERS | {"host", "content-length", "authorization"}
    }


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_agent_server(path: str, request: Request) -> StreamingResponse:
    """Forward Agent Server protocol requests while preserving SSE streams."""
    principal: TenantPrincipal = request.state.principal
    if not is_allowed_thread_path(path, principal) or (path == "threads" and request.method != "POST"):
        raise HTTPException(status_code=404, detail="Agent resource not found")
    body = await request.body()
    content = body
    secured_payload: dict[str, Any] | None = None
    if body and "application/json" in request.headers.get("content-type", ""):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            secured_payload = _create_thread_payload(payload, principal) if path == "threads" else inject_trusted_agent_context(payload, principal)
            content = json.dumps(secured_payload).encode()

    agent_id = str((secured_payload or {}).get("assistant_id") or "customer_support_agent")
    input_messages = ((secured_payload or {}).get("input") or {}).get("messages", [])
    user_input = next((message.get("content", "") for message in reversed(input_messages) if isinstance(message, dict) and message.get("type") in {"human", "user"}), "")
    session_id = path.split("/")[1] if path.startswith("threads/") else ""

    client = httpx.AsyncClient(timeout=None)
    try:
        upstream = await client.send(
            client.build_request(
                method=request.method,
                url=_upstream_url(path, request.url.query),
                headers=_proxy_request_headers(request),
                content=content,
            ),
            stream=True,
        )
    except httpx.RequestError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Customer-support agent is unavailable") from exc

    async def response_body() -> AsyncIterator[bytes]:
        sse_buffer = b""
        recorded = set()
        try:
            async for chunk in upstream.aiter_raw():
                sse_buffer += chunk
                while b"\n\n" in sse_buffer:
                    raw_event, sse_buffer = sse_buffer.split(b"\n\n", 1)
                    data = b"\n".join(line[5:].lstrip() for line in raw_event.replace(b"\r\n", b"\n").split(b"\n") if line.startswith(b"data:"))
                    try:
                        governed = _governed_output_from_sse(json.loads(data)) if data else None
                    except json.JSONDecodeError:
                        governed = None
                    if governed is not None:
                        answer, report = governed
                        fingerprint = sha256(f"{answer}:{json.dumps(report, sort_keys=True)}".encode()).hexdigest()
                        if fingerprint not in recorded:
                            _persist_governed_output(request.app.state.gateway, tenant_id=principal.tenant_id, agent_id=agent_id, session_id=session_id, user_input=user_input, answer=answer, report=report)
                            recorded.add(fingerprint)
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    response_headers = {
        name: value
        for name, value in upstream.headers.items()
        if name.lower() not in _HOP_BY_HOP_HEADERS
    }
    return StreamingResponse(response_body(), status_code=upstream.status_code, headers=response_headers)
