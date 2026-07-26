import pathlib
import sys
import unittest
import json
from dataclasses import dataclass
from unittest.mock import patch


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "sdk"))

from memguard.transport.http import HttpTransport
from memguard.core.event import MemoryEvent, MemoryOp, MemoryType


class HttpTransportQueueTests(unittest.TestCase):
    def test_configures_bounded_delivery_queue(self):
        transport = HttpTransport("http://localhost:8000", queue_maxsize=7)

        self.assertEqual(transport.queue_capacity, 7)

    def test_flush_reports_when_no_records_are_pending(self):
        transport = HttpTransport("http://localhost:8000")

        self.assertTrue(transport.flush(timeout=0.01))

    def test_retries_failed_delivery_before_returning(self):
        @dataclass
        class Event:
            operation: str = "read"

        transport = HttpTransport("http://localhost:8000", max_retries=2, retry_backoff=0)
        with patch("memguard.transport.http.http.client.HTTPConnection") as client:
            connection = client.return_value
            connection.request.side_effect = [OSError("offline"), None]
            connection.getresponse.return_value.status = 200
            transport._emit_sync(Event())
            self.assertTrue(transport.flush(timeout=1))

        self.assertEqual(client.call_count, 2)

    def test_batches_memory_events_into_one_request(self):
        @dataclass
        class Event:
            operation: str = "read"

        transport = HttpTransport("http://localhost:8000")
        with patch("memguard.transport.http.http.client.HTTPConnection") as client:
            connection = client.return_value
            connection.getresponse.return_value.status = 200
            transport._emit_sync(Event(operation="read"))
            transport._emit_sync(Event(operation="create"))
            self.assertTrue(transport.flush(timeout=1))

        self.assertEqual(client.call_count, 1)
        payload = json.loads(connection.request.call_args.kwargs["body"].decode("utf-8"))
        self.assertEqual(len(payload["events"]), 2)

    def test_serializes_real_memory_event_enums_for_the_api(self):
        event = MemoryEvent(
            agent_id="generic-agent",
            operation=MemoryOp.READ,
            memory_type=MemoryType.SEMANTIC,
            memory_key="profile:language",
        )
        transport = HttpTransport("http://localhost:8000")

        with patch("memguard.transport.http.http.client.HTTPConnection") as client:
            connection = client.return_value
            connection.getresponse.return_value.status = 200
            transport._emit_sync(event)
            self.assertTrue(transport.flush(timeout=1))

        payload = json.loads(connection.request.call_args.kwargs["body"].decode("utf-8"))
        self.assertEqual(payload["events"][0]["operation"], "read")
        self.assertEqual(payload["events"][0]["memory_type"], "semantic")

    def test_uses_http_client_for_local_sdk_delivery(self):
        transport_source = (
            pathlib.Path(__file__).parent.parent / "sdk" / "memguard" / "transport" / "http.py"
        ).read_text()

        self.assertIn("http.client.HTTPConnection", transport_source)


if __name__ == "__main__":
    unittest.main()
