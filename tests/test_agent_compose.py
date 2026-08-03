import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_compose_keeps_agent_server_private_and_connects_backend():
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text()

    assert "agent-server:" in compose
    assert "LANGGRAPH_AGENT_URL: http://agent-server:2024" in compose
    assert '"2024:2024"' not in compose


def test_agent_server_registers_customer_support_graph():
    graph_config = (PROJECT_ROOT / "agent-server" / "langgraph.json").read_text()

    assert '"customer_support_agent"' in graph_config
    # LangGraph must import this as a package module.  A file path loads
    # graph.py without package context, which breaks its relative imports.
    assert "support_agent.graph:customer_support_agent" in graph_config


def test_agent_graph_leaves_persistence_to_langgraph_runtime():
    graph_source = (PROJECT_ROOT / "agent-server" / "support_agent" / "graph.py").read_text()

    assert "InMemorySaver" not in graph_source
