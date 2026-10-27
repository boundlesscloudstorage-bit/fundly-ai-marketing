"""Opt-in PostgreSQL tests using a uniquely named, disposable schema."""

from __future__ import annotations

import os
import unittest
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.db_models import Base
from app.models import SaveDraftRequest
from app.services.draft_repository import DraftRepository, DraftVersionConflict

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
POSTGRES_TESTS_ENABLED = os.getenv("RUN_POSTGRES_INTEGRATION") == "1" and bool(TEST_DATABASE_URL)


@unittest.skipUnless(
    POSTGRES_TESTS_ENABLED,
    "Set RUN_POSTGRES_INTEGRATION=1 and TEST_DATABASE_URL to opt into isolated PostgreSQL tests",
)
class PostgreSQLDraftRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parsed_url = make_url(TEST_DATABASE_URL or "")
        database_name = (parsed_url.database or "").lower()
        is_named_test_database = (
            database_name.startswith("test_")
            or database_name.endswith("_test")
        )

        is_dedicated_neon_test_database = (
            database_name == "neondb"
            and (parsed_url.host or "").endswith(".neon.tech")
        )

        if not (is_named_test_database or is_dedicated_neon_test_database):
            raise RuntimeError(
                "TEST_DATABASE_URL must use a test-named database "
                "or the dedicated Neon test database."
            )
        if parsed_url.get_backend_name() != "postgresql":
            raise RuntimeError("TEST_DATABASE_URL must point to PostgreSQL")

        cls.schema = f"fundly_phase4_test_{uuid4().hex}"
        cls.engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
        with cls.engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{cls.schema}"'))

        cls.test_engine = cls.engine.execution_options(schema_translate_map={None: cls.schema})
        Base.metadata.create_all(cls.test_engine)
        cls.session_factory = sessionmaker(bind=cls.test_engine, expire_on_commit=False)
        cls.repository = DraftRepository()

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "engine"):
            with cls.engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA IF EXISTS "{cls.schema}" CASCADE'))
            cls.engine.dispose()

    def test_postgres_create_list_update(self) -> None:
        request = SaveDraftRequest(
            topic="saving with a goal",
            caption="A measured example caption.",
            hashtags=["#Planning"],
            platform="linkedin",
            objective="education",
            tone="friendly",
        )
        with self.session_factory() as session:
            created = self.repository.create(session, request)

        with self.session_factory() as session:
            listed = self.repository.list(session)
            persisted = next(draft for draft in listed if draft.id == created.id)
            self.assertEqual(persisted.id, created.id)

        with self.session_factory() as session:
            updated = self.repository.update(
                session,
                created.id,
                {"caption": "Updated example caption."},
            )
            self.assertEqual(updated.caption, "Updated example caption.")

    def test_postgres_version_conflict_rolls_back_update(self) -> None:
        request = SaveDraftRequest(
            topic="saving with a goal",
            caption="A measured example caption.",
            hashtags=["#Planning"],
            platform="linkedin",
            objective="education",
            tone="friendly",
        )
        with self.session_factory() as session:
            created = self.repository.create(session, request)

        with self.session_factory() as session:
            updated = self.repository.update(
                session,
                created.id,
                {"caption": "Updated example caption."},
            )
            self.assertEqual(updated.caption, "Updated example caption.")

        with self.session_factory() as session:
            with self.assertRaises(DraftVersionConflict):
                self.repository.update(
                    session,
                    created.id,
                    {"caption": "Stale update."},
                    expected_version=1,
                )

        with self.session_factory() as session:
            persisted = next(
                draft for draft in self.repository.list(session) if draft.id == created.id
            )
            self.assertEqual(persisted.caption, "Updated example caption.")


if __name__ == "__main__":
    unittest.main()
