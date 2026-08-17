from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .inference_protocol import InferenceProtocolError, parse_claude_decision
from .store import StaleGeneration


class MistralInferenceError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MistralInference:
    """Inference-only Mistral boundary; it owns no state, turn, memory, PTY or effect authority."""

    ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
    MAX_WORLD_CHARS = 600_000
    MAX_RESPONSE_BYTES = 2_000_000

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        opener=None,
    ):
        key = api_key if api_key is not None else os.environ.get("MISTRAL_API_KEY", "")
        key = str(key).strip()
        if not key or len(key) > 4096 or any(ch in key for ch in ("\r", "\n", "\x00")):
            raise MistralInferenceError("MISTRAL_API_KEY is required and must be a bounded header value")
        selected_model = str(model or os.environ.get("CLAYVERSE_MISTRAL_MODEL", "mistral-small-latest")).strip()
        if not selected_model or len(selected_model) > 256 or any(ch in selected_model for ch in ("\r", "\n", "\x00")):
            raise MistralInferenceError("invalid Mistral model identifier")
        self._api_key = key
        self.model = selected_model
        self.timeout = int(timeout or os.environ.get("CLAYVERSE_MISTRAL_TIMEOUT_SECONDS", "120"))
        if self.timeout <= 0 or self.timeout > 600:
            raise MistralInferenceError("invalid Mistral timeout")
        self._opener = opener or build_opener(_NoRedirect())

    @staticmethod
    def _bounded_receipt_string(value: Any, name: str, max_length: int = 512) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value or len(value) > max_length or "\x00" in value:
            raise MistralInferenceError(f"invalid {name}")
        return value

    def _request_payload(self, world: Any, observation: str) -> bytes:
        if not isinstance(observation, str) or not observation or len(observation) > 100_000 or "\x00" in observation:
            raise MistralInferenceError("invalid observation")
        try:
            world_json = json.dumps(world, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise MistralInferenceError("assembled world is not canonical JSON") from exc
        if len(world_json) > self.MAX_WORLD_CHARS:
            raise MistralInferenceError("assembled world exceeds Mistral boundary")
        system = (
            "You are a bounded inference engine inside ClayVerse. UnifiedDB is canonical state. "
            "The supplied WORLD is context only. You have no tools, PTY, filesystem, EntityOS or EffectGate authority. "
            "Return exactly one JSON object with keys text and effect. text must be a string and effect must always be null. "
            "Never propose or encode executable actions in effect; ClayVerse handles effects only through a separate canonical turn."
        )
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}"},
            ],
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if self._api_key.encode("utf-8") in encoded:
            raise MistralInferenceError("credential entered request payload")
        return encoded

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        payload = self._request_payload(world, observation)
        request = Request(
            self.ENDPOINT,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            raise MistralInferenceError(f"Mistral HTTP failure status={int(exc.code)}") from None
        except (URLError, TimeoutError, OSError):
            raise MistralInferenceError("Mistral transport failure") from None
        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise MistralInferenceError("Mistral response exceeds boundary")
        try:
            envelope = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MistralInferenceError("Mistral response is not valid JSON") from exc
        if not isinstance(envelope, dict):
            raise MistralInferenceError("Mistral response envelope must be an object")
        choices = envelope.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise MistralInferenceError("Mistral response must contain exactly one choice")
        message = choices[0].get("message")
        if not isinstance(message, dict) or message.get("tool_calls") not in (None, []):
            raise MistralInferenceError("Mistral tool calls are forbidden")
        content = message.get("content")
        if not isinstance(content, str) or not content:
            raise MistralInferenceError("Mistral response content is missing")
        try:
            decision = parse_claude_decision(content)
        except InferenceProtocolError as exc:
            raise MistralInferenceError("Mistral decision violates ClayVerse inference protocol") from exc
        if decision.get("effect") is not None or decision.get("selection") != "respond":
            raise MistralInferenceError("Mistral effect intent is forbidden")
        returned_model = self._bounded_receipt_string(envelope.get("model"), "returned model", 256)
        response_id = self._bounded_receipt_string(envelope.get("id"), "response id", 512)
        finish_reason = self._bounded_receipt_string(choices[0].get("finish_reason"), "finish reason", 128)
        receipt = {
            "provider": "mistral",
            "endpoint_profile": "api.mistral.ai/v1/chat/completions",
            "requested_model": self.model,
            "returned_model": returned_model,
            "response_id": response_id,
            "finish_reason": finish_reason,
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "response_bytes": len(raw),
            "effect_authority": False,
        }
        return {
            "text": decision["text"],
            "selection": "respond",
            "effect": None,
            "provider_receipt": receipt,
        }


class MistralTurnRunner:
    """Runs one Mistral cognition turn through the existing canonical TurnLifecycle."""

    def __init__(self, inference: MistralInference):
        self.inference = inference

    def run(self, lifecycle, prompt: str, resources: list[str] | None = None) -> dict[str, Any]:
        admission = lifecycle.begin(prompt, resources, source="mistral-api:request")
        try:
            lifecycle.db.assert_live_generation(lifecycle.session_id, int(admission["generation"]))
            decision = self.inference.reason(admission["context"], prompt)
            lifecycle.db.assert_live_generation(lifecycle.session_id, int(admission["generation"]))
            completion = lifecycle.complete(
                decision["text"],
                source="mistral-api:response",
                provider_receipt=decision["provider_receipt"],
            )
            if not completion.get("completed") or completion.get("causal_id") != admission["causal_id"]:
                raise MistralInferenceError("Mistral completion diverged from canonical causal turn")
            return {
                "user_id": admission["user_id"],
                "session_id": admission["session_id"],
                "turn_id": admission["turn_id"],
                "assistant_turn_id": completion["assistant_turn_id"],
                "causal_id": admission["causal_id"],
                "generation": admission["generation"],
                "text": decision["text"],
                "provider_receipt": decision["provider_receipt"],
            }
        except Exception:
            try:
                if lifecycle.active() is not None:
                    lifecycle.abort("mistral_turn_failed_or_stale")
            except Exception:
                pass
            raise
