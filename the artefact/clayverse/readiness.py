from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass


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


def claude_readiness(inference=None, *, required: bool) -> ClaudeReadiness:
    """Source/runtime preflight for the normal interactive Claude Code surface.

    ClayVerse no longer uses `claude --bare -p` as its product runtime. Authentication
    belongs to each durable interactive Claude Code HOME/session and is therefore not
    inferred from ANTHROPIC_API_KEY presence. This preflight proves only that the CLI
    binary and tmux substrate exist and that `claude --version` succeeds. A real signed-in
    interactive session remains a separate executable acceptance gate.

    The optional ``inference`` parameter is retained only for compatibility with older
    unit callers; if provided, its ``available()`` result is used as the binary probe.
    """
    binary_available = bool(inference.available()) if inference is not None else shutil.which("claude") is not None
    tmux_available = shutil.which("tmux") is not None
    version_ok = binary_available and _command_ok(["claude", "--version"])
    status = ClaudeReadiness(
        binary_available=binary_available,
        tmux_available=tmux_available,
        interactive_cli_version_ok=version_ok,
        authenticated_runtime_verified=False,
    )
    if required and not binary_available:
        raise RuntimeError("Claude Code CLI is required but unavailable")
    if required and not tmux_available:
        raise RuntimeError("tmux is required for permanent ClayVerse terminal sessions")
    if required and not version_ok:
        raise RuntimeError("Claude Code interactive CLI version probe failed")
    return status
