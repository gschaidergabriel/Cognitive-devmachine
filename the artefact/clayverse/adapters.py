from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
from typing import Any

from .clerk_auth import AuthenticationError, ClerkConfig, ClerkTokenVerifier
from .inference_protocol import (
    CLAUDE_DECISION_SCHEMA,
    InferenceProtocolError,
    parse_claude_decision_payload,
)


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
