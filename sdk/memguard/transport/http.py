"""
HTTP Transport — sends events to the MemGuard control plane via REST API.

Fire-and-forget: never blocks the calling agent.
Uses the standard library HTTP client — zero additional dependencies.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
import http.client
from dataclasses import dataclass
from urllib.parse import urlparse

from ..core.interceptor import Transport

logger = logging.getLogger("memguard.transport.http")


@dataclass(frozen=True)
class TransportStats:
    queued: int
    delivered: int
    dropped: int
    failed: int
    pending: int

    @property
    def evidence_complete(self) -> bool:
        return self.pending == 0 and self.dropped == 0 and self.failed == 0


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
        max_retries: int = 3,
        retry_backoff: float = 0.1,
        queue_maxsize: int = 1_000,
        batch_size: int = 50,
        batch_wait: float = 0.01,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max(1, max_retries)
        self.retry_backoff = max(0.0, retry_backoff)
        self.queue_capacity = max(1, queue_maxsize)
        self.batch_size = max(1, batch_size)
        self.batch_wait = max(0.0, batch_wait)
        self._queue: queue.Queue = queue.Queue(maxsize=self.queue_capacity)
        self._pending = 0
        self._queued = 0
        self._delivered = 0
        self._dropped = 0
        self._failed = 0
        self._pending_lock = threading.Condition()
        self._worker = threading.Thread(target=self._drain, daemon=True)
        self._worker.start()

    def flush(self, timeout: float | None = None) -> bool:
        """Wait until records already handed to the transport finish sending."""
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._pending_lock:
            while self._pending:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._pending_lock.wait(remaining)
        return True

    def stats(self) -> TransportStats:
        with self._pending_lock:
            return TransportStats(
                queued=self._queued,
                delivered=self._delivered,
                dropped=self._dropped,
                failed=self._failed,
                pending=self._pending,
            )

    async def emit(self, event) -> None:
        """Send event synchronously (no-thread for reliability during demo)."""
        self._emit_sync(event)

    def _emit_sync(self, event) -> None:
        """Queue a record without blocking the instrumented agent."""
        with self._pending_lock:
            self._pending += 1
            self._queued += 1
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            with self._pending_lock:
                self._pending -= 1
                self._dropped += 1
                self._pending_lock.notify_all()
            logger.warning("MemGuard HTTP transport queue is full; dropping new record")

    def _drain(self) -> None:
        while True:
            event = self._queue.get()
            batch = [event]
            try:
                if hasattr(event, "operation"):
                    deadline = time.monotonic() + self.batch_wait
                    while len(batch) < self.batch_size:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            break
                        try:
                            next_event = self._queue.get(timeout=remaining)
                        except queue.Empty:
                            break
                        if not hasattr(next_event, "operation"):
                            delivered = self._deliver_batch(batch)
                            self._record_delivery(batch, delivered)
                            self._complete(batch)
                            batch = [next_event]
                            break
                        batch.append(next_event)

                    if hasattr(batch[0], "operation"):
                        delivered = self._deliver_batch(batch)
                    else:
                        delivered = self._deliver(batch[0])
                else:
                    delivered = self._deliver(event)
                self._record_delivery(batch, delivered)
            finally:
                self._complete(batch)

    def _record_delivery(self, events, delivered: bool) -> None:
        with self._pending_lock:
            if delivered:
                self._delivered += len(events)
            else:
                self._failed += len(events)

    def _complete(self, events) -> None:
        for _ in events:
            self._queue.task_done()
        with self._pending_lock:
            self._pending -= len(events)
            self._pending_lock.notify_all()

    def _deliver(self, event) -> bool:
        """Deliver one queued record with bounded retries."""
        if hasattr(event, "operation"):
            return self._deliver_batch([event])

        try:
            from dataclasses import asdict

            payload = asdict(event)
            self._post("/v1/trace", payload)
            return True
        except Exception:
            # Observability must never break production, but log at warning
            logger.warning(
                "MemGuard HTTP transport: trace emit failed (backend may be down)",
                exc_info=False,
            )
            return False

    def _deliver_batch(self, events) -> bool:
        try:
            from dataclasses import asdict

            self._post("/v1/events", {"events": [asdict(event) for event in events]})
            return True
        except Exception:
            logger.warning(
                "MemGuard HTTP transport: event batch emit failed (backend may be down)",
                exc_info=False,
            )
            return False

    def _post(self, path: str, payload) -> None:
        endpoint = urlparse(self.base_url)
        if endpoint.scheme not in {"http", "https"} or not endpoint.hostname:
            raise ValueError("base_url must be an absolute HTTP(S) URL")

        request_path = f"{endpoint.path.rstrip('/')}{path}"
        connection_type = (
            http.client.HTTPSConnection
            if endpoint.scheme == "https"
            else http.client.HTTPConnection
        )
        # Framework metadata may include checkpoint/message objects that are
        # meaningful as evidence but are not JSON-native. Preserve delivery
        # by recording their string representation instead of dropping the
        # whole batch.
        body = json.dumps(payload, default=str).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}),
        }
        for attempt in range(self.max_retries):
            try:
                connection = connection_type(
                    endpoint.hostname, endpoint.port, timeout=self.timeout
                )
                connection.request("POST", request_path, body=body, headers=headers)
                response = connection.getresponse()
                response.read()
                connection.close()
                if not 200 <= response.status < 300:
                    raise OSError(f"MemGuard server returned HTTP {response.status}")
                return
            except (OSError, http.client.HTTPException):
                if attempt + 1 == self.max_retries:
                    raise
                time.sleep(self.retry_backoff * (2**attempt))
