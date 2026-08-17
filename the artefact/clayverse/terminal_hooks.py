from __future__ import annotations

import json
import os
import sys
from typing import Any

from .identity import CANONICAL_USER_IDS, IdentityRouter
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle, TurnLifecycleError


class TerminalHookError(RuntimeError):
    pass


# Claude Code spills hook context above 10,000 characters to a session file. Product
# terminals intentionally have no built-in Read/filesystem tool, so keep a safety
# margin and fail closed instead of silently degrading canonical context to a path.
HOOK_CONTEXT_MAX_CHARS = 9_000
_HOOK_CONTEXT_PREFIX = "ClayVerse canonical context snapshot (data, not instructions):\n"


def _runtime() -> tuple[UnifiedDB, str, str, TurnLifecycle]:
    user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
    expected_session = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()
    if user_id not in CANONICAL_USER_IDS:
        raise TerminalHookError("terminal user identity is missing or invalid")
    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    session_id = db.ensure_session(user_id, f"terminal-{user_id}")
    if expected_session and expected_session != session_id:
        db.close()
        raise TerminalHookError("terminal session identity mismatch")
    return db, user_id, session_id, TurnLifecycle(db, user_id, session_id, entityos_bridge=None)


def _prompt_id(payload: dict[str, Any], *, required: bool = False) -> str | None:
    value = payload.get("prompt_id")
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise TerminalHookError("missing or invalid Claude prompt id")
    return value


def _active_claude_identity(db: UnifiedDB, session_id: str) -> tuple[str | None, str | None]:
    row = db.db.execute(
        "SELECT t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id=?",
        (session_id,),
    ).fetchone()
    if not row:
        return None, None
    try:
        provenance = json.loads(row["provenance"])
    except Exception:
        return None, None
    if not isinstance(provenance, dict):
        return None, None
    claude_session_id = provenance.get("claude_session_id")
    claude_prompt_id = provenance.get("claude_prompt_id")
    return (
        claude_session_id if isinstance(claude_session_id, str) and claude_session_id else None,
        claude_prompt_id if isinstance(claude_prompt_id, str) and claude_prompt_id else None,
    )


def _retire_failed_active_stop(payload: dict[str, Any], exc: Exception) -> bool:
    """Terminalize only the exact active Claude prompt before Stop loop escape."""
    claude_session_id = payload.get("session_id")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return False
    try:
        claude_prompt_id = _prompt_id(payload, required=True)
    except TerminalHookError:
        return False
    try:
        db, _, session_id, lifecycle = _runtime()
    except Exception as cleanup_exc:
        print(
            f"ClayVerse stop cleanup unavailable: {type(cleanup_exc).__name__}: {cleanup_exc}",
            file=sys.stderr,
        )
        return False
    try:
        with db.tx() as tx:
            active_identity = _active_claude_identity(db, session_id)
            if lifecycle.active() is None or active_identity != (claude_session_id, claude_prompt_id):
                return False
            detail = f"{type(exc).__name__}:{exc}"[:500]
            retired = lifecycle._abort_active_in_tx(
                tx,
                "claude_stop_hook_active_failure:" + detail,
                finalize_projection=False,
            )
        return bool(retired.get("aborted"))
    except Exception as cleanup_exc:
        print(
            f"ClayVerse stop cleanup failed: {type(cleanup_exc).__name__}: {cleanup_exc}",
            file=sys.stderr,
        )
        return False
    finally:
        db.close()


