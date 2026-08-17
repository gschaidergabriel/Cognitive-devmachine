from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .clerk_auth import AuthenticationError, ClerkConfig, ClerkTokenVerifier
from .inference_protocol import (
    CLAUDE_DECISION_SCHEMA,
    InferenceProtocolError,
    parse_claude_decision_payload,
)


class _MistralNoRedirectHandler(HTTPRedirectHandler):
    """Refuse redirects so a bearer token can never cross the fixed API origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def urlopen(request, timeout):
    """Open one Mistral request with redirect following disabled."""

    return build_opener(_MistralNoRedirectHandler()).open(request, timeout=timeout)


class ClaudeCodeInference:
    """Tool-less Claude Code cognition boundary for ClayVerse.

    Cognition runs with all built-in tools disabled, MCP configuration fail-closed,
    no Claude session persistence, and an explicit environment allowlist. HOME is
    retained so Claude subscription/OAuth credentials remain usable. UnifiedDB /
    WorldAssembler remains the sole durable ClayVerse state authority. Claude may
    return a schema-validated effect intent, but only EffectGate can execute it.
    """

    ENV_ALLOWLIST = (
        "PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
        "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
        "HTTP_PROXY", "HTTPS_PROXY",
        "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    )

    def __init__(self, binary: str | None = None, cwd: str | None = None, timeout: int | None = None):
        self.binary = binary or os.environ.get("CLAUDE_CODE_BIN", "claude")
        self.cwd = cwd or os.environ.get("CLAYVERSE_WORKSPACE", "/workspace")
        self.timeout = int(timeout or os.environ.get("CLAYVERSE_CLAUDE_TIMEOUT_SECONDS", "120"))
        self._lock = threading.Lock()

    @classmethod
    def _subprocess_env(cls) -> dict[str, str]:
        env = {key: os.environ[key] for key in cls.ENV_ALLOWLIST if key in os.environ}
        env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
        env["DISABLE_AUTOUPDATER"] = "1"
        env["CLAUDE_CODE_SKIP_PROMPT_HISTORY"] = "1"
        return env

    def available(self) -> bool:
        executable = shutil.which(self.binary)
        if executable is None:
            return False
        try:
            cp = subprocess.run(
                [executable, "--version"], shell=False, capture_output=True,
                timeout=5, env=self._subprocess_env(),
            )
            return cp.returncode == 0
        except Exception:
            return False

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        world_json = json.dumps(world, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(world_json) > 600_000:
            raise RuntimeError("assembled world exceeds Claude Code boundary")
        system = (
            "You are the cognition engine inside ClayVerse, one persistent central entity shared by authenticated users. "
            "UnifiedDB is authoritative state and the supplied WORLD is the only persisted context for this turn. ClayGraph "
            "is a derived projection. You have no tool authority in this cognition call. Produce the schema-constrained response. "
            "For a normal reply set effect to null. Only when the user's intent and required arguments are sufficiently explicit "
            "may you request entityos.exec or state.noop. Never request process.exec, a shell, or any other capability. If required "
            "action parameters are missing, ask for them in text and set effect to null. An effect is only an intent; ClayVerse "
            "independently validates and executes it through EffectGate."
        )
        prompt = f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}"
        schema = json.dumps(CLAUDE_DECISION_SCHEMA, sort_keys=True, separators=(",", ":"))
        args = [
            self.binary, "-p", prompt, "--output-format", "json", "--json-schema", schema,
            "--max-turns", "1", "--permission-mode", "plan", "--tools", "",
            "--strict-mcp-config", "--no-session-persistence", "--append-system-prompt", system,
        ]
        with self._lock:
            try:
                cp = subprocess.run(
                    args, shell=False, cwd=self.cwd, env=self._subprocess_env(),
                    capture_output=True, text=True, timeout=self.timeout, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Claude Code inference timeout") from exc
        if cp.returncode != 0:
            stderr = cp.stderr.encode("utf-8", errors="replace")
            raise RuntimeError(
                f"Claude Code inference failed rc={cp.returncode} "
                f"stderr_sha256={hashlib.sha256(stderr).hexdigest()} stderr_bytes={len(stderr)}"
            )
        try:
            envelope = json.loads(cp.stdout)
        except json.JSONDecodeError as exc:
            raise InferenceProtocolError("Claude Code envelope is not JSON") from exc
        if not isinstance(envelope, dict) or envelope.get("is_error") is True:
            raise InferenceProtocolError("Claude Code returned an error envelope")
        structured = envelope.get("structured_output")
        if structured is None:
            raise InferenceProtocolError("Claude Code structured_output is missing")
        return parse_claude_decision_payload(structured)


class MistralInference:
    """Token/API cognition boundary used by the final ClayVerse sandbox gate.

    The API token is read for each request and is never retained on this object.
    Mistral has inference authority only: its JSON response is independently parsed
    through the same fail-closed ClayVerse decision protocol. The adapter returns
    only non-secret provider identity/digest metadata; ClayVerseEngine persists that
    proposal before EffectGate can observe any requested effect.
    """

    ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
    MAX_WORLD_BYTES = 600_000
    MAX_OBSERVATION_CHARS = 100_000
    MAX_RESPONSE_BYTES = 2_000_000
    MAX_TOKENS = 4096

    def __init__(self, *, model: str | None = None, timeout: int | None = None):
        self.model = (model or os.environ.get("CLAYVERSE_MISTRAL_MODEL", "")).strip()
        self.timeout = int(timeout or os.environ.get("CLAYVERSE_MISTRAL_TIMEOUT_SECONDS", "120"))
        if self.timeout < 1 or self.timeout > 300:
            raise ValueError("Mistral timeout must be between 1 and 300 seconds")
        self._lock = threading.Lock()

    def available(self) -> bool:
        # Availability is intentionally local-only: do not spend a provider request
        # merely to advertise readiness and never retain the secret on the adapter.
        return bool(self.model and os.environ.get("MISTRAL_API_KEY", "").strip())

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a cognition engine inside ClayVerse, one persistent central entity. "
            "UnifiedDB is authoritative state; the supplied WORLD is bounded context only. "
            "You have no direct tool, shell, filesystem, terminal, EntityOS or effect authority. "
            "Return exactly one JSON object with keys text and effect. effect must be null for a normal reply. "
            "Only when the user's intent and arguments are explicit may effect be an object containing exactly "
            "capability, target and argv. capability may only be entityos.exec or state.noop. entityos.exec requires "
            "a bounded non-empty argv string array; state.noop uses argv null. Never request process.exec, shell "
            "execution, network authority, credentials or any other capability. The response is only a proposal; "
            "ClayVerse independently validates and re-ingests it and EffectGate alone decides whether execution is admitted."
        )

    def reason(self, world: Any, observation: str) -> dict[str, Any]:
        if not self.model or len(self.model) > 256 or "\x00" in self.model:
            raise RuntimeError("CLAYVERSE_MISTRAL_MODEL is required and must be a bounded model id")
        token = os.environ.get("MISTRAL_API_KEY", "")
        if (
            not token
            or token != token.strip()
            or "\x00" in token
            or "\n" in token
            or "\r" in token
        ):
            raise RuntimeError("MISTRAL_API_KEY is required at runtime")
        if (
            not isinstance(observation, str)
            or not observation
            or len(observation) > self.MAX_OBSERVATION_CHARS
            or "\x00" in observation
        ):
            raise InferenceProtocolError("invalid Mistral observation")

        world_json = json.dumps(world, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(world_json.encode("utf-8")) > self.MAX_WORLD_BYTES:
            raise RuntimeError("assembled world exceeds Mistral boundary")

        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": f"WORLD:\n{world_json}\n\nOBSERVATION:\n{observation}"},
                ],
                "response_format": {"type": "json_object"},
                "tools": [],
                "tool_choice": "none",
                "parallel_tool_calls": False,
                "stream": False,
                "temperature": 0,
                "max_tokens": self.MAX_TOKENS,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            self.ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ClayVerse-MistralInference/1",
            },
            method="POST",
        )

        http_error_status = None
        transport_failure_type = None
        try:
            with self._lock:
                with urlopen(request, timeout=self.timeout) as response:
                    raw = response.read(self.MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            # Do not raise while the provider exception is active: ``from None``
            # only suppresses display and still leaves ``__context__`` reachable.
            http_error_status = int(exc.code)
            raw = b""
        except (URLError, TimeoutError, OSError) as exc:
            transport_failure_type = type(exc).__name__
            raw = b""
        finally:
            # Scrub references that can retain the bearer credential before any
            # post-transport validation raises and publishes this frame in traceback.
            token = ""
            request = None

        if http_error_status is not None:
            raise RuntimeError(f"Mistral inference HTTP failure status={http_error_status}")
        if transport_failure_type is not None:
            raise RuntimeError(
                f"Mistral inference transport failure type={transport_failure_type}"
            )

        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise InferenceProtocolError("Mistral response exceeds bound")
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
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
        if model_returned != self.model:
            raise InferenceProtocolError("Mistral response model does not match requested model")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            raise InferenceProtocolError("Mistral response must contain exactly one choice")

        choice = choices[0]
        if choice.get("finish_reason") != "stop":
            raise InferenceProtocolError("Mistral response did not finish cleanly")
        message = choice.get("message")
        if not isinstance(message, dict):
            raise InferenceProtocolError("Mistral choice message is missing")
        content = message.get("content")
        if not isinstance(content, str) or not content or len(content.encode("utf-8")) > self.MAX_RESPONSE_BYTES:
            raise InferenceProtocolError("Mistral message content must be bounded non-empty JSON text")
        try:
            decision_payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise InferenceProtocolError("Mistral message content is not JSON") from exc

        decision = parse_claude_decision_payload(decision_payload)
        decision["inference_receipt"] = {
            "provider": "mistral",
            "model_requested": self.model,
            "model_returned": model_returned,
            "response_id": response_id,
            "finish_reason": "stop",
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        }
        return decision
