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
