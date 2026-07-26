"""
Global Configuration Settings

This module loads configuration from environment variables using Pydantic Settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application Settings

    [Business Purpose] Centralized configuration management for the entire FinCompli system
    """

    # LLM Configuration
    llm_base_url: str = Field(default="http://localhost:8080", description="Local Qwen LLM endpoint")
    llm_model: str = Field(default="Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf")
    llm_api_key: str = Field(default="not-needed-for-local")

    # Database Paths
    chroma_db_path: str = Field(default="./data/chroma")
    sqlite_db_path: str = Field(default="./data/sqlite/fincompli.db")

    # System Configuration
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    max_risk_score: float = Field(default=0.85, description="Above this triggers manual review")
    auto_approve_threshold: float = Field(default=0.30, description="Below this auto-approves")

    # Mock Settings
    enable_mock_data: bool = Field(default=True)
    transaction_stream_delay: int = Field(default=0, description="Delay in seconds, 0 means immediate")

    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_project_root() -> Path:
    """
    Get the project root directory
    """
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Get the data directory path
    """
    data_dir = get_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_audit_log_dir() -> Path:
    """
    Get the audit log directory path
    """
    audit_dir = get_project_root() / "audit_logs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir
