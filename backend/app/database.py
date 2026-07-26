"""Database selection for local development and pilot deployments."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    def connect(self) -> Any:
        """Open a connection with dictionary-style rows for the selected driver."""
        if self.driver == "sqlite":
            connection = sqlite3.connect(self.url.removeprefix("sqlite:///"))
            connection.row_factory = sqlite3.Row
            return connection

        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.url, row_factory=dict_row)
