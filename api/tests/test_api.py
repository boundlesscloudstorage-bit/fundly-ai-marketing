import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.services.draft_store import draft_store


class DemoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        draft_store.clear()
        self.client = TestClient(app)

    def test_health_is_demo_mode(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "mode": "demo"})

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

    def test_generation_returns_valid_deterministic_demo_content(self) -> None:
        request = {
            "topic": "building a monthly budget",
            "platform": "linkedin",
            "objective": "education",
            "tone": "friendly",
            "keywords": "planning, everyday money",
        }
        first = self.client.post("/api/content/generate", json=request)
        second = self.client.post("/api/content/generate", json=request)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), second.json())
        payload = first.json()
        self.assertEqual(payload["platform"], "linkedin")
        self.assertEqual(payload["tone"], "friendly")
        self.assertTrue(payload["is_demo_generated"])
        self.assertEqual(payload["character_count"], len(payload["caption"]))
        self.assertTrue(all(tag.startswith("#") for tag in payload["hashtags"]))

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

    def test_generation_changes_with_tone_and_platform(self) -> None:
        common = {
            "topic": "setting a savings goal",
            "objective": "engagement",
            "tone": "friendly",
        }
        friendly = self.client.post("/api/content/generate", json={**common, "platform": "instagram"}).json()
        inspiring = self.client.post(
            "/api/content/generate",
            json={**common, "platform": "linkedin", "tone": "inspiring"},
        ).json()
        self.assertNotEqual(friendly["caption"], inspiring["caption"])

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

        response = self.client.patch(
            f"/api/drafts/{saved['id']}",
            json={"caption": "Updated caption with a few more words.", "hashtags": ["#MoneyGoals"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["caption"], "Updated caption with a few more words.")
        self.assertEqual(response.json()["hashtags"], ["#MoneyGoals"])
        self.assertEqual(response.json()["character_count"], len(response.json()["caption"]))

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
