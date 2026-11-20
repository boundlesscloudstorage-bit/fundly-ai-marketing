"""Provider tests use mocked HTTP responses and never consume API credits."""

from __future__ import annotations

import json
import unittest

import httpx

from app.models import ContentGenerationRequest
from app.services.content_generator import (
    AIAuthenticationError,
    AIConfigurationError,
    AIInvalidResponseError,
    AIModelUnavailableError,
    AIProviderConnectionError,
    AIProviderError,
    AIProviderTimeoutError,
    AIProviderUnavailableError,
    AIRequestRejectedError,
    AIRateLimitError,
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

    async def test_x_prompt_and_schema_include_a_safe_character_margin(self) -> None:
        request = make_request().model_copy(update={"platform": "x"})

        def handler(provider_request: httpx.Request) -> httpx.Response:
            sent = json.loads(provider_request.content)
            prompt = sent["contents"][0]["parts"][0]["text"]
            self.assertIn("at most 220 characters", prompt)
            self.assertEqual(sent["generationConfig"]["responseSchema"]["properties"]["caption"]["maxLength"], 220)
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": json.dumps({"caption": "A concise X caption.", "hashtags": ["#Fundly"]})}]
                            }
                        }
                    ]
                },
            )

        generator = ContentGenerator(api_key="test-key", transport=httpx.MockTransport(handler), use_proxy=False)
        generated = await generator.generate(request)
        self.assertEqual(generated.platform, "x")

    async def test_missing_api_key_fails_before_network_request(self) -> None:
        generator = ContentGenerator(api_key="")
        with self.assertRaises(AIConfigurationError):
            await generator.generate(make_request())

    async def test_provider_error_statuses_are_mapped_without_exposing_details(self) -> None:
        cases = (
            (
                httpx.Response(
                    400,
                    json={"error": {"status": "INVALID_ARGUMENT", "message": "API key not valid: fake-secret"}},
                ),
                AIAuthenticationError,
            ),
            (httpx.Response(403, json={"error": {"status": "PERMISSION_DENIED"}}), AIAuthenticationError),
            (httpx.Response(404, json={"error": {"status": "NOT_FOUND"}}), AIModelUnavailableError),
            (
                httpx.Response(
                    400,
                    json={"error": {"status": "INVALID_ARGUMENT", "message": "The requested model was not found."}},
                ),
                AIModelUnavailableError,
            ),
            (httpx.Response(429, json={"error": {"status": "RESOURCE_EXHAUSTED"}}), AIRateLimitError),
            (httpx.Response(400, json={"error": {"status": "INVALID_ARGUMENT"}}), AIRequestRejectedError),
            (
                httpx.Response(500, json={"error": {"message": "private provider detail"}}),
                AIProviderUnavailableError,
            ),
        )
        for provider_response, expected_error in cases:
            with self.subTest(expected_error=expected_error.__name__):
                transport = httpx.MockTransport(lambda _request, item=provider_response: item)
                generator = ContentGenerator(api_key="test-key", transport=transport)
                with self.assertRaises(expected_error) as caught:
                    await generator.generate(make_request())
                self.assertNotIn("fake-secret", str(caught.exception))
                self.assertNotIn("private provider detail", str(caught.exception))

    async def test_timeout_is_reported_as_timeout(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("private timeout detail")

        generator = ContentGenerator(api_key="test-key", transport=httpx.MockTransport(handler))
        with self.assertRaises(AIProviderTimeoutError) as caught:
            await generator.generate(make_request())
        self.assertIsInstance(caught.exception.__cause__, httpx.ReadTimeout)

    async def test_connection_error_is_reported_without_transport_details(self) -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed for test-key")

        generator = ContentGenerator(api_key="test-key", transport=httpx.MockTransport(handler))
        with self.assertRaises(AIProviderConnectionError) as caught:
            await generator.generate(make_request())
        self.assertIsInstance(caught.exception.__cause__, httpx.ConnectError)
        self.assertNotIn("test-key", str(caught.exception))

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
