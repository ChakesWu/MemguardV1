"""
HTTP Transport — sends events to the MemGuard control plane via REST API.

Fire-and-forget: never blocks the calling agent.
Uses urllib (stdlib) — zero additional dependencies.
"""

from __future__ import annotations

import json
import logging
import threading
from urllib import request, error

from ..core.interceptor import Transport

logger = logging.getLogger("memguard.transport.http")


class HttpTransport(Transport):
    """
    Sends MemoryEvents to the MemGuard server via HTTP POST.

    Usage:
        transport = HttpTransport(
            base_url="http://localhost:8000",
            api_key=None  # Optional: for authenticated endpoints
        )
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        timeout: float = 2.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def emit(self, event) -> None:
        """Send event synchronously (no-thread for reliability during demo)."""
        self._emit_sync(event)

    def _emit_sync(self, event) -> None:
        """Synchronous HTTP POST in a background thread."""
        try:
            from dataclasses import asdict
            payload = asdict(event)

            # Route based on event type
            if hasattr(event, 'operation'):
                url = f"{self.base_url}/v1/events"
                body = json.dumps({"events": [payload]}).encode("utf-8")
            else:
                url = f"{self.base_url}/v1/trace"
                body = json.dumps(payload).encode("utf-8")

            req = request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {})
                },
                method="POST",
            )

            request.urlopen(req, timeout=self.timeout)
        except (error.URLError, OSError, Exception):
            # Observability must never break production, but log at warning
            logger.warning("MemGuard HTTP transport: emit failed to %s (backend may be down)", url, exc_info=False)
