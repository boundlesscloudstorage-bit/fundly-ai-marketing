"""Offline tests for database URL handling and the connectivity check."""

from __future__ import annotations

import io
import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError

from app.database import create_database_engine, get_database_url
from app.check_database import check_database_connection


class DatabaseConfigurationTests(unittest.TestCase):
    def test_missing_database_url_keeps_local_sqlite_default(self) -> None:
        with patch.dict(os.environ, {"DATABASE_URL": ""}):
            self.assertEqual(get_database_url(), "sqlite:///./fundly.db")

    def test_postgresql_urls_select_psycopg_driver(self) -> None:
        for raw_url in (
            "postgres://DB_USER:DB_PASSWORD@DB_HOST:5432/postgres?sslmode=require",
            "postgresql://DB_USER:DB_PASSWORD@DB_HOST:5432/postgres?sslmode=require",
        ):
            with self.subTest(url_scheme=raw_url.split(":", 1)[0]):
                with patch.dict(os.environ, {"DATABASE_URL": raw_url}):
                    normalized = get_database_url()
                self.assertTrue(normalized.startswith("postgresql+psycopg://"))
                engine = create_database_engine(normalized)
                try:
                    self.assertEqual(engine.url.drivername, "postgresql+psycopg")
                finally:
                    engine.dispose()

    def test_connection_check_succeeds_with_isolated_sqlite(self) -> None:
        engine = create_engine("sqlite://")
        output = io.StringIO()
        try:
            self.assertTrue(check_database_connection(engine, output))
        finally:
            engine.dispose()
        self.assertEqual(output.getvalue(), "Database connection successful (SELECT 1).\n")

    def test_connection_error_is_sanitized(self) -> None:
        engine = create_engine("sqlite://")

        @event.listens_for(engine, "do_connect")
        def simulate_connection_error(*_args, **_kwargs):
            raise OperationalError(
                "connect",
                {},
                RuntimeError("postgresql+psycopg://DB_USER:URL_SECRET_SENTINEL@DB_HOST/db"),
            )

        output = io.StringIO()
        try:
            self.assertFalse(check_database_connection(engine, output))
        finally:
            engine.dispose()

        message = output.getvalue()
        self.assertIn("Database connection failed (OperationalError)", message)
        self.assertNotIn("URL_SECRET_SENTINEL", message)
        self.assertNotIn("DB_USER", message)
        self.assertNotIn("DB_HOST", message)
        self.assertNotIn("postgresql+psycopg://", message)


if __name__ == "__main__":
    unittest.main()
