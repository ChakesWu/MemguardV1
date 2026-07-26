"""
Null Transport — silently discards all events.

Useful when you want to handle output yourself (e.g., in a demo).
"""

from ..core.interceptor import Transport


class NullTransport(Transport):
    """Silently discards all events. No output, no side effects."""

    async def emit(self, event) -> None:
        pass
