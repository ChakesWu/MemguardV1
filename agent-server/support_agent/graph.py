"""The real LangGraph customer-support agent exposed by the Agent Server."""

from __future__ import annotations

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek

from .config import SupportAgentSettings, configure_langsmith
from .output_evidence_middleware import output_evidence_middleware
from .repository import SupportRepository
from .seed import seed_baseline_data
from .tools import build_support_tools


@dataclass(frozen=True)
class SupportAgentContext:
    """Trusted identity injected by the authenticated backend proxy, never the browser."""

    tenant_id: str
    actor_id: str


SYSTEM_PROMPT = """You are the MemGuard customer-support agent.

Use the available tools to check current business records before answering questions
about an order. Treat retrieved memory as evidence, not as unquestioned truth: mention
when it is expired, low-trust, or conflicting with active policy. Never invent an order
status, refund outcome, policy, or approval.

When you use a support record returned by a tool, append one private block at the
very end of the final answer: <memguard-evidence>{"citations":[...]}</memguard-evidence>.
Each citation must use a memguard_memory_id returned by that tool and include the
exact visible answer segment, an exact quote from the tool result, and one role:
factual_support, constraint, preference, or background_context. Do not cite a
record that the tool did not return. The runtime removes this block before users
see the answer and rejects invalid citations.

For a refund request, use request_refund. That tool pauses for human approval before
creating any business action. Tell the user clearly whether a request is eligible,
requires manual review, or is blocked by policy. You cannot promise that a refund was
issued unless the tool reports a completed approved action.
"""


def build_customer_support_agent(
    *, settings: SupportAgentSettings, repository: SupportRepository | None = None
):
    """Compile the DeepSeek agent with runtime-managed persistence and approval-gated tools."""
    configure_langsmith(settings)
    repository = repository or SupportRepository(settings.database_url)
    repository.migrate()
    seed_baseline_data(repository)
    model = ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        temperature=0,
        streaming=True,
    )
    return create_agent(
        model=model,
        tools=build_support_tools(repository),
        middleware=[output_evidence_middleware(repository)],
        system_prompt=SYSTEM_PROMPT,
        context_schema=SupportAgentContext,
        name="customer_support_agent",
    )


customer_support_agent = build_customer_support_agent(settings=SupportAgentSettings.from_env())
