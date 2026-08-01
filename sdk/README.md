# MemGuard SDK

MemGuard records which memories and retrieved context were available when an AI agent produced an output. It provides evidence-backed lineage for debugging; it does not claim to expose the model's internal reasoning.

## Installation

```bash
pip install memguard
```

## Record a useful explanation

```python
from memguard import MemGuard

guard = MemGuard(
    api_url="http://localhost:8000",
    api_key="<token>",
    agent_id="travel-agent",
    namespace="acme-dev",
    capture_content=True,
)
guard.set_session("user-42-run-7")

memory_event_id = guard.record_retrieval(
    "profile:current_location",
    {"current_location": "Taipei"},
    source_type="conversation",
    retrieval_rank=1,
    included_in_prompt=True,
    fact_key="current_location",
)

guard.record_output(
    user_input="I am currently in New York.",
    output_text="You are currently in Taipei.",
    input_event_ids=[memory_event_id],
    model="my-agent-model",
    current_facts={"current_location": "New York"},
)
guard.flush()
```

`capture_content=True` is required for value-level conflict visualization. Enable it only when your privacy and data-handling policy permits raw memory content to be recorded. The default is hash-only capture.

## Check and run the deterministic demo

```bash
memguard doctor --api-url http://localhost:8000 --api-token "$MEMGUARD_API_TOKEN" --tenant-id acme-dev
memguard demo --api-url http://localhost:8000 --api-token "$MEMGUARD_API_TOKEN" --tenant-id acme-dev
```
