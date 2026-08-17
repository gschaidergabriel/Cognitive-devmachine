from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlsplit


DEFAULT_GLM_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEFAULT_GLM_MODEL = "glm-5.2"
_MAX_WORLD_JSON_CHARS = 600_000
_MAX_OBSERVATION_CHARS = 100_000
_MAX_RESPONSE_BYTES = 2_000_000
_MAX_TOKEN_CHARS = 16_384


class GLMInferenceError(RuntimeError):
    """Fail-closed error for the inference-only GLM boundary."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward the GLM bearer credential across an HTTP redirect."""

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
        raise GLMInferenceError("GLM endpoint is invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "open.bigmodel.cn"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.path != "/api/paas/v4/chat/completions"
        or parsed.query
        or parsed.fragment
    ):
        raise GLMInferenceError("GLM endpoint is outside the admitted provider boundary")
    return endpoint


def _validated_token(value: str) -> str:
    token = value.strip()
    if (
        not token
        or len(token) > _MAX_TOKEN_CHARS
        or any(ord(char) < 0x21 or ord(char) == 0x7F for char in token)
    ):
        raise GLMInferenceError("GLM API token is missing or malformed")
    return token


def _validated_model(value: str) -> str:
    model = value.strip()
    if (
        not model
        or len(model) > 128
        or not model.startswith("glm-")
        or any(ord(char) < 0x21 or ord(char) > 0x7E for char in model)
    ):
        raise GLMInferenceError("GLM model identifier is invalid")
    return model


class GLMTokenInference:
    """Inference-only GLM client for the single ClayVerse causal/state authority.

    This object owns no session, memory, PTY, filesystem, capability, EffectGate or
    EntityOS authority. It accepts already-assembled canonical context and returns a
    text-only decision with ``effect=None`` so any future provider selection can keep
    execution authority inside the existing ClayVerse turn/effect lifecycle.

    The bearer token is intentionally kept only in a private in-memory field and an
    Authorization header. It is never placed in the request body, returned decision,
    exception text, UnifiedDB, receipt or provider metadata by this module.
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
        self.endpoint = _validated_endpoint(
            endpoint or os.environ.get("GLM_API_URL", DEFAULT_GLM_ENDPOINT)
        )
        self.model = _validated_model(model or os.environ.get("GLM_MODEL", DEFAULT_GLM_MODEL))
        self._api_token = _validated_token(
            api_token if api_token is not None else os.environ.get("GLM_API_TOKEN", "")
        )
        try:
            timeout = float(
                timeout_seconds
                if timeout_seconds is not None
                else os.environ.get("CLAYVERSE_GLM_TIMEOUT_SECONDS", "120")
            )
        except (TypeError, ValueError) as exc:
            raise GLMInferenceError("GLM timeout is invalid") from exc
        if not (0.1 <= timeout <= 600.0):
            raise GLMInferenceError("GLM timeout is outside the admitted bound")
        self.timeout_seconds = timeout
        self._opener = opener or urllib.request.build_opener(_NoRedirectHandler())

    def __repr__(self) -> str:
        return (
            f"GLMTokenInference(endpoint={self.endpoint!r}, model={self.model!r}, "
            "api_token=<redacted>)"
        )

    def _payload(self, world: Any, observation: str) -> bytes:
        if (
            not isinstance(observation, str)
            or not observation
            or len(observation) > _MAX_OBSERVATION_CHARS
        ):
            raise GLMInferenceError("GLM observation is outside the admitted text bound")
        try:
            world_json = json.dumps(
                world,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise GLMInferenceError("assembled world is not canonical JSON") from exc
        if len(world_json) > _MAX_WORLD_JSON_CHARS:
            raise GLMInferenceError("assembled world exceeds GLM inference boundary")
        system = (
            "You are an inference-only cognition provider inside ClayVerse. "
            "The supplied WORLD is canonical context assembled by ClayVerse; UnifiedDB remains authoritative. "
            "You have no tools, PTY, filesystem, EffectGate, EntityOS, capability or execution authority. "
            "Return only assistant text. Never claim that an external action was executed."
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
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            # Suppress the provider exception chain entirely: a future transport or
            # provider implementation must not smuggle response/request material into logs.
            raise GLMInferenceError(f"GLM inference failed with HTTP status {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise GLMInferenceError("GLM inference transport failed") from None
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise GLMInferenceError("GLM response exceeds admitted size")
        try:
            envelope = json.loads(raw, parse_constant=_reject_json_constant)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise GLMInferenceError("GLM response is not valid canonical JSON") from exc
        try:
            choices = envelope["choices"]
            message = choices[0]["message"]
            text = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GLMInferenceError("GLM response shape is invalid") from exc
        if not isinstance(text, str) or not text.strip():
            raise GLMInferenceError("GLM response content is invalid")
        response_model = envelope.get("model")
        if not isinstance(response_model, str):
            raise GLMInferenceError("GLM response model identifier is missing or invalid")
        if _validated_model(response_model) != self.model:
            raise GLMInferenceError("GLM response model does not match requested model")
        return {
            "text": text,
            "selection": "respond",
            "effect": None,
            "provider": "glm",
            "model": response_model,
        }
