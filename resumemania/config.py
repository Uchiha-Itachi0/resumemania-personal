"""Settings loaded from the environment (.env). Nothing secret lives in code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FAST_MODEL = "gemini-3.5-flash-lite"
# gemini-3.8-flash gives deeper answers but has had Google capacity outages (503/504)
# since Oct 2026. Switch GEMINI_MODEL_SMART in .env once it is stable.
DEFAULT_SMART_MODEL = "gemini-3.5-flash-lite"
DEFAULT_FALLBACK_MODELS = "gemini-3.5-flash"
DEFAULT_TIMEOUT_SECONDS = 45
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "resumemania.db"
DEFAULT_MAX_UPLOAD_MB = 5


class MissingApiKeyError(RuntimeError):
    """Raised when GEMINI_API_KEY is not set."""


@dataclass(frozen=True)
class Settings:
    api_key: str
    fast_model: str
    smart_model: str
    fallback_models: tuple[str, ...]
    timeout_seconds: int
    db_path: Path
    max_upload_mb: int

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def require_api_key(self) -> str:
        if not self.api_key:
            raise MissingApiKeyError(
                "GEMINI_API_KEY is missing. Copy .env.example to .env and add your key."
            )
        return self.api_key


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a whole number, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0, got {value}")
    return value


def load_settings(env_file: Path | None = None) -> Settings:
    """Read settings from the environment, loading .env first if present."""
    load_dotenv(env_file or PROJECT_ROOT / ".env", override=False)
    db_raw = os.getenv("RESUMEMANIA_DB_PATH", "").strip()
    return Settings(
        api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        fast_model=os.getenv("GEMINI_MODEL_FAST", "").strip() or DEFAULT_FAST_MODEL,
        smart_model=os.getenv("GEMINI_MODEL_SMART", "").strip() or DEFAULT_SMART_MODEL,
        fallback_models=tuple(
            m.strip() for m in os.getenv("GEMINI_MODEL_FALLBACKS", DEFAULT_FALLBACK_MODELS).split(",")
            if m.strip()
        ),
        timeout_seconds=_int_env("GEMINI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
        db_path=Path(db_raw) if db_raw else DEFAULT_DB_PATH,
        max_upload_mb=_int_env("RESUMEMANIA_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB),
    )
