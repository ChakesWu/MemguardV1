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
    assert "./support_agent/graph.py:customer_support_agent" in graph_config
