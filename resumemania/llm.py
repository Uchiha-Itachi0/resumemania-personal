"""Thin wrapper over Gemini that always returns a validated Pydantic object.

Agents depend on the `StructuredLLM` protocol, so tests swap in `FakeLLM`.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_ATTEMPTS = 2
RETRY_BASE_SECONDS = 1.5
DEFAULT_TIMEOUT_SECONDS = 45
# After a model fails with an outage error, skip it for this long so later steps don't wait on it.
COOLDOWN_SECONDS = 300


class LLMError(RuntimeError):
    """The model failed or returned something we could not use."""


class StructuredLLM(Protocol):
    def generate(
        self, *, model: str, system: str, prompt: str, schema: type[T], step: str
    ) -> T: ...


def _default_client(api_key: str, timeout_seconds: int) -> object:
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key, http_options=types.HttpOptions(timeout=timeout_seconds * 1000)
    )


class GeminiLLM:
    """Calls Gemini with JSON output bound to a Pydantic schema.

    Every call has a timeout. If a model is busy (503), times out (504) or is too slow,
    the call moves straight to the next model in `fallback_models`, so one overloaded model
    never blocks you. A model that failed is skipped for COOLDOWN_SECONDS, so only the first
    step pays for an outage. Malformed JSON is retried once on the same model.

    Temperature is left at Gemini's default: Google's Gemini 3 guide deprecates setting it.
    """

    def __init__(
        self,
        api_key: str,
        fallback_models: tuple[str, ...] = (),
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        client_factory: Callable[[str, int], object] | None = None,
    ):
        if not api_key:
            raise LLMError("GEMINI_API_KEY is missing.")
        self._client = (client_factory or _default_client)(api_key, timeout_seconds)
        self._fallbacks = tuple(m.strip() for m in fallback_models if m.strip())
        self._cooldown_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def generate(
        self, *, model: str, system: str, prompt: str, schema: type[T], step: str
    ) -> T:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
        )
        candidates = self._healthy([model, *self._fallbacks])
        last_error: Exception | None = None
        for index, candidate in enumerate(candidates):
            try:
                return self._call(candidate, config, prompt, schema, step)
            except _ModelUnavailable as exc:
                last_error = exc.__cause__
                self._cool_down(candidate)
                if index + 1 < len(candidates):
                    logger.warning("step=%s model=%s status=failover to=%s",
                                   step, candidate, candidates[index + 1])
        raise LLMError(
            f"Gemini is busy and couldn't finish '{step}'. Wait a minute and try again."
        ) from last_error

    def _healthy(self, models: list[str]) -> list[str]:
        """Unique models in order, minus any cooling down. Never returns an empty list."""
        ordered = list(dict.fromkeys(models))
        now = time.monotonic()
        with self._lock:
            healthy = [m for m in ordered if self._cooldown_until.get(m, 0.0) <= now]
        skipped = [m for m in ordered if m not in healthy]
        if skipped:
            logger.info("skipping models in cooldown: %s", ",".join(skipped))
        return healthy or ordered

    def _cool_down(self, model: str) -> None:
        with self._lock:
            self._cooldown_until[model] = time.monotonic() + COOLDOWN_SECONDS

    def _call(self, model: str, config: object, prompt: str, schema: type[T], step: str) -> T:
        import httpx
        from google.genai import errors

        for attempt in range(1, MAX_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                response = self._client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                result = _parse_response(response, schema)
                logger.info("step=%s model=%s status=ok attempt=%d ms=%d", step, model, attempt, _ms_since(started))
                return result
            except errors.ClientError as exc:
                if exc.code == 429:
                    # Rate limited on this model: another model has its own quota.
                    logger.warning("step=%s model=%s status=rate_limited ms=%d", step, model, _ms_since(started))
                    raise _ModelUnavailable() from exc
                # Bad key, unknown model, bad request. Retrying will not help.
                logger.warning("step=%s model=%s status=client_error code=%s", step, model, exc.code)
                raise LLMError(_client_error_message(exc, model)) from exc
            except (errors.ServerError, httpx.TimeoutException) as exc:
                logger.warning("step=%s model=%s status=unavailable error=%s code=%s ms=%d",
                               step, model, type(exc).__name__, getattr(exc, "code", "-"),
                               _ms_since(started))
                raise _ModelUnavailable() from exc
            except (ValidationError, ValueError) as exc:
                logger.warning("step=%s model=%s status=bad_output attempt=%d ms=%d",
                               step, model, attempt, _ms_since(started))
                if attempt == MAX_ATTEMPTS:
                    raise _ModelUnavailable() from exc
                time.sleep(RETRY_BASE_SECONDS * attempt)
        raise AssertionError("unreachable")


def _ms_since(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


class _ModelUnavailable(Exception):
    """Internal: this model can't answer right now. Try the next one."""


def _parse_response(response: object, schema: type[T]) -> T:
    parsed = getattr(response, "parsed", None)
    if isinstance(parsed, schema):
        return parsed
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from model")
    return schema.model_validate_json(text)


def _client_error_message(exc: Exception, model: str) -> str:
    code = getattr(exc, "code", None)
    detail = f"{getattr(exc, 'message', '')} {getattr(exc, 'status', '')}".lower()
    if code in (401, 403) or "api key" in detail or "api_key" in detail:
        return "Your Gemini API key was rejected. Check GEMINI_API_KEY in .env."
    if code == 404:
        return f"Model '{model}' was not found. Check the model names in .env."
    if code == 429:
        return "You've hit the Gemini rate limit. Wait a minute and try again."
    return f"Gemini refused the request ({code}). Check your .env settings."


class FakeLLM:
    """Test double: returns canned objects by schema, records every call."""

    def __init__(self, responses: dict[type[BaseModel], BaseModel | Exception]):
        self._responses = dict(responses)
        self.calls: list[dict[str, str]] = []

    def generate(
        self, *, model: str, system: str, prompt: str, schema: type[T], step: str
    ) -> T:
        self.calls.append({"model": model, "step": step, "prompt": prompt, "system": system})
        response = self._responses.get(schema)
        if response is None:
            raise LLMError(f"FakeLLM has no response for {schema.__name__}")
        if isinstance(response, Exception):
            raise response
        return response.model_copy(deep=True)  # type: ignore[return-value]
