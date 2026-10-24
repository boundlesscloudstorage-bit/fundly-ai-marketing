import unittest

from fastapi.testclient import TestClient

from app.main import app


class DemoApiTests(unittest.TestCase):
    def setUp(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
