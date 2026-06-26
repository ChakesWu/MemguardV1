"""
Base transport class. All transports inherit from this.

The Transport is the bridge between the SDK (client-side) and the
MemGuard control plane (server-side).
"""

from ..core.event import MemoryEvent  # noqa: F401
from ..core.interceptor import Transport  # noqa: F401
