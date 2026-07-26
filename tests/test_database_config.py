import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))


class DatabaseConfigTests(unittest.TestCase):
    def test_defaults_to_sqlite_for_local_development(self):
        with patch.dict(os.environ, {}, clear=True):
            from app.database import DatabaseConfig

            config = DatabaseConfig.from_env()

        self.assertEqual(config.driver, "sqlite")
        self.assertTrue(config.url.startswith("sqlite:///"))

    def test_uses_postgres_database_url_when_configured(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://memguard:secret@db:5432/memguard"}, clear=True):
            from app.database import DatabaseConfig

            config = DatabaseConfig.from_env()

        self.assertEqual(config.driver, "postgres")
        self.assertEqual(config.url, "postgresql://memguard:secret@db:5432/memguard")

    def test_postgres_config_connects_with_dictionary_rows(self):
        from app.database import DatabaseConfig

        config = DatabaseConfig(
            url="postgresql://memguard:secret@db:5432/memguard",
            driver="postgres",
        )

        self.assertTrue(hasattr(config, "connect"))
        with patch("psycopg.connect") as connect:
            connection = config.connect()

        self.assertIs(connection.raw, connect.return_value)
        connect.assert_called_once_with(config.url, row_factory=__import__("psycopg").rows.dict_row)

    def test_postgres_connection_translates_sqlite_placeholders(self):
        from app.database import DatabaseConfig

        config = DatabaseConfig(
            url="postgresql://memguard:secret@db:5432/memguard",
            driver="postgres",
        )
        with patch("psycopg.connect") as connect:
            connection = config.connect()
            connection.execute("SELECT ?", ("evidence",))

        connect.return_value.execute.assert_called_once_with("SELECT %s", ("evidence",))

    def test_gateway_uses_database_url_selected_at_initialization(self):
        from app.services import MemoryGateway

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://memguard:secret@db:5432/memguard"}, clear=True):
            with patch.object(MemoryGateway, "_init_db"):
                gateway = MemoryGateway()

        self.assertTrue(hasattr(gateway, "database"))
        self.assertEqual(gateway.database.driver, "postgres")

    def test_gateway_initializes_schema_through_configured_database(self):
        from app.services import MemoryGateway

        database = MagicMock()
        database.driver = "sqlite"
        connection = MagicMock()
        connection.__enter__.return_value = connection
        database.connect.return_value = connection
        with patch("app.services.DatabaseConfig.from_env", return_value=database):
            with patch.object(MemoryGateway, "_load_from_db"):
                MemoryGateway()

        database.connect.assert_called_once_with()

    def test_postgres_event_persistence_uses_conflict_safe_upsert(self):
        from app.services import MemoryEvent, MemoryGateway

        gateway = MemoryGateway.__new__(MemoryGateway)
        gateway.database = MagicMock(driver="postgres")
        connection = MagicMock()
        connection.__enter__.return_value = connection
        gateway.database.connect.return_value = connection
        event = MemoryEvent(
            event_id="event-1",
            tenant_id="tenant-1",
            agent_id="agent-1",
            memory_id="memory-1",
            trace_id="trace-1",
            event_type="read",
            source_type="semantic",
            content="Python",
            content_hash="hash-1",
            policy_decision="allow",
            trust_score=80.0,
            created_at="2026-07-26T00:00:00+00:00",
        )

        gateway._persist_event(event)

        statement = connection.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (event_id) DO UPDATE", statement)

    def test_postgres_trace_persistence_uses_conflict_safe_upsert(self):
        from app.services import DecisionTrace, MemoryGateway

        gateway = MemoryGateway.__new__(MemoryGateway)
        gateway.database = MagicMock(driver="postgres")
        connection = MagicMock()
        connection.__enter__.return_value = connection
        gateway.database.connect.return_value = connection
        trace = DecisionTrace(
            trace_id="trace-1",
            tenant_id="tenant-1",
            agent_id="agent-1",
            session_id="session-1",
            timestamp="2026-07-26T00:00:00+00:00",
            input_memory_ids=["memory-in"],
            input_memory_events=["event-in"],
            user_input="Why?",
            llm_prompt_hash="prompt-hash",
            llm_output="Because Python.",
            llm_output_hash="output-hash",
            llm_model="demo",
            output_memory_ids=["memory-out"],
            output_memory_events=["event-out"],
            memory_influence_scores={"event-in": 1.0},
            total_influence_score=1.0,
        )

        gateway._persist_trace(trace)

        statement = connection.execute.call_args.args[0]
        self.assertIn("ON CONFLICT (trace_id) DO UPDATE", statement)

    def test_database_statistics_use_gateway_connection_layer(self):
        main_source = (pathlib.Path(__file__).parent.parent / "backend" / "app" / "main.py").read_text()

        self.assertIn("with gateway.database.connect() as conn", main_source)

    def test_postgres_session_query_uses_string_aggregation(self):
        from app.services import MemoryGateway

        gateway = MemoryGateway.__new__(MemoryGateway)
        gateway.database = MagicMock(driver="postgres")
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.execute.return_value.fetchall.return_value = []
        gateway.database.connect.return_value = connection

        gateway.get_sessions_list()

        statement = connection.execute.call_args.args[0]
        self.assertIn("STRING_AGG(DISTINCT agent_id, ',')", statement)


if __name__ == "__main__":
    unittest.main()
