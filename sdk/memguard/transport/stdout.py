"""
Stdout Transport — prints events to stdout.

Useful for debugging and development.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict

from ..core.interceptor import Transport

logger = logging.getLogger("memguard.transport.stdout")


class StdoutTransport(Transport):
    """
    Prints MemoryEvents to stdout as JSON.

    Usage:
        transport = StdoutTransport()
        interceptor = MemGuardInterceptor(
            agent_id="my-agent",
            transport=transport
        )
    """

    async def emit(self, event) -> None:
        """Print event to stdout."""
        try:
            payload = asdict(event)
            print(f"[MemGuard] {json.dumps(payload)}")
        except Exception:
            logger.debug("MemGuard StdoutTransport: print failed", exc_info=True)
