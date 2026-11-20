"""Configuration-loading regressions without real credentials or provider calls."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import GeminiSettings, load_gemini_settings
from app.services.content_generator import (
    AIConfigurationError,
    AIInvalidModelConfigurationError,
    ContentGenerator,
)
from app.models import ContentGenerationRequest

API_DIR = Path(__file__).resolve().parents[1]


def make_request() -> ContentGenerationRequest:
    return ContentGenerationRequest(
        topic="monthly budgeting",
        platform="linkedin",
        objective="education",
        tone="friendly",
    )


class GeminiConfigurationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generator_loads_env_file_before_database_module_import(self) -> None:
        env_file = API_DIR / "configuration-fixture" / ".env"
        script = """
import os, sys
from pathlib import Path
import app.config as config
config.API_ENV_FILE = Path(sys.argv[1])
config.dotenv_values = lambda _path: {
    'GEMINI_API_KEY': 'unit-test-key',
    'GEMINI_MODEL': 'gemini-test-model',
}
sys.path.insert(0, str(Path(sys.argv[2])))
os.chdir(sys.argv[3])
from app.services.content_generator import ContentGenerator
generator = ContentGenerator()
assert 'app.database' not in sys.modules
assert config.API_ENV_FILE.is_absolute()
print('configuration_loaded' if generator._api_key == 'unit-test-key' else 'configuration_missing')
print('model_loaded' if generator._model == 'gemini-test-model' else 'model_missing')
"""
        child_env = os.environ.copy()
        child_env.pop("GEMINI_API_KEY", None)
        child_env.pop("GEMINI_MODEL", None)
        result = subprocess.run(
            [sys.executable, "-c", script, str(env_file), str(API_DIR), str(API_DIR.parent)],
            cwd=API_DIR,
            env=child_env,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )

        self.assertEqual(result.stdout.splitlines(), ["configuration_loaded", "model_loaded"])

    async def test_process_environment_takes_precedence_over_dotenv(self) -> None:
        env_file = API_DIR / "configuration-fixture" / ".env"
        values = {
            "GEMINI_API_KEY": "file-key",
            "GEMINI_MODEL": "file-model",
            "GEMINI_USE_PROXY": "true",
        }
        with patch("app.config.dotenv_values", return_value=values):
            with patch.dict(
                os.environ,
                {
                    "GEMINI_API_KEY": "process-key",
                    "GEMINI_MODEL": "process-model",
                    "GEMINI_USE_PROXY": "false",
                },
            ):
                settings = load_gemini_settings(env_file)

        self.assertEqual(
            settings,
            GeminiSettings(api_key="process-key", model="process-model", use_proxy=False),
        )

    async def test_blank_process_settings_fall_back_to_dotenv(self) -> None:
        values = {
            "GEMINI_API_KEY": "file-key",
            "GEMINI_MODEL": "file-model",
            "GEMINI_USE_PROXY": "true",
        }
        with patch("app.config.dotenv_values", return_value=values):
            with patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "  ", "GEMINI_MODEL": "\t", "GEMINI_USE_PROXY": " "},
            ):
                settings = load_gemini_settings(API_DIR / "configuration-fixture" / ".env")

        self.assertEqual(
            settings,
            GeminiSettings(api_key="file-key", model="file-model", use_proxy=True),
        )

    async def test_dotenv_can_enable_proxy_when_required(self) -> None:
        env_file = API_DIR / "configuration-fixture" / "proxy-enabled.env"
        with patch("app.config.dotenv_values", return_value={"GEMINI_USE_PROXY": "true"}):
            with patch.dict(os.environ, {}, clear=True):
                settings = load_gemini_settings(env_file)
        self.assertTrue(settings.use_proxy)

    async def test_proxy_environment_is_ignored_by_default(self) -> None:
        env_file = API_DIR / "configuration-fixture" / "default-proxy.env"
        with patch("app.config.dotenv_values", return_value={}):
            with patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "unit-test-key", "HTTPS_PROXY": "http://unreachable.invalid:9999"},
                clear=True,
            ):
                settings = load_gemini_settings(env_file)
        self.assertFalse(settings.use_proxy)

    async def test_missing_key_is_a_configuration_error(self) -> None:
        env_file = API_DIR / "configuration-fixture" / "empty.env"
        with patch("app.config.dotenv_values", return_value={}):
            with patch.dict(os.environ, {}, clear=True):
                generator = ContentGenerator(env_file=env_file)
                with self.assertRaises(AIConfigurationError):
                    await generator.generate(make_request())

    async def test_invalid_model_is_distinct_from_missing_key(self) -> None:
        env_file = API_DIR / "configuration-fixture" / "invalid-model.env"
        values = {"GEMINI_API_KEY": "unit-test-key", "GEMINI_MODEL": "models/bad"}
        with patch("app.config.dotenv_values", return_value=values):
            with patch.dict(os.environ, {}, clear=True):
                generator = ContentGenerator(env_file=env_file)
                with self.assertRaises(AIInvalidModelConfigurationError):
                    await generator.generate(make_request())


if __name__ == "__main__":
    unittest.main()
