"""Authenticated reverse proxy for the private LangGraph Agent Server."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from copy import deepcopy
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .auth import TenantPrincipal


router = APIRouter(prefix="/v1/agent-server", tags=["customer-support-agent"])
_HOP_BY_HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}


def inject_trusted_agent_context(payload: dict[str, Any], principal: TenantPrincipal) -> dict[str, Any]:
    """Return a copy with Keycloak identity replacing all browser-supplied agent identity."""
    secured = deepcopy(payload)
    config = secured.get("config") if isinstance(secured.get("config"), dict) else {}
    configurable = config.get("configurable") if isinstance(config.get("configurable"), dict) else {}
    configurable = {**configurable, "tenant_id": principal.tenant_id, "actor_id": principal.subject}
    secured["config"] = {**config, "configurable": configurable}
    secured["context"] = {"tenant_id": principal.tenant_id, "actor_id": principal.subject}
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
    body = await request.body()
    content = body
    if body and "application/json" in request.headers.get("content-type", ""):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            content = json.dumps(inject_trusted_agent_context(payload, principal)).encode()

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
        try:
            async for chunk in upstream.aiter_raw():
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
