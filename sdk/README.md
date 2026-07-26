# MemGuard SDK

Memory observability and security for AI agents.

## Installation

```bash
pip install memguard
```

## Quick Start

```python
from memguard import MemGuardInterceptor
from memguard.transport.stdout import StdoutTransport

# Create interceptor
interceptor = MemGuardInterceptor(
    agent_id="my-agent",
    transport=StdoutTransport()
)

# Record memory operations
interceptor.record(
    operation=MemoryOp.CREATE,
    memory_key="user_preference",
    after_value={"language": "Python"}
)
```

## Features

- 🔍 **Memory operation tracking** - See every read, write, update, delete
- 🧠 **Decision tracing** - Link memory reads to agent decisions
- ⚡ **Zero overhead** - Fire-and-forget async instrumentation
- 🔌 **Framework agnostic** - Works with any agent framework
- 📊 **Multiple transports** - Stdout, HTTP, File

## Documentation

See the main [MemGuard repository](https://github.com/yourusername/memguard) for full documentation.
