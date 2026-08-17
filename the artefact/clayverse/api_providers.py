from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import sys
import threading
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .inference_protocol import InferenceProtocolError, parse_claude_decision_payload


_PROVIDER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_MISTRAL_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
_PR_GET_DUMPABLE = 3
_PR_SET_DUMPABLE = 4
_SUID_DUMP_DISABLE = 0


class _NoRedirectHandler(HTTPRedirectHandler):
    """Never forward an inference bearer token across a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _urlopen(request: Request, timeout: int):
    return build_opener(_NoRedirectHandler()).open(request, timeout=timeout)


def harden_api_secret_process_boundary() -> dict[str, object]:
    """Make the API-secret-holding service non-dumpable before terminal children exist.

    ClayVerse terminal processes intentionally share the container UID. The provider
    token may enter this service through the runtime secret environment, whose initial
    bytes remain visible through procfs subject to Linux ptrace access checks. Refuse
    API terminal mode unless the kernel can make this process non-dumpable and reports
    that state back. Child processes still receive explicitly sanitized environments.
    """
    if sys.platform != "linux":
        raise RuntimeError("API terminal secret boundary requires Linux PR_SET_DUMPABLE")
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.restype = ctypes.c_int
    result = prctl(_PR_SET_DUMPABLE, _SUID_DUMP_DISABLE, 0, 0, 0)
    if result != 0:
        err = ctypes.get_errno()
        raise OSError(err, "PR_SET_DUMPABLE failed")
    observed = prctl(_PR_GET_DUMPABLE, 0, 0, 0, 0)
    if observed != _SUID_DUMP_DISABLE:
        if observed < 0:
            err = ctypes.get_errno()
            raise OSError(err, "PR_GET_DUMPABLE failed")
        raise RuntimeError("API secret process remained dumpable")
    return {"linux_pr_set_dumpable": True, "process_dumpable": False}


def _validated_https_endpoint(value: str) -> str:
    endpoint = value.strip()
    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("LLM API endpoint is invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path
        or port not in (None, 443)
    ):
        raise ValueError("LLM API endpoint must be a fixed HTTPS URL without credentials/query/fragment")
    return endpoint


def _reject_nonfinite_json(value: str):
    raise ValueError(f"non-finite JSON constant rejected: {value}")


def _reject_duplicate_json_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON object key rejected")
        obj[key] = value
    return obj


@dataclass(frozen=True)
class ChatCompletionsProviderConfig:
    provider: str
    endpoint: str
    model: str
    token_env: str
    protocol: str = "chat-completions-json-v1"

    def __post_init__(self) -> None:
        if not _PROVIDER_RE.fullmatch(self.provider):
            raise ValueError("invalid LLM API provider name")
        object.__setattr__(self, "endpoint", _validated_https_endpoint(self.endpoint))
        model = self.model.strip()
        if not model or len(model) > 256 or "\x00" in model:
            raise ValueError("invalid LLM API model")
        object.__setattr__(self, "model", model)
        if self.token_env not in {"MISTRAL_API_KEY", "CLAYVERSE_LLM_API_TOKEN"}:
            raise ValueError("unapproved LLM API token environment")

    @property
    def endpoint_identity_sha256(self) -> str:
        parsed = urlsplit(self.endpoint)
        identity = f"{parsed.scheme}://{parsed.hostname}{parsed.path}".encode("utf-8")
        return hashlib.sha256(identity).hexdigest()


class GenericChatCompletionsInference:
    """Fail-closed inference-only boundary for JSON chat-completion APIs."""

    MAX_WORLD_BYTES = 600_000
    MAX_OBSERVATION_CHARS = 100_000
    MAX_RESPONSE_BYTES = 2_000_000
    MAX_TOKENS = 4096

    def __init__(self, config: ChatCompletionsProviderConfig, *, timeout: int | None = None):
        self.config = config
        self.timeout = int(timeout or os.environ.get("CLAYVERSE_LLM_API_TIMEOUT_SECONDS", "120"))
        if self.timeout < 1 or self.timeout > 300:
            raise ValueError("LLM API timeout must be between 1 and 300 seconds")
        self._lock = threading.Lock()

    def available(self) -> bool:
        return bool(os.environ.get(self.config.token_env, "").strip())

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are an inference engine inside ClayVerse, one persistent central entity. "
            "UnifiedDB is authoritative state; WORLD is bounded context for this turn. "
            "You have no direct terminal, filesystem, EntityOS, EffectGate, network-effect, "
            "credential or state authority. Return exactly one JSON object with keys text "
            "and effect. effect is null for a normal reply. Only when user intent and all "
            "required arguments are explicit may effect contain exactly capability, target "
            "and argv. capability may only be entityos.exec or state.noop. Never request "
            "process.exec or a shell capability. Your response is only a proposal; ClayVerse "
            "re-ingests and independently validates it before any effect can execute."
        )

    @staticmethod
    def _clean_token(token: str) -> str:
        if (
            not token
            or token != token.strip()
            or "\x00" in token
            or "\n" in token
            or "\r" in token
            or len(token) > 16_384
            or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in token)
        ):
            raise RuntimeError("LLM API token is required at runtime")
        return token

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        token = self._clean_token(os.environ.get(self.config.token_env, ""))
        if (
            not isinstance(observation, str)
            or not observation
            or len(observation) > self.MAX_OBSERVATION_CHARS
            or "\x00" in observation
        ):
            token = ""
            raise InferenceProtocolError("invalid LLM API observation")

        try:
            world_json = json.dumps(
                world,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            token = ""
            raise InferenceProtocolError("LLM API WORLD is not canonical JSON") from exc
        if len(world_json.encode("utf-8")) > self.MAX_WORLD_BYTES:
            token = ""
            raise RuntimeError("assembled world exceeds LLM API boundary")
        if token in world_json or token in observation:
            token = ""
            raise InferenceProtocolError("LLM API runtime credential reached model-visible context")

        try:
            body = json.dumps(
                {
                    "model": self.config.model,
                    "messages": [
                        {"role": "system", "content": self._system_prompt()},
                        {"role": "user", "content": f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}"},
                    ],
                    "response_format": {"type": "json_object"},
                    "stream": False,
                    "temperature": 0,
                    "max_tokens": self.MAX_TOKENS,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            token = ""
            raise InferenceProtocolError("LLM API request is not canonical JSON") from exc
        request = Request(
            self.config.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ClayVerse-GenericInference/1",
            },
            method="POST",
        )

        http_error_status = None
        transport_failure_type = None
        secret_echoed = False
        try:
            with self._lock:
                with _urlopen(request, timeout=self.timeout) as response:
                    raw = response.read(self.MAX_RESPONSE_BYTES + 1)
                    secret_echoed = token.encode("ascii") in raw
        except HTTPError as exc:
            http_error_status = int(exc.code)
            raw = b""
        except (URLError, TimeoutError, OSError) as exc:
            transport_failure_type = type(exc).__name__
            raw = b""
        finally:
            token = ""
            request = None

        if http_error_status is not None:
            raise RuntimeError(f"LLM API inference HTTP failure status={http_error_status}")
        if transport_failure_type is not None:
            raise RuntimeError(f"LLM API inference transport failure type={transport_failure_type}")
        if secret_echoed:
            raw = b""
            raise InferenceProtocolError("LLM API response contains runtime credential")
        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise InferenceProtocolError("LLM API response exceeds bound")

        try:
            envelope = json.loads(raw, parse_constant=_reject_nonfinite_json, object_pairs_hook=_reject_duplicate_json_pairs)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise InferenceProtocolError("LLM API response envelope is not canonical JSON") from exc
        if not isinstance(envelope, dict):
            raise InferenceProtocolError("LLM API response envelope must be an object")

        response_id = envelope.get("id")
        model_returned = envelope.get("model")
        choices = envelope.get("choices")
        if not isinstance(response_id, str) or not response_id or len(response_id) > 512:
            raise InferenceProtocolError("LLM API response id is missing or invalid")
        if not isinstance(model_returned, str) or not model_returned or len(model_returned) > 256:
            raise InferenceProtocolError("LLM API response model is missing or invalid")
        if model_returned != self.config.model:
            raise InferenceProtocolError("LLM API response model does not match requested model")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise InferenceProtocolError("LLM API response must contain exactly one choice")

        choice = choices[0]
        finish_reason = choice.get("finish_reason")
        if finish_reason != "stop":
            raise InferenceProtocolError("LLM API response did not finish cleanly")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise InferenceProtocolError("LLM API choice message is missing")
        content = message.get("content")
        if not isinstance(content, str) or not content or len(content.encode("utf-8")) > self.MAX_RESPONSE_BYTES:
            raise InferenceProtocolError("LLM API message content must be bounded JSON text")
        try:
            decision_payload = json.loads(content, parse_constant=_reject_nonfinite_json, object_pairs_hook=_reject_duplicate_json_pairs)
        except (json.JSONDecodeError, ValueError) as exc:
            raise InferenceProtocolError("LLM API message content is not canonical JSON") from exc

        decision = parse_claude_decision_payload(decision_payload)
        decision["inference_receipt"] = {
            "provider": self.config.provider,
            "protocol": self.config.protocol,
            "model_requested": self.config.model,
            "model_returned": model_returned,
            "response_id": response_id,
            "finish_reason": finish_reason,
            "endpoint_identity_sha256": self.config.endpoint_identity_sha256,
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
        return decision


def build_api_inference_from_env() -> GenericChatCompletionsInference:
    """Build the admitted API inference profile without loading arbitrary code."""

    profile = os.environ.get("CLAYVERSE_LLM_API_PROFILE", "").strip().lower()
    if profile == "mistral":
        model = os.environ.get("CLAYVERSE_LLM_API_MODEL", "").strip() or os.environ.get("CLAYVERSE_MISTRAL_MODEL", "").strip()
        config = ChatCompletionsProviderConfig(
            provider="mistral", endpoint=_MISTRAL_ENDPOINT, model=model, token_env="MISTRAL_API_KEY"
        )
        return GenericChatCompletionsInference(config)

    if profile == "openai-compatible":
        config = ChatCompletionsProviderConfig(
            provider=os.environ.get("CLAYVERSE_LLM_API_NAME", "").strip().lower(),
            endpoint=os.environ.get("CLAYVERSE_LLM_API_ENDPOINT", ""),
            model=os.environ.get("CLAYVERSE_LLM_API_MODEL", ""),
            token_env="CLAYVERSE_LLM_API_TOKEN",
        )
        return GenericChatCompletionsInference(config)

    raise RuntimeError("CLAYVERSE_LLM_API_PROFILE must be mistral or openai-compatible")