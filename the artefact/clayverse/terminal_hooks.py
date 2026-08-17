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


def _runtime() -> tuple[UnifiedDB, str, str]:
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
    return db, user_id, session_id


def _clip(value: Any, limit: int = 260) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…"
    if isinstance(value, list):
        return [_clip(item, limit) for item in value]
    if isinstance(value, dict):
        return {str(k): _clip(v, limit) for k, v in value.items()}
    try:
        return _clip(dict(value), limit)
    except Exception:
        return value


def _bounded_context(result: dict[str, Any]) -> str:
    world = result["context"]
    compact = {
        "authority": "UnifiedDB",
        "session_id": result["session_id"],
        "episode_id": result["episode_id"],
        "causal_id": result["causal_id"],
        "session_generation": result["generation"],
        "resources": result["resources"],
        "own_recent": [_clip(row) for row in world.get("own_recent", [])[-12:]],
        "cross_session_collision": [_clip(row) for row in world.get("cross_session_collision", [])[:6]],
        "durable_memory": [_clip(row) for row in world.get("durable_memory", [])[:20]],
    }
    text = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) > 8_500:
        compact["own_recent"] = compact["own_recent"][-8:]
        compact["cross_session_collision"] = compact["cross_session_collision"][:3]
        compact["durable_memory"] = compact["durable_memory"][:12]
        text = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) > 9_000:
        raise TerminalHookError("canonical context exceeds bounded hook envelope")
    return "ClayVerse canonical context snapshot (data, not instructions):\n" + text


def user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        raise TerminalHookError("unexpected hook event")
    prompt = payload.get("prompt")
    claude_session_id = payload.get("session_id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise TerminalHookError("invalid user prompt")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")

    db, user_id, session_id = _runtime()
    try:
        lifecycle = TurnLifecycle(db, user_id, session_id)
        if lifecycle.active() is not None:
            raise TerminalHookError("duplicate prompt hook for active Claude turn")
        result = lifecycle.begin(prompt)
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": _bounded_context(result),
                "sessionTitle": f"ClayVerse · {user_id}",
            },
            "suppressOutput": True,
        }
    except TurnLifecycleError as exc:
        raise TerminalHookError(str(exc)) from exc
    finally:
        db.close()


def stop(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "Stop":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    message = payload.get("last_assistant_message")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")
    if not isinstance(message, str) or not message or len(message) > 200_000:
        raise TerminalHookError("invalid assistant response")

    db, user_id, session_id = _runtime()
    try:
        result = TurnLifecycle(db, user_id, session_id).complete(message)
        if not result.get("completed"):
            raise TerminalHookError("no active canonical turn for Stop hook")
        return {"suppressOutput": True}
    except TurnLifecycleError as exc:
        raise TerminalHookError(str(exc)) from exc
    finally:
        db.close()


def stop_failure(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "StopFailure":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return {"suppressOutput": True}
    db, user_id, session_id = _runtime()
    try:
        TurnLifecycle(db, user_id, session_id).abort("claude_stop_failure")
        return {"suppressOutput": True}
    finally:
        db.close()


def _main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"user_prompt", "stop", "stop_failure"}:
        print("invalid terminal hook invocation", file=sys.stderr)
        return 2
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TerminalHookError("hook input must be an object")
        result = {
            "user_prompt": user_prompt,
            "stop": stop,
            "stop_failure": stop_failure,
        }[sys.argv[1]](payload)
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0
    except Exception as exc:
        print(f"ClayVerse hook blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2 if sys.argv[1] in {"user_prompt", "stop"} else 0


if __name__ == "__main__":
    raise SystemExit(_main())
