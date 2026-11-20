"""Central application configuration with a repository-relative env file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

API_DIR = Path(__file__).resolve().parents[1]
API_ENV_FILE = API_DIR / ".env"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"


def load_environment(env_file: Path | None = None) -> None:
    """Load the backend env file by absolute path, independent of process cwd."""
    load_dotenv(env_file or API_ENV_FILE, override=False)


@dataclass(frozen=True)
class GeminiSettings:
    api_key: str = field(repr=False)
    model: str = DEFAULT_GEMINI_MODEL
    use_proxy: bool = False


def _first_nonblank(*values: str | None) -> str:
    """Return the first non-empty trimmed setting value."""
    for value in values:
        if value is not None and value.strip():
            return value.strip()
    return ""


def load_gemini_settings(env_file: Path | None = None) -> GeminiSettings:
    """Read Gemini settings from process env first, then the backend env file.

    This reads the file directly rather than depending on another module to have
    already imported `load_dotenv`, and it never mutates the process environment.
    """
    path = env_file or API_ENV_FILE
    file_values = dotenv_values(path)
    api_key = _first_nonblank(os.getenv("GEMINI_API_KEY"), file_values.get("GEMINI_API_KEY"))
    model = _first_nonblank(os.getenv("GEMINI_MODEL"), file_values.get("GEMINI_MODEL")) or DEFAULT_GEMINI_MODEL
    proxy_setting = _first_nonblank(os.getenv("GEMINI_USE_PROXY"), file_values.get("GEMINI_USE_PROXY")).lower()
    return GeminiSettings(
        api_key=api_key,
        model=model or DEFAULT_GEMINI_MODEL,
        use_proxy=proxy_setting in {"1", "true", "yes", "on"},
    )
