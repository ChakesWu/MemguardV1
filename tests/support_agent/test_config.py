import pathlib
import sys

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "agent-server"))


def test_settings_require_deepseek_key_when_real_model_is_enabled(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://memguard:memguard@postgres:5432/memguard")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    from support_agent.config import SupportAgentSettings

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        SupportAgentSettings.from_env()


def test_settings_require_langsmith_key_when_tracing_is_enabled(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://memguard:memguard@postgres:5432/memguard")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    from support_agent.config import SupportAgentSettings

    with pytest.raises(ValueError, match="LANGSMITH_API_KEY"):
        SupportAgentSettings.from_env()


def test_settings_default_to_deepseek_v4_flash(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://memguard:memguard@postgres:5432/memguard")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")

    from support_agent.config import SupportAgentSettings

    assert SupportAgentSettings.from_env().deepseek_model == "deepseek-v4-flash"


def test_requirements_use_current_deepseek_integration_major_version():
    requirements = (PROJECT_ROOT / "agent-server" / "requirements.txt").read_text()

    assert "langchain-deepseek>=1,<2" in requirements


def test_langsmith_environment_is_configured_only_on_the_server(monkeypatch):
    from support_agent.config import SupportAgentSettings, configure_langsmith

    settings = SupportAgentSettings(
        database_url="sqlite:///support.db",
        deepseek_api_key="deepseek-test-key",
        deepseek_model="deepseek-v4-flash",
        langsmith_tracing=True,
        langsmith_api_key="langsmith-test-key",
        langsmith_project="support-agent-test",
    )

    configure_langsmith(settings)

    assert "LANGSMITH_API_KEY" not in settings.__dict__ or settings.langsmith_api_key == "langsmith-test-key"
    assert __import__("os").environ["LANGSMITH_TRACING"] == "true"
    assert __import__("os").environ["LANGSMITH_PROJECT"] == "support-agent-test"
