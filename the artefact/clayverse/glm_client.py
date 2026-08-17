from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable


class GLMConfigError(RuntimeError):
    pass


class GLMInferenceError(RuntimeError):
    pass


_ENDPOINTS = {
    "global": "https://api.z.ai/api/paas/v4/chat/completions",
    "cn": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
}

_MAX_REQUEST_BYTES = 750_000
_MAX_RESPONSE_BYTES = 2_000_000
_MAX_TEXT_CHARS = 200_000


@dataclass(frozen=True)
class GLMInferenceResult:
    text: str
    turn_id: str
    causal_id: str
    generation: int
    requested_model: str
    provider_model: str | None
    provider_request_id: str | None


Transport = Callable[[urllib.request.Request, float, int], tuple[int, bytes]]


def _default_transport(request: urllib.request.Request, timeout: float, max_bytes: int) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        body = exc.read(max_bytes + 1)
        status = int(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GLMInferenceError(f"GLM transport unavailable ({type(exc).__name__})") from exc
    if len(body) > max_bytes:
        raise GLMInferenceError("GLM response exceeds bounded envelope")
    return status, body


def _identity(value: str, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048 or "\x00" in value:
        raise GLMInferenceError(f"invalid {name}")
    return value


class GLMInferenceClient:
    """Inference-only GLM boundary; never a turn, memory, terminal or effect authority.

    The caller owns canonical UnifiedDB lifecycle identity. This client only sends a
    bounded text inference request and returns the same caller-supplied turn/causal/
    generation identity alongside bounded provider text. It never executes tool calls,
    never writes state, and never exposes the bearer token in payloads or errors.
    """

    def __init__(
        self,
        *,
        token: str,
        model: str,
        endpoint: str = "global",
        timeout_seconds: float = 120.0,
        transport: Transport | None = None,
    ):
        if not isinstance(token, str) or not token or token != token.strip() or len(token) > 8192 or any(c in token for c in "\r\n"):
            raise GLMConfigError("invalid GLM API token")
        if not isinstance(model, str) or not model or len(model) > 128 or any(c.isspace() for c in model) or "\x00" in model:
            raise GLMConfigError("invalid GLM model")
        if endpoint not in _ENDPOINTS:
            raise GLMConfigError("GLM endpoint must be one of the pinned official endpoint profiles")
        try:
            timeout = float(timeout_seconds)
        except (TypeError, ValueError) as exc:
            raise GLMConfigError("invalid GLM timeout") from exc
        if not 1.0 <= timeout <= 600.0:
            raise GLMConfigError("GLM timeout outside admitted bounds")
        self._token = token
        self.model = model
        self.endpoint_profile = endpoint
        self.url = _ENDPOINTS[endpoint]
        self.timeout_seconds = timeout
        self._transport = transport or _default_transport

    @classmethod
    def from_env(cls, *, transport: Transport | None = None) -> "GLMInferenceClient":
        token = os.environ.get("GLM_API_TOKEN", "")
        model = os.environ.get("GLM_MODEL", "")
        endpoint = os.environ.get("GLM_API_ENDPOINT", "global")
        timeout = os.environ.get("GLM_TIMEOUT_SECONDS", "120")
        return cls(token=token, model=model, endpoint=endpoint, timeout_seconds=timeout, transport=transport)

    def infer(
        self,
        *,
        context: object,
        observation: str,
        turn_id: str,
        causal_id: str,
        generation: int,
    ) -> GLMInferenceResult:
        turn_id = _identity(turn_id, "turn_id")
        causal_id = _identity(causal_id, "causal_id")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            raise GLMInferenceError("invalid generation")
        if not isinstance(observation, str) or not observation or len(observation) > 100_000 or "\x00" in observation:
            raise GLMInferenceError("invalid observation")
        try:
            context_json = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        except (TypeError, ValueError) as exc:
            raise GLMInferenceError("context is not serializable") from exc
        if len(context_json) > 600_000:
            raise GLMInferenceError("assembled context exceeds GLM boundary")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an inference engine inside ClayVerse. UnifiedDB and the supplied context are authoritative. "
                        "Return assistant text only. You have no terminal, filesystem, tool, EntityOS, EffectGate or external-effect authority."
                    ),
                },
                {"role": "user", "content": f"CONTEXT:\n{context_json}\n\nOBSERVATION:\n{observation}"},
            ],
            "stream": False,
        }
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(body) > _MAX_REQUEST_BYTES:
            raise GLMInferenceError("GLM request exceeds bounded envelope")
        request = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        status, response_body = self._transport(request, self.timeout_seconds, _MAX_RESPONSE_BYTES)
        if not 200 <= status < 300:
            digest = hashlib.sha256(response_body).hexdigest()
            raise GLMInferenceError(f"GLM HTTP failure status={status} body_sha256={digest} body_bytes={len(response_body)}")
        try:
            envelope = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GLMInferenceError("GLM response is not valid JSON") from exc
        if not isinstance(envelope, dict):
            raise GLMInferenceError("GLM response envelope must be an object")
        choices = envelope.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise GLMInferenceError("GLM response must contain exactly one choice")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise GLMInferenceError("GLM response message missing")
        if message.get("tool_calls") not in (None, []):
            raise GLMInferenceError("GLM tool calls are forbidden at the inference boundary")
        text = message.get("content")
        if not isinstance(text, str) or len(text) > _MAX_TEXT_CHARS or "\x00" in text:
            raise GLMInferenceError("invalid GLM response text")

        provider_model = envelope.get("model")
        if provider_model is not None and (not isinstance(provider_model, str) or len(provider_model) > 256):
            raise GLMInferenceError("invalid GLM provider model identity")
        provider_request_id = envelope.get("request_id", envelope.get("id"))
        if provider_request_id is not None and (not isinstance(provider_request_id, str) or len(provider_request_id) > 512):
            raise GLMInferenceError("invalid GLM provider request identity")

        return GLMInferenceResult(
            text=text,
            turn_id=turn_id,
            causal_id=causal_id,
            generation=generation,
            requested_model=self.model,
            provider_model=provider_model,
            provider_request_id=provider_request_id,
        )
