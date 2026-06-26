"""
File Transport — appends events to a JSONL file.

Useful for development, offline mode, or when you don't want to run the server.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict

from ..core.interceptor import Transport

logger = logging.getLogger("memguard.transport.file")


class FileTransport(Transport):
    """
    Writes MemoryEvents to a JSONL file.

    Usage:
        transport = FileTransport("memguard_events.jsonl")
        interceptor = MemGuardInterceptor(
            agent_id="my-agent",
            transport=transport
        )
    """

    def __init__(self, filepath: str = "memguard_events.jsonl"):
        self.filepath = filepath

    async def emit(self, event) -> None:
        """Append event as one JSON line to the file."""
        try:
            payload = asdict(event)
            with open(self.filepath, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            logger.debug("MemGuard FileTransport: write failed", exc_info=True)
