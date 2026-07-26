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
    Prints MemoryEvents to stdout as compact single-line JSON.

    Usage:
        transport = StdoutTransport()
        interceptor = MemGuardInterceptor(
            agent_id="my-agent",
            transport=transport
        )
    """

    def __init__(self, verbose: bool = False):
        """
        Args:
            verbose: Whether to output detailed JSON (default False, only prints a one-line summary)
        """
        self.verbose = verbose

    async def emit(self, event) -> None:
        """Print event to stdout."""
        try:
            if self.verbose:
                payload = asdict(event)
                print(f"[MemGuard] {json.dumps(payload)}")
            else:
                # Compact format: only prints a one-line summary
                payload = asdict(event)
                op = payload.get("operation", "?")
                key = payload.get("memory_key", "?")
                mtype = payload.get("memory_type", "?")
                print(f"[MemGuard] {op.upper():<8} {key:<30} type={mtype}")
        except Exception:
            logger.debug("MemGuard StdoutTransport: print failed", exc_info=True)
