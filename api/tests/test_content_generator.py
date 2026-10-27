"""Provider tests use mocked HTTP responses and never consume API credits."""

from __future__ import annotations

import json
import unittest

import httpx

from app.models import ContentGenerationRequest
from app.services.content_generator import (
    AIConfigurationError,
    AIInvalidResponseError,
    AIProviderError,
    AIProviderTimeoutError,
    ContentGenerator,
)


def make_request() -> ContentGenerationRequest:
    return ContentGenerationRequest(
        topic="monthly budgeting",
        platform="linkedin",
        objective="education",
        tone="friendly",
        keywords="planning",
    )


class ContentGeneratorTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_provider_response_is_validated_and_mapped(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["x-goog-api-key"], "test-key")
            sent = json.loads(request.content)
            self.assertEqual(sent["generationConfig"]["responseMimeType"], "application/json")
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps(
                                            {
                                                "caption": "A thoughtful budgeting message.",
                                                "hashtags": ["#Budgeting", "#Fundly"],
                                            }
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            )

        generator = ContentGenerator(api_key="test-key", transport=httpx.MockTransport(handler))
        generated = await generator.generate(make_request())
        self.assertEqual(generated.topic, "monthly budgeting")
        self.assertEqual(generated.platform, "linkedin")
        self.assertEqual(generated.objective, "education")
        self.assertEqual(generated.tone, "friendly")
        self.assertEqual(generated.character_count, len(generated.caption))
        self.assertFalse(generated.is_demo_generated)

    async def test_missing_api_key_fails_before_network_request(self) -> None:
        generator = ContentGenerator(api_key="")
        with self.assertRaises(AIConfigurationError):
            await generator.generate(make_request())

    async def test_provider_http_error_is_sanitized(self) -> None:
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(429, json={"error": {"message": "private provider detail"}})
        )
        generator = ContentGenerator(api_key="test-key", transport=transport)
        with self.assertRaises(AIProviderError) as caught:
            await generator.generate(make_request())
        self.assertNotIn("private provider detail", str(caught.exception))

    async def test_timeout_is_reported_as_timeout(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("private timeout detail")

        generator = ContentGenerator(api_key="test-key", transport=httpx.MockTransport(handler))
        with self.assertRaises(AIProviderTimeoutError):
            await generator.generate(make_request())

    async def test_invalid_or_unsafe_provider_output_is_rejected(self) -> None:
        for caption in (
            "",
            "Guaranteed returns for everyone.",
            "Our portfolio earned a 12.4% annual return in 2025.",
            "The investment returned by 18.5% last year.",
        ):
            with self.subTest(caption=caption):
                transport = httpx.MockTransport(
                    lambda _request, current=caption: httpx.Response(
                        200,
                        json={
                            "candidates": [
                                {
                                    "content": {
                                        "parts": [
                                            {
                                                "text": json.dumps(
                                                    {"caption": current, "hashtags": ["#Fundly"]}
                                                )
                                            }
                                        ]
                                    }
                                }
                            ]
                        },
                    )
                )
                generator = ContentGenerator(api_key="test-key", transport=transport)
                with self.assertRaises(AIInvalidResponseError):
                    await generator.generate(make_request())

    async def test_malformed_provider_response_is_rejected(self) -> None:
        invalid_payloads = (
            {"candidates": []},
            {"candidates": [{"content": {"parts": [{"text": "not JSON"}]}}]},
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": json.dumps({"caption": "Caption with missing tags."})}]
                        }
                    }
                ]
            },
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                transport = httpx.MockTransport(lambda _request, body=payload: httpx.Response(200, json=body))
                generator = ContentGenerator(api_key="test-key", transport=transport)
                with self.assertRaises(AIInvalidResponseError):
                    await generator.generate(make_request())

    async def test_x_caption_over_platform_limit_is_rejected(self) -> None:
        request = make_request().model_copy(update={"platform": "x"})
        long_caption = "A" * 281
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps(
                                            {"caption": long_caption, "hashtags": ["#Fundly"]}
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            )
        )
        generator = ContentGenerator(api_key="test-key", transport=transport)
        with self.assertRaises(AIInvalidResponseError):
            await generator.generate(request)


if __name__ == "__main__":
    unittest.main()
