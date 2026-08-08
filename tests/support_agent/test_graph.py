import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))


def test_graph_builds_real_deepseek_agent_with_support_tools(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'server.db'}")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")

    from support_agent.config import SupportAgentSettings
    from support_agent.graph import build_customer_support_agent
    from support_agent.repository import SupportRepository
    from support_agent.seed import seed_baseline_data

    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    repository.migrate()
    seed_baseline_data(repository)
    settings = SupportAgentSettings(
        database_url=repository.database_url,
        deepseek_api_key="test-key",
        deepseek_model="deepseek-v4-flash",
        langsmith_tracing=False,
        langsmith_api_key=None,
        langsmith_project="support-agent-test",
    )

    graph = build_customer_support_agent(settings=settings, repository=repository)

    assert "tools" in graph.nodes
    assert "model" in graph.nodes


def test_graph_keeps_chat_model_for_tool_binding_when_retries_are_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'server.db'}")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")

    from support_agent.config import SupportAgentSettings
    import support_agent.graph as graph_module
    from support_agent.repository import SupportRepository

    captured: dict[str, object] = {}

    class FakeChatDeepSeek:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

        def bind_tools(self, *args: object, **kwargs: object) -> "FakeChatDeepSeek":
            return self

    def fake_create_agent(**kwargs: object) -> object:
        return kwargs["model"]

    monkeypatch.setattr(graph_module, "ChatDeepSeek", FakeChatDeepSeek)
    monkeypatch.setattr(graph_module, "create_agent", fake_create_agent)
    repository = SupportRepository(f"sqlite:///{tmp_path / 'support.db'}")
    settings = SupportAgentSettings(
        database_url=repository.database_url,
        deepseek_api_key="test-key",
        deepseek_model="deepseek-v4-flash",
        langsmith_tracing=False,
        langsmith_api_key=None,
        langsmith_project="support-agent-test",
    )

    model = graph_module.build_customer_support_agent(settings=settings, repository=repository)

    assert isinstance(model, FakeChatDeepSeek)
    assert captured["max_retries"] == 3