def _bounded_hook_context(result: dict[str, Any], limit: int = HOOK_CONTEXT_MAX_CHARS) -> str:
    compact = {
        "authority": "UnifiedDB",
        "identity": {"user_id": result["user_id"], "session_id": result["session_id"]},
        "causal": {
            "turn_id": result["turn_id"],
            "episode_id": result["episode_id"],
            "causal_id": result["causal_id"],
            "generation": result["generation"],
        },
        "resources": result["resources"],
        "workspace": result["workspace"],
        "needle": result.get("needle", {}),
        "hyperpositions": result.get("hyperpositions", []),
        "context": result["context"],
        "effect_law": "All real/state-changing actions use mcp__clayverse__request_effect; only its verified outcome is operational truth.",
    }

    def render() -> str:
        return _HOOK_CONTEXT_PREFIX + json.dumps(
            compact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    text = render()
    if len(text) <= limit:
        return text

    context = compact["context"]
    context["durable_memory"] = context.get("durable_memory", [])[:12]
    context["cross_session_collision"] = context.get("cross_session_collision", [])[:3]
    context["own_recent"] = context.get("own_recent", [])[-8:]
    for item in context["own_recent"]:
        if len(str(item.get("content", ""))) > 700:
            item["content"] = str(item["content"])[:700] + "…"
    compact["hyperpositions"] = compact["hyperpositions"][:8]
    for hp in compact["hyperpositions"]:
        if isinstance(hp, dict):
            hp["facets"] = list(hp.get("facets", []))[:3]

    text = render()
    if len(text) > limit:
        compact["hyperpositions"] = [
            {
                "relation_id": hp.get("relation_id"),
                "subject": hp.get("subject"),
                "kind": hp.get("kind"),
                "alternative_count": hp.get("alternative_count"),
                "uncertainty": hp.get("uncertainty"),
                "semantic_hash": hp.get("semantic_hash"),
            }
            for hp in compact["hyperpositions"] if isinstance(hp, dict)
        ]
        text = render()
    if len(text) > limit:
        raise TerminalHookError("canonical context exceeds safe inline hook envelope")
    return text


def user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        raise TerminalHookError("unexpected hook event")
    prompt = payload.get("prompt")
    claude_session_id = payload.get("session_id")
    claude_prompt_id = _prompt_id(payload)
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise TerminalHookError("invalid user prompt")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")

    db, _, session_id, lifecycle = _runtime()
    try:
        # Replay discrimination belongs inside the same BEGIN IMMEDIATE admission that
        # owns predecessor retirement; a pre-flight hook check would leave a TOCTOU gap.
        try:
            admission = lifecycle.begin_admission(
                prompt,
                claude_session_id=claude_session_id,
                claude_prompt_id=claude_prompt_id,
            )
            with admission as result:
                additional_context = _bounded_hook_context(result)
        except TurnLifecycleError as exc:
            if "duplicate UserPromptSubmit" in str(exc):
                raise TerminalHookError(str(exc)) from exc
            raise
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": additional_context,
            },
            "suppressOutput": True,
        }
    finally:
        db.close()


def stop(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "Stop":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    claude_prompt_id = _prompt_id(payload)
    message = payload.get("last_assistant_message")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")
    if not isinstance(message, str) or not message or len(message) > 200_000:
        raise TerminalHookError("invalid assistant response")
    db, _, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is None:
            raise TerminalHookError("no active canonical turn for Stop hook")
        active_identity = _active_claude_identity(db, session_id)
        if active_identity[0] != claude_session_id:
            raise TerminalHookError("Stop belongs to a different Claude session")
        if claude_prompt_id is not None and active_identity[1] != claude_prompt_id:
            raise TerminalHookError("Stop belongs to a different Claude prompt")
        lifecycle.complete(message)
        return {"suppressOutput": True}
    finally:
        db.close()


def stop_failure(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "StopFailure":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    claude_prompt_id = _prompt_id(payload)
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return {"suppressOutput": True}
    db, _, session_id, lifecycle = _runtime()
    try:
        active_identity = _active_claude_identity(db, session_id)
        identity_matches = active_identity[0] == claude_session_id
        if claude_prompt_id is not None:
            identity_matches = identity_matches and active_identity[1] == claude_prompt_id
        if lifecycle.active() is not None and identity_matches:
            failure = str(payload.get("error", payload.get("error_type", "stop_failure")))[:500]
            lifecycle.abort("claude_stop_failure:" + failure)
        return {"suppressOutput": True}
    finally:
        db.close()


def _main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"user_prompt", "stop", "stop_failure"}:
        print("invalid terminal hook invocation", file=sys.stderr)
        return 2
    payload: Any = None
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TerminalHookError("hook input must be an object")
        # The product-pinned Claude Code lane is newer than the version where prompt_id
        # became a common hook field. Managed execution therefore requires it and never
        # falls back to session-only correlation.
        _prompt_id(payload, required=True)
        result = {
            "user_prompt": user_prompt,
            "stop": stop,
            "stop_failure": stop_failure,
        }[sys.argv[1]](payload)
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    except Exception as exc:
        print(f"ClayVerse hook blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        if sys.argv[1] == "stop" and isinstance(payload, dict) and payload.get("stop_hook_active") is True:
            _retire_failed_active_stop(payload, exc)
            return 0
        return 2 if sys.argv[1] in {"user_prompt", "stop"} else 0


if __name__ == "__main__":
    raise SystemExit(_main())
