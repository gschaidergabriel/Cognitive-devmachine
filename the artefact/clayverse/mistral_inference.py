from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable

from .inference_protocol import InferenceProtocolError, parse_claude_decision_payload


class MistralInference:
    """Inference-only Mistral boundary for the canonical ClayVerse engine.

    The API key is read only at call time from ``MISTRAL_API_KEY`` and is sent only
    in the Authorization header to the fixed Mistral API origin. It is never added
    to prompts, receipts, UnifiedDB provenance, exception messages or returned
    values. Model output remains an untrusted proposal: the existing inference
    protocol parser validates it and ClayVerseEngine re-ingests it before EffectGate.
    """

    API_URL = "https://api.mistral.ai/v1/chat/completions"
    MAX_WORLD_BYTES = 600_000
    MAX_OBSERVATION_CHARS = 100_000
    MAX_RESPONSE_BYTES = 1_000_000

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout: int | None = None,
        max_tokens: int | None = None,
        opener: Callable[..., Any] | None = None,
    ):
        self.model = (model or os.environ.get("MISTRAL_MODEL", "")).strip()
        if not self.model or len(self.model) > 256 or "\x00" in self.model:
            raise RuntimeError("MISTRAL_MODEL is required and must be a bounded model id")

        self.timeout = int(
            timeout
            if timeout is not None
            else os.environ.get("CLAYVERSE_MISTRAL_TIMEOUT_SECONDS", "120")
        )
        if self.timeout < 1 or self.timeout > 300:
            raise ValueError("Mistral timeout must be between 1 and 300 seconds")

        self.max_tokens = int(
            max_tokens
            if max_tokens is not None
            else os.environ.get("CLAYVERSE_MISTRAL_MAX_TOKENS", "4096")
        )
        if self.max_tokens < 1 or self.max_tokens > 32768:
            raise ValueError("Mistral max_tokens must be between 1 and 32768")

        self._open = opener or urllib.request.urlopen

    @staticmethod
    def _api_key() -> str:
        key = os.environ.get("MISTRAL_API_KEY", "")
        if not key or key != key.strip() or "\x00" in key or "\n" in key or "\r" in key:
            raise RuntimeError("MISTRAL_API_KEY is required at runtime")
        return key

    def available(self) -> bool:
        try:
            self._api_key()
        except RuntimeError:
            return False
        return True

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are an inference-only cognition provider inside ClayVerse. UnifiedDB and the supplied WORLD are "
            "the canonical state for this turn. You have no direct tools, filesystem, PTY, shell, memory, state, "
            "or effect authority. Return one JSON object with exactly two keys: text and effect. text is the user-facing "
            "response string. effect is null for a normal response. Only when the user's intent and required arguments "
            "are sufficiently explicit may effect be an object with exactly capability, target, argv, where capability "
            "is entityos.exec or state.noop. entityos.exec requires a bounded non-empty string argv array; state.noop uses "
            "argv null. Never request process.exec, shell execution, network authority, credentials, or any other capability. "
            "If action parameters are missing, ask for them in text and set effect to null. Any effect is only a proposal: "
            "ClayVerse independently re-ingests this response and validates it through EffectGate before execution."
        )

    def _request_bytes(self, world: Any, observation: str) -> bytes:
        if not isinstance(observation, str) or not observation or len(observation) > self.MAX_OBSERVATION_CHARS:
            raise InferenceProtocolError("invalid Mistral observation")
        if "\x00" in observation:
            raise InferenceProtocolError("invalid Mistral observation")

        world_json = json.dumps(
            world,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(world_json.encode("utf-8")) > self.MAX_WORLD_BYTES:
            raise RuntimeError("assembled world exceeds Mistral boundary")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {
                    "role": "user",
                    "content": f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}",
                },
            ],
            "response_format": {"type": "json_object"},
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
            "stream": False,
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        request_bytes = self._request_bytes(world, observation)
        api_key = self._api_key()
        request = urllib.request.Request(
            self.API_URL,
            data=request_bytes,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ClayVerse-MistralInference/1",
            },
        )

        try:
            with self._open(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Mistral inference HTTP {int(exc.code)}") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise RuntimeError("Mistral inference transport failure") from None

        if status < 200 or status >= 300:
            raise RuntimeError(f"Mistral inference HTTP {status}")
        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise RuntimeError("Mistral inference response exceeds boundary")

        try:
            envelope = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InferenceProtocolError("Mistral response envelope is not JSON") from exc
        if not isinstance(envelope, dict):
            raise InferenceProtocolError("Mistral response envelope must be an object")

        response_id = envelope.get("id")
        model_returned = envelope.get("model")
        choices = envelope.get("choices")
        if not isinstance(response_id, str) or not response_id or len(response_id) > 512:
            raise InferenceProtocolError("Mistral response id is missing or invalid")
        if not isinstance(model_returned, str) or not model_returned or len(model_returned) > 256:
            raise InferenceProtocolError("Mistral response model is missing or invalid")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise InferenceProtocolError("Mistral response must contain exactly one choice")

        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            raise InferenceProtocolError("Mistral response did not finish cleanly")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise InferenceProtocolError("Mistral response message is missing")
        content = message.get("content")
        if not isinstance(content, str) or not content or len(content) > self.MAX_RESPONSE_BYTES:
            raise InferenceProtocolError("Mistral structured response content is invalid")

        try:
            structured = json.loads(content)
        except json.JSONDecodeError as exc:
            raise InferenceProtocolError("Mistral structured response is not JSON") from exc
        decision = parse_claude_decision_payload(structured)
        decision["inference_receipt"] = {
            "provider": "mistral",
            "model_requested": self.model,
            "model_returned": model_returned,
            "response_id": response_id,
            "finish_reason": "stop",
            "request_sha256": hashlib.sha256(request_bytes).hexdigest(),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
        return decision
