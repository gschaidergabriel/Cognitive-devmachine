from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClaudeReadiness:
    binary_available: bool
    tmux_available: bool
    interactive_cli_version_ok: bool
    authenticated_runtime_verified: bool = False

    def as_dict(self) -> dict[str, bool]:
        return asdict(self)


def _command_ok(argv: list[str], timeout: int = 5) -> bool:
    try:
        cp = subprocess.run(argv, shell=False, capture_output=True, timeout=timeout, check=False)
        return cp.returncode == 0
    except Exception:
        return False


def _credentials_verified(path: str | Path) -> bool:
    """Cheap, local, non-networked check that a real Claude Code OAuth credential
    is present and not expired at the given path.

    This intentionally does not call the Anthropic API: readiness is a boot-time
    substrate check, not a per-request auth call. It only proves the shape a
    genuine `claude setup-token`/`claude login` credential file has: a non-empty
    access token and a future `expiresAt` (epoch milliseconds, matching the
    Claude Code credential file format).
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        oauth = data.get("claudeAiOauth")
        if not isinstance(oauth, dict):
            return False
        token = oauth.get("accessToken")
        expires_at = oauth.get("expiresAt")
        if not isinstance(token, str) or not token:
            return False
        if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
            return False
        return expires_at > time.time() * 1000
    except Exception:
        return False


def claude_readiness(
    inference=None,
    *,
    required: bool,
    credentials_path: str | Path | None = None,
) -> ClaudeReadiness:
    """Source/runtime preflight for the normal interactive Claude Code surface.

    ClayVerse no longer uses `claude --bare -p` as its product runtime. Authentication
    belongs to each durable interactive Claude Code HOME/session and is therefore not
    inferred from ANTHROPIC_API_KEY presence. This preflight proves the CLI binary and
    tmux substrate exist, that `claude --version` succeeds, and -- when a
    ``credentials_path`` is supplied -- that a real, unexpired OAuth credential is on
    disk at that path (see ``_credentials_verified``). Authentication is never required
    for boot to succeed: a signed-out terminal is a normal, reportable state, not a
    startup failure. A live interactive `claude -p` answer remains a separate,
    independent acceptance gate on top of this preflight.

    The optional ``inference`` parameter is retained only for compatibility with older
    unit callers; if provided, its ``available()`` result is used as the binary probe.
    """
    binary_available = bool(inference.available()) if inference is not None else shutil.which("claude") is not None
    tmux_available = shutil.which("tmux") is not None
    version_ok = binary_available and _command_ok(["claude", "--version"])
    authenticated_runtime_verified = (
        _credentials_verified(credentials_path) if credentials_path else False
    )
    status = ClaudeReadiness(
        binary_available=binary_available,
        tmux_available=tmux_available,
        interactive_cli_version_ok=version_ok,
        authenticated_runtime_verified=authenticated_runtime_verified,
    )
    if required and not binary_available:
        raise RuntimeError("Claude Code CLI is required but unavailable")
    if required and not tmux_available:
        raise RuntimeError("tmux is required for permanent ClayVerse terminal sessions")
    if required and not version_ok:
        raise RuntimeError("Claude Code interactive CLI version probe failed")
    return status
