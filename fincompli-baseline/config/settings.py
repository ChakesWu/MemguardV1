"""
Global Configuration Settings
全局配置設定

This module loads configuration from environment variables using Pydantic Settings.
使用 Pydantic Settings 從環境變量加載配置。
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application Settings
    應用配置

    [Business Purpose] Centralized configuration management for the entire FinCompli system
    [業務目的] 整個 FinCompli 系統的集中配置管理
    """

    # LLM Configuration / LLM 配置
    llm_base_url: str = Field(default="http://localhost:8080", description="Local Qwen LLM endpoint")
    llm_model: str = Field(default="Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-IQ3_M.gguf")
    llm_api_key: str = Field(default="not-needed-for-local")

    # Database Paths / 數據庫路徑
    chroma_db_path: str = Field(default="./data/chroma")
    sqlite_db_path: str = Field(default="./data/sqlite/fincompli.db")

    # System Configuration / 系統配置
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    max_risk_score: float = Field(default=0.85, description="Above this triggers manual review")
    auto_approve_threshold: float = Field(default=0.30, description="Below this auto-approves")

    # Mock Settings / Mock 設置
    enable_mock_data: bool = Field(default=True)
    transaction_stream_delay: int = Field(default=0, description="Delay in seconds, 0 means immediate")

    # API Settings / API 設置
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance / 全局配置實例
settings = Settings()


def get_project_root() -> Path:
    """
    Get the project root directory
    獲取項目根目錄
    """
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """
    Get the data directory path
    獲取數據目錄路徑
    """
    data_dir = get_project_root() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_audit_log_dir() -> Path:
    """
    Get the audit log directory path
    獲取審計日誌目錄路徑
    """
    audit_dir = get_project_root() / "audit_logs"
    audit_dir.mkdir(parents=True, exist_ok=True)
    return audit_dir
