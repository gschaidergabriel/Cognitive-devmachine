from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit


DEFAULT_MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MISTRAL_MODEL = "mistral-small-latest"
_MAX_WORLD_JSON_CHARS = 600_000
_MAX_OBSERVATION_CHARS = 100_000
_MAX_RESPONSE_BYTES = 2_000_000
_MAX_TOKEN_CHARS = 16_384


class MistralInferenceError(RuntimeError):
    """Fail-closed error for the inference-only Mistral boundary."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward the Mistral bearer credential across an HTTP redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _validated_endpoint(value: str) -> str:
    endpoint = value.strip().rstrip("/")
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError as exc:
        raise MistralInferenceError("Mistral endpoint is invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.mistral.ai"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.path != "/v1/chat/completions"
        or parsed.query
        or parsed.fragment
    ):
        raise MistralInferenceError("Mistral endpoint is outside the admitted provider boundary")
    return endpoint


def _validated_token(value: str) -> str:
    token = value.strip()
    if (
        not token
        or len(token) > _MAX_TOKEN_CHARS
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in token)
    ):
        raise MistralInferenceError("Mistral API token is missing or malformed")
    return token


def _validated_model(value: str) -> str:
    model = value.strip()
    if (
        not model
        or len(model) > 128
        or not (model.startswith("mistral-") or model.startswith("ministral-"))
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in model)
    ):
        raise MistralInferenceError("Mistral model identifier is invalid")
    return model


class MistralTokenInference:
    """Inference-only Mistral adapter for the single ClayVerse causal authority.

    The adapter accepts canonical context already assembled by ClayVerse and returns
    text-only cognition with ``effect=None``. It owns no session, durable memory,
    PTY, filesystem, EffectGate, EntityOS, capability or truth authority.

    ``MISTRAL_API_KEY`` is authentication material only. The key is held in a
    private in-memory field and an Authorization header, never in the request body,
    return value, provider metadata, receipt, UnifiedDB or ClayGraph by this module.
    """

    def __init__(
        self,
        *,
        api_token: str | None = None,
        model: str | None = None,
        endpoint: str | None = None,
        timeout_seconds: float | None = None,
        opener: Any | None = None,
    ):
        endpoint_value = (
            endpoint
            if endpoint is not None
            else os.environ.get("MISTRAL_API_URL", DEFAULT_MISTRAL_ENDPOINT)
        )
        model_value = (
            model
            if model is not None
            else os.environ.get("MISTRAL_MODEL", DEFAULT_MISTRAL_MODEL)
        )
        self.endpoint = _validated_endpoint(endpoint_value)
        self.model = _validated_model(model_value)
        self._api_token = _validated_token(
            api_token if api_token is not None else os.environ.get("MISTRAL_API_KEY", "")
        )
        try:
            timeout = float(
                timeout_seconds
                if timeout_seconds is not None
                else os.environ.get("CLAYVERSE_MISTRAL_TIMEOUT_SECONDS", "120")
            )
        except (TypeError, ValueError) as exc:
            raise MistralInferenceError("Mistral timeout is invalid") from exc
        if not (0.1 <= timeout <= 600.0):
            raise MistralInferenceError("Mistral timeout is outside the admitted bound")
        self.timeout_seconds = timeout
        self._opener = opener or urllib.request.build_opener(_NoRedirectHandler())

    def __repr__(self) -> str:
        return (
            f"MistralTokenInference(endpoint={self.endpoint!r}, model={self.model!r}, "
            "api_token=<redacted>)"
        )

    def _payload(self, world: Any, observation: str) -> bytes:
        if (
            not isinstance(observation, str)
            or not observation
            or len(observation) > _MAX_OBSERVATION_CHARS
        ):
            raise MistralInferenceError("Mistral observation is outside the admitted text bound")
        try:
            world_json = json.dumps(
                world,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise MistralInferenceError("assembled world is not canonical JSON") from exc
        if len(world_json) > _MAX_WORLD_JSON_CHARS:
            raise MistralInferenceError("assembled world exceeds Mistral inference boundary")
        if self._api_token in world_json or self._api_token in observation:
            raise MistralInferenceError("Mistral credential appeared in inference content")
        system = (
            "You are an inference-only cognition provider inside ClayVerse. "
            "WORLD is canonical context assembled by ClayVerse; UnifiedDB remains authoritative. "
            "You have no tools, PTY, filesystem, EffectGate, EntityOS, capability, truth-promotion "
            "or execution authority. Return assistant text only and never claim an external action executed."
        )
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}",
                },
            ],
            "stream": False,
        }
        return json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        payload = self._payload(world, observation)
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        http_status: int | None = None
        transport_failed = False
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            http_status = int(exc.code)
            raw = b""
        except (urllib.error.URLError, TimeoutError, OSError):
            transport_failed = True
            raw = b""
        if http_status is not None:
            raise MistralInferenceError(
                f"Mistral inference failed with HTTP status {http_status}"
            )
        if transport_failed:
            raise MistralInferenceError("Mistral inference transport failed")
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise MistralInferenceError("Mistral response exceeds admitted size")
        parse_failed = False
        try:
            envelope = json.loads(raw, parse_constant=_reject_json_constant)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            parse_failed = True
            envelope = None
        if parse_failed:
            raise MistralInferenceError("Mistral response is not valid canonical JSON")
        try:
            choices = envelope["choices"]
            message = choices[0]["message"]
            text = message["content"]
        except (KeyError, IndexError, TypeError):
            raise MistralInferenceError("Mistral response shape is invalid") from None
        if not isinstance(text, str) or not text.strip():
            raise MistralInferenceError("Mistral response content is invalid")
        if not isinstance(envelope, dict):
            raise MistralInferenceError("Mistral response shape is invalid")
        response_model = envelope.get("model")
        if not isinstance(response_model, str):
            raise MistralInferenceError("Mistral response model identifier is missing or invalid")
        if _validated_model(response_model) != self.model:
            raise MistralInferenceError("Mistral response model does not match requested model")
        if self._api_token in text:
            raise MistralInferenceError("Mistral credential appeared in provider response")
        return {
            "text": text,
            "selection": "respond",
            "effect": None,
            "provider": "mistral",
            "model": response_model,
        }
