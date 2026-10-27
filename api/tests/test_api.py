import unittest
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from app.database import create_session_factory
from app.db_models import DraftRecord
from app.main import create_app
from app.models import GeneratedContent
from app.services.content_generator import (
    AIInvalidResponseError,
    AIProviderError,
    AIProviderTimeoutError,
    ContentGenerator,
)
from app.services.draft_repository import DraftRepository, DraftVersionConflict


class MockContentGenerator:
    async def generate(self, request):
        caption = f"A thoughtful Fundly draft about {request.topic}."
        return GeneratedContent(
            topic=request.topic,
            caption=caption,
            hashtags=["#Fundly", "#Planning"],
            platform=request.platform,
            objective=request.objective,
            tone=request.tone,
            character_count=len(caption),
            is_demo_generated=False,
        )


class DemoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        config.attributes["database_url"] = "sqlite://"
        migration_connection = self.engine.connect()
        config.attributes["connection"] = migration_connection
        command.upgrade(config, "head")
        migration_connection.close()

        self.session_factory = create_session_factory(self.engine)
        self.client = TestClient(create_app(self.session_factory, content_generator=MockContentGenerator()))

    def tearDown(self) -> None:
        self.client.close()
        self.engine.dispose()

    def test_health_is_demo_mode(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "mode": "demo"})

    def test_migration_schema_matches_sqlalchemy_model(self) -> None:
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        config.attributes["database_url"] = "sqlite://"
        with self.engine.connect() as connection:
            config.attributes["connection"] = connection
            command.check(config)

    def test_migration_downgrade_is_limited_to_new_drafts_table(self) -> None:
        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        config.attributes["database_url"] = "sqlite://"
        with self.engine.begin() as connection:
            connection.execute(text("CREATE TABLE existing_sentinel (id INTEGER PRIMARY KEY)"))
        with self.engine.connect() as connection:
            config.attributes["connection"] = connection
            command.downgrade(config, "base")
            tables = inspect(connection).get_table_names()
            self.assertIn("existing_sentinel", tables)
            self.assertNotIn("drafts", tables)
            connection.commit()
            command.upgrade(config, "head")
            self.assertIn("drafts", inspect(connection).get_table_names())

    def test_overview_is_validated_and_marked_demo(self) -> None:
        response = self.client.get("/api/dashboard/overview")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["brand_id"], "fundly")
        self.assertTrue(payload["is_demo"])
        self.assertTrue(all(metric["is_demo"] for metric in payload["metrics"]))

    def test_campaigns_and_content_are_demo_records(self) -> None:
        campaigns = self.client.get("/api/campaigns").json()
        content = self.client.get("/api/content").json()
        self.assertEqual(campaigns["total"], len(campaigns["items"]))
        self.assertTrue(all(item["is_demo"] for item in campaigns["items"]))
        self.assertEqual(content["total"], len(content["items"]))
        self.assertTrue(all(item["is_ai_generated_example"] for item in content["items"]))

    def test_unknown_route_returns_not_found(self) -> None:
        self.assertEqual(self.client.get("/api/missing").status_code, 404)

    def test_cors_allows_local_dashboard_origin(self) -> None:
        response = self.client.get(
            "/api/dashboard/overview",
            headers={"Origin": "http://localhost:3000"},
        )
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:3000")

    def test_cors_does_not_allow_unconfigured_origin(self) -> None:
        response = self.client.get(
            "/api/dashboard/overview",
            headers={"Origin": "http://example.com"},
        )
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_generation_returns_valid_ai_content_shape(self) -> None:
        request = {
            "topic": "building a monthly budget",
            "platform": "linkedin",
            "objective": "education",
            "tone": "friendly",
            "keywords": "planning, everyday money",
        }
        first = self.client.post("/api/content/generate", json=request)

        self.assertEqual(first.status_code, 200)
        payload = first.json()
        self.assertEqual(payload["platform"], "linkedin")
        self.assertEqual(payload["tone"], "friendly")
        self.assertFalse(payload["is_demo_generated"])
        self.assertEqual(payload["character_count"], len(payload["caption"]))
        self.assertTrue(all(tag.startswith("#") for tag in payload["hashtags"]))

    def test_generated_content_rejects_inconsistent_character_count(self) -> None:
        with self.assertRaises(ValidationError):
            GeneratedContent(
                topic="budgeting basics",
                caption="A short caption.",
                hashtags=["#Fundly"],
                platform="linkedin",
                objective="education",
                tone="friendly",
                character_count=1,
                is_demo_generated=False,
            )

    def test_generation_uses_all_supported_platforms(self) -> None:
        for platform in ("x", "linkedin", "instagram", "facebook"):
            with self.subTest(platform=platform):
                response = self.client.post(
                    "/api/content/generate",
                    json={
                        "topic": "saving for a goal",
                        "platform": platform,
                        "objective": "engagement",
                        "tone": "inspiring",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["platform"], platform)
                self.assertLessEqual(response.json()["character_count"], 280 if platform == "x" else 2800)

    def test_generation_rejects_missing_and_invalid_fields(self) -> None:
        missing_topic = self.client.post(
            "/api/content/generate",
            json={"platform": "x", "objective": "education", "tone": "friendly"},
        )
        invalid_platform = self.client.post(
            "/api/content/generate",
            json={"topic": "saving for a goal", "platform": "threads", "objective": "education", "tone": "friendly"},
        )
        unsafe_claim = self.client.post(
            "/api/content/generate",
            json={"topic": "guaranteed returns", "platform": "x", "objective": "education", "tone": "professional"},
        )

        self.assertEqual(missing_topic.status_code, 422)
        self.assertEqual(invalid_platform.status_code, 422)
        self.assertEqual(unsafe_claim.status_code, 422)

    def test_generation_without_provider_key_returns_clear_configuration_error(self) -> None:
        client = TestClient(create_app(self.session_factory, content_generator=ContentGenerator(api_key="")))
        try:
            response = client.post(
                "/api/content/generate",
                json={
                    "topic": "monthly budgeting",
                    "platform": "linkedin",
                    "objective": "education",
                    "tone": "friendly",
                },
            )
        finally:
            client.close()

        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.json()["detail"])

    def test_provider_failures_return_sanitized_http_errors(self) -> None:
        cases = (
            (AIProviderTimeoutError(), 504),
            (AIInvalidResponseError(), 502),
            (AIProviderError(), 502),
        )
        for error, expected_status in cases:
            with self.subTest(expected_status=expected_status, error_type=type(error).__name__):
                class FailingGenerator:
                    async def generate(self, _request):
                        raise error

                client = TestClient(
                    create_app(self.session_factory, content_generator=FailingGenerator())
                )
                try:
                    response = client.post(
                        "/api/content/generate",
                        json={
                            "topic": "monthly budgeting",
                            "platform": "linkedin",
                            "objective": "education",
                            "tone": "friendly",
                        },
                    )
                finally:
                    client.close()
                self.assertEqual(response.status_code, expected_status)
                self.assertNotIn("GEMINI_API_KEY", response.text)

    def test_generated_draft_provenance_is_persisted(self) -> None:
        response = self.client.post(
            "/api/drafts",
            json={
                "topic": "saving with a goal",
                "caption": "A thoughtful Fundly draft about saving with a goal.",
                "hashtags": ["#Fundly"],
                "platform": "linkedin",
                "objective": "education",
                "tone": "friendly",
                "is_demo_generated": False,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["is_demo_generated"])

    def test_generation_rejects_unsupported_claims_in_keywords(self) -> None:
        response = self.client.post(
            "/api/content/generate",
            json={
                "topic": "budgeting basics",
                "platform": "instagram",
                "objective": "education",
                "tone": "professional",
                "keywords": "guaranteed returns",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_save_and_list_drafts(self) -> None:
        created = self.client.post(
            "/api/drafts",
            json={
                "topic": "saving for a goal",
                "caption": "An edited caption for a considered next step.",
                "hashtags": ["#Savings", "#Fundly"],
                "platform": "instagram",
                "objective": "brand_awareness",
                "tone": "inspiring",
            },
        )
        self.assertEqual(created.status_code, 201)
        saved = created.json()
        self.assertEqual(saved["status"], "draft")
        self.assertTrue(saved["is_demo_generated"])
        self.assertEqual(saved["character_count"], len(saved["caption"]))
        self.assertTrue(saved["id"])
        self.assertTrue(saved["created_at"])
        self.assertTrue(saved["updated_at"])
        datetime.fromisoformat(saved["created_at"])
        datetime.fromisoformat(saved["updated_at"])

        listed = self.client.get("/api/drafts")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["total"], 1)
        self.assertEqual(listed.json()["items"][0]["id"], saved["id"])

    def test_saved_drafts_survive_app_recreation(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "saving for later",
                "caption": "A persistent example draft.",
                "hashtags": ["#Planning"],
                "platform": "facebook",
                "objective": "education",
                "tone": "professional",
            },
        ).json()

        with TestClient(create_app(self.session_factory)) as restarted_app:
            persisted = restarted_app.get("/api/drafts")

        self.assertEqual(persisted.status_code, 200)
        self.assertEqual(persisted.json()["items"][0]["id"], saved["id"])

    def test_edit_draft_updates_caption_hashtags_and_character_count(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "budgeting basics",
                "caption": "Original caption.",
                "hashtags": ["#Budgeting"],
                "platform": "facebook",
                "objective": "education",
                "tone": "professional",
            },
        ).json()

        original_updated_at = datetime.fromisoformat(saved["updated_at"])

        response = self.client.patch(
            f"/api/drafts/{saved['id']}",
            json={"caption": "Updated caption with a few more words.", "hashtags": ["#MoneyGoals"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["caption"], "Updated caption with a few more words.")
        self.assertEqual(response.json()["hashtags"], ["#MoneyGoals"])
        self.assertEqual(response.json()["character_count"], len(response.json()["caption"]))
        self.assertGreaterEqual(datetime.fromisoformat(response.json()["updated_at"]), original_updated_at)

    def test_approve_draft_without_publishing(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Review options at a pace that feels right.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "engagement",
                "tone": "friendly",
            },
        ).json()

        response = self.client.patch(f"/api/drafts/{saved['id']}", json={"status": "approved"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "approved")

    def test_editing_approved_content_requires_reapproval(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Review options at a pace that feels right.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "engagement",
                "tone": "friendly",
            },
        ).json()
        self.client.patch(f"/api/drafts/{saved['id']}", json={"status": "approved"})

        response = self.client.patch(
            f"/api/drafts/{saved['id']}",
            json={"caption": "Review every option at a pace that feels right."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "draft")
        self.assertEqual(response.json()["caption"], "Review every option at a pace that feels right.")

    def test_noop_content_edit_preserves_approval(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Review options at a pace that feels right.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "engagement",
                "tone": "friendly",
            },
        ).json()
        self.client.patch(f"/api/drafts/{saved['id']}", json={"status": "approved"})

        response = self.client.patch(
            f"/api/drafts/{saved['id']}",
            json={"caption": saved["caption"], "hashtags": saved["hashtags"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "approved")

    def test_editing_draft_keeps_draft_status(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Review options at a pace that feels right.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "engagement",
                "tone": "friendly",
            },
        ).json()

        response = self.client.patch(
            f"/api/drafts/{saved['id']}", json={"hashtags": ["#Planning", "#Fundly"]}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "draft")
        self.assertEqual(response.json()["hashtags"], ["#Planning", "#Fundly"])

    def test_version_conflict_rolls_back_update(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Original content.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "education",
                "tone": "friendly",
            },
        ).json()

        repository = DraftRepository()
        with self.session_factory() as session:
            record = session.get(DraftRecord, saved["id"])
            self.assertIsNotNone(record)
            current_version = record.version

        with self.session_factory() as session:
            repository.update(session, saved["id"], {"caption": "Committed update."})

        with self.session_factory() as session:
            with self.assertRaises(DraftVersionConflict):
                repository.update(
                    session,
                    saved["id"],
                    {"caption": "Stale update must roll back."},
                    expected_version=current_version,
                )

        with self.session_factory() as session:
            stored = session.scalar(select(DraftRecord).where(DraftRecord.id == saved["id"]))
            self.assertEqual(stored.caption, "Committed update.")
            self.assertEqual(stored.version, current_version + 1)

    def test_concurrent_version_conflict_returns_409(self) -> None:
        saved = self.client.post(
            "/api/drafts",
            json={
                "topic": "thoughtful planning",
                "caption": "Original content.",
                "hashtags": ["#Planning"],
                "platform": "linkedin",
                "objective": "education",
                "tone": "friendly",
            },
        ).json()
        # Exercise the same atomic compare-and-swap failure as a concurrently stale request.
        class ConflictingRepository(DraftRepository):
            def update(self, session, draft_id, changes, *, expected_version=None):
                return super().update(session, draft_id, changes, expected_version=0)

        self.client.app.state.draft_repository = ConflictingRepository()
        response = self.client.patch(
            f"/api/drafts/{saved['id']}",
            json={"caption": "Stale update."},
        )

        self.assertEqual(response.status_code, 409)
        current = self.client.get("/api/drafts").json()["items"][0]
        self.assertEqual(current["caption"], "Original content.")

    def test_database_unavailable_returns_generic_503(self) -> None:
        broken_engine = create_engine("sqlite://", poolclass=StaticPool)

        @event.listens_for(broken_engine, "do_connect")
        def simulate_connection_loss(*_args, **_kwargs):
            raise OperationalError("connect", {}, RuntimeError("database offline"))

        broken_client = TestClient(create_app(create_session_factory(broken_engine)))
        try:
            response = broken_client.get("/api/drafts")
        finally:
            broken_client.close()
            broken_engine.dispose()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Draft storage is temporarily unavailable"})

    def test_missing_draft_and_invalid_patch_return_errors(self) -> None:
        missing = self.client.patch("/api/drafts/not-a-real-id", json={"status": "approved"})
        invalid_status = self.client.patch("/api/drafts/not-a-real-id", json={"status": "published"})
        empty_patch = self.client.patch("/api/drafts/not-a-real-id", json={})

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(invalid_status.status_code, 422)
        self.assertEqual(empty_patch.status_code, 422)

    def test_hashtag_schema_validation(self) -> None:
        response = self.client.post(
            "/api/drafts",
            json={
                "topic": "budgeting basics",
                "caption": "A thoughtful sample caption.",
                "hashtags": ["not-a-hashtag"],
                "platform": "x",
                "objective": "education",
                "tone": "professional",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_saved_copy_rejects_guaranteed_return_claims(self) -> None:
        response = self.client.post(
            "/api/drafts",
            json={
                "topic": "budgeting basics",
                "caption": "Guaranteed returns for everyone.",
                "hashtags": ["#Fundly"],
                "platform": "x",
                "objective": "education",
                "tone": "professional",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_cors_preflight_allows_draft_mutations(self) -> None:
        for method in ("POST", "PATCH"):
            with self.subTest(method=method):
                response = self.client.options(
                    "/api/drafts",
                    headers={
                        "Origin": "http://localhost:3000",
                        "Access-Control-Request-Method": method,
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(method, response.headers.get("access-control-allow-methods", ""))


if __name__ == "__main__":
    unittest.main()
