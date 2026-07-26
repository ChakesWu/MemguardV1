"""Database selection for local development and pilot deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    driver: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            if database_url.startswith(("postgres://", "postgresql://")):
                return cls(url=database_url, driver="postgres")
            if database_url.startswith("sqlite:///"):
                return cls(url=database_url, driver="sqlite")
            raise ValueError("DATABASE_URL must use postgresql:// or sqlite:///.")

        default_path = Path(__file__).parent.parent / "memguard.db"
        sqlite_path = Path(os.getenv("MEMGUARD_DB_PATH", default_path)).resolve()
        return cls(url=f"sqlite:///{sqlite_path}", driver="sqlite")
