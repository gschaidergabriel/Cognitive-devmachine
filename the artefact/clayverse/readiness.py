from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ClaudeReadiness:
    binary_available: bool
    bare_api_key_configured: bool
    authenticated_runtime_verified: bool = False

    def as_dict(self) -> dict[str, bool]:
        return asdict(self)


def claude_readiness(inference: Any, *, required: bool) -> ClaudeReadiness:
    """Fail closed for the exact ClayVerse Claude Code invocation contract.

    ClayVerse invokes `claude --bare -p`. Bare mode intentionally does not consume
    subscription/OAuth state, and this artifact does not provide an explicit
    `--settings` apiKeyHelper or cloud-provider route. Therefore the admitted
    credential for this source shape is a non-empty ANTHROPIC_API_KEY.

    This preflight proves configuration only. It deliberately does not claim that
    Anthropic accepted the credential; authenticated runtime verification remains
    an external executable gate until an actual isolated inference succeeds.
    """
    binary_available = bool(inference.available())
    api_key_configured = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    status = ClaudeReadiness(
        binary_available=binary_available,
        bare_api_key_configured=api_key_configured,
    )
    if required and not binary_available:
        raise RuntimeError("Claude Code CLI is required but unavailable")
    if required and not api_key_configured:
        raise RuntimeError("ANTHROPIC_API_KEY is required for ClayVerse Claude Code --bare inference")
    return status
