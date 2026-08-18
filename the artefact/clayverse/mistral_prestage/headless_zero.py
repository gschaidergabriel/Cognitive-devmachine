from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from .. import identity  # coordinator-owned, imported not edited

MANAGED_SETTINGS = "/etc/claude-code/managed-settings.json"
# Dynamically rendered identity -- the SAME file the interactive tmux terminal
# points --append-system-prompt-file at (clayverse.terminal_sessions). NOT the
# static image copy at /opt/clayverse/runtime/CLAUDE.md.
RUNTIME_PROMPT = "/var/lib/clayverse/runtime/CLAUDE.md"

# Everything managed-settings.json currently permits. Callers may pass a
# narrower subset (F74 "pre-selected tools"); anything outside this set is
# outside managed policy and cannot be granted here regardless.
DEFAULT_ALLOWED_TOOLS = (
    "mcp__clayverse__session_state",
    "mcp__clayverse__request_effect",
    "mcp__clayverse__request_autonomy_effect",
    "mcp__clayverse__udb_embedding_search",
    "mcp__clayverse__udb_embedding_store",
    "mcp__clayverse__udb_neuropedia_activation",
    "mcp__clayverse__udb_memory_add",
    "mcp__clayverse__udb_memory_search",
)

MAX_PROMPT_CHARS = 20_000
DEFAULT_TIMEOUT_SECONDS = 90
_BLOCKED_PREFIX = "UserPromptSubmit operation blocked by hook"


class HeadlessZeroError(RuntimeError):
    pass


def run_headless(
    caveman_prompt: str,
    *,
    user_id: str,
    session_id: str,
    tool_selection: list[str] | None = None,
    home: str = "/var/lib/clay",
    db_path: str = "/var/lib/clay/wiki.db",
    state_root: str = "/var/lib/clayverse",
    max_turns: int = 6,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    pipeline_managed: bool = True,
) -> dict:
    """One headless, non-interactive, tool-capable Zero call.

    Mirrors clayverse.terminal_sessions.TerminalSessionManager.ensure()'s proven
    claude_argv/env_argv shape (same --settings/--setting-sources/--tools/
    --allowedTools/--permission-mode/--append-system-prompt-file) so headless
    Zero gets the SAME identity and policy surface as the interactive terminal,
    not a weaker ad-hoc one. Differs only in invocation shape: -p one-shot
    instead of a long-lived tmux pty session, --no-session-persistence (product
    law: Claude Code is runtime cognition, never durable identity/memory --
    UnifiedDB is; a stateless one-shot call is what forces that).

    ⚠️ MEASURED 2026-08-18, READ BEFORE CALLING WITH A REAL user_id/session_id:
    the managed UserPromptSubmit/Stop/StopFailure hooks (/etc/claude-code/
    managed-settings.json, allowManagedHooksOnly=true) fire on `claude -p`
    exactly as they do interactively -- there is no CLI flag that skips them
    without also losing OAuth auth (--bare requires ANTHROPIC_API_KEY, this
    deployment authenticates via the OAuth credential at
    /var/lib/clay/.claude/.credentials.json, not an API key). Firing means the
    hook independently calls TurnLifecycle.begin_admission()/complete() using
    the raw CAVEMAN prompt as if a human had typed it -- a second, colliding
    admission path, on top of whatever this module's caller does with
    TurnLifecycle itself. pipeline_managed=True sets CLAYVERSE_PIPELINE_MANAGED=1
    in the subprocess env for exactly this reason, but as of 2026-08-18 that
    flag has NO EFFECT -- terminal_hooks.py does not check it yet (proposed
    patch is in the report, not applied; terminal_hooks.py is coordinator-owned).
    Until that patch lands, do not call this with user_id/session_id pointing at
    a real canonical session -- it WILL write permanent turns into that
    session's history. Two such turns already exist in session:andreas from
    this module's own measurement runs; disclosed in the report, not cleaned up
    (turns are an append-only causal ledger by design -- raw deletion would be
    more destructive than the noise it removes).
    """
    if user_id not in {"gabriel", "andreas"}:
        raise HeadlessZeroError("headless Zero requires a canonical user id")
    if not identity.ist_kanonische_sitzung(session_id, user_id):
        raise HeadlessZeroError("session id must be one of the user's canonical session slots")
    if not isinstance(caveman_prompt, str) or not caveman_prompt or len(caveman_prompt) > MAX_PROMPT_CHARS:
        raise HeadlessZeroError("invalid caveman prompt")

    tools = list(tool_selection) if tool_selection else list(DEFAULT_ALLOWED_TOOLS)
    if not tools:
        raise HeadlessZeroError("tool selection must not be empty")
    unknown = set(tools) - set(DEFAULT_ALLOWED_TOOLS)
    if unknown:
        raise HeadlessZeroError(f"tool selection outside managed policy: {sorted(unknown)}")
    if not Path(RUNTIME_PROMPT).is_file():
        raise HeadlessZeroError("runtime identity file missing -- cannot call headless without it")

    argv = [
        "claude", "-p", caveman_prompt,
        "--settings", MANAGED_SETTINGS,
        "--setting-sources", "",
        "--tools", "",
        "--allowedTools", *tools,
        "--permission-mode", "dontAsk",
        "--append-system-prompt-file", RUNTIME_PROMPT,
        "--output-format", "json",
        "--no-session-persistence",
        "--max-turns", str(max_turns),
    ]
    env = {
        "HOME": home,
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "PYTHONPATH": "/opt/clayverse",
        "CLAYVERSE_STATE_ROOT": state_root,
        "CLAYVERSE_DB_PATH": db_path,
        "CLAYVERSE_USER_ID": user_id,
        "CLAYVERSE_SESSION_ID": session_id,
        "DISABLE_UPDATES": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    }
    if pipeline_managed:
        env["CLAYVERSE_PIPELINE_MANAGED"] = "1"

    started = time.perf_counter()
    try:
        cp = subprocess.run(
            argv, env=env, capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HeadlessZeroError("headless Zero call timed out") from exc
    wall_ms = (time.perf_counter() - started) * 1000.0

    if cp.returncode != 0:
        raise HeadlessZeroError(f"headless Zero exited rc={cp.returncode} stderr={cp.stderr[:500]!r}")
    try:
        envelope = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise HeadlessZeroError("headless Zero output is not JSON") from exc
    if not isinstance(envelope, dict):
        raise HeadlessZeroError("headless Zero envelope must be an object")
    if envelope.get("is_error"):
        raise HeadlessZeroError(f"headless Zero returned an error envelope: {str(envelope.get('result',''))[:500]}")

    result_text = envelope.get("result")
    if not isinstance(result_text, str) or not result_text:
        raise HeadlessZeroError("headless Zero returned no result text")
    if result_text.startswith(_BLOCKED_PREFIX):
        raise HeadlessZeroError(f"blocked by managed hook: {result_text[:300]}")

    return {
        "caveman_answer": result_text,
        "num_turns": envelope.get("num_turns"),
        "duration_ms_claude_code": envelope.get("duration_ms"),
        "duration_ms_api": envelope.get("duration_api_ms"),
        "cost_usd": envelope.get("total_cost_usd"),
        "wall_ms": wall_ms,
        "claude_session_id": envelope.get("session_id"),
    }
