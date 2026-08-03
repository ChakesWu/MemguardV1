import pathlib
import sys
from pathlib import Path

from langgraph.prebuilt import ToolRuntime


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))

from support_agent.repository import SupportRepository
from support_agent.seed import seed_baseline_data
from support_agent.tools import build_support_tools


def _runtime(*, tenant_id: str = "acme-dev", actor_id: str = "demo-user", tool_call_id: str = "call-1") -> ToolRuntime:
    return ToolRuntime(
        state={},
        context={"tenant_id": tenant_id, "actor_id": actor_id},
        config={},
        stream_writer=lambda _value: None,
        tool_call_id=tool_call_id,
        store=None,
    )


def test_refund_request_interrupts_before_any_business_write(tmp_path: Path, monkeypatch) -> None:
    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    tools = {tool.name: tool for tool in build_support_tools(repository)}
    requested_approvals: list[dict] = []

    def reject(approval: dict) -> dict:
        requested_approvals.append(approval)
        return {"decision": "reject"}

    monkeypatch.setattr("support_agent.tools.interrupt", reject)

    result = tools["request_refund"].func("ORD-4821", "Item is defective", True, _runtime())

    assert requested_approvals[0]["kind"] == "approval_required"
    assert requested_approvals[0]["action"] == "request_refund"
    assert result["status"] == "rejected"
    assert repository.actions_for("acme-dev", "ORD-4821") == []


def test_approved_refund_request_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    tools = {tool.name: tool for tool in build_support_tools(repository)}
    monkeypatch.setattr("support_agent.tools.interrupt", lambda _approval: {"decision": "approve"})

    first = tools["request_refund"].func("ORD-4821", "Item is defective", True, _runtime())
    second = tools["request_refund"].func("ORD-4821", "Item is defective", True, _runtime())

    assert first["status"] == "manual_review_requested"
    assert second["action_id"] == first["action_id"]
    assert len(repository.actions_for("acme-dev", "ORD-4821")) == 1
