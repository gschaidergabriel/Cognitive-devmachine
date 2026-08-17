from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .identity import IdentityRouter
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle


def _lifecycle() -> TurnLifecycle:
    root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    user_id = os.environ.get("CLAYVERSE_USER_ID", "")
    session_id = os.environ.get("CLAYVERSE_SESSION_ID", "")
    return TurnLifecycle(db, user_id, session_id, entityos_bridge=None)


def _read_input() -> dict:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        raise RuntimeError("invalid Claude hook input") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("invalid Claude hook input object")
    return payload


def user_prompt(payload: dict) -> int:
    lifecycle = _lifecycle()
    try:
        result = lifecycle.begin(str(payload.get("prompt", "")))
        context = {
            "identity": {"user_id": result["user_id"], "session_id": result["session_id"]},
            "causal": {"turn_id": result["turn_id"], "episode_id": result["episode_id"], "causal_id": result["causal_id"], "generation": result["generation"]},
            "resources": result["resources"],
            "workspace": result["workspace"],
            "unifieddb_context": result["context"],
            "effect_law": "Any real/state-changing action must use the ClayVerse MCP effect tool and only a verified returned outcome may be claimed.",
        }
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "CLAYVERSE_CANONICAL_CONTEXT\n" + json.dumps(context, ensure_ascii=False, sort_keys=True, default=str),
                "sessionTitle": f"ClayVerse · {result['user_id'].capitalize()}",
            }
        }, ensure_ascii=False))
        return 0
    finally:
        lifecycle.db.close()


def stop(payload: dict) -> int:
    lifecycle = _lifecycle()
    try:
        lifecycle.complete(str(payload.get("last_assistant_message", "")))
        return 0
    except Exception as exc:
        print(f"ClayVerse failed to close causal turn: {exc}", file=sys.stderr)
        return 2
    finally:
        lifecycle.db.close()


def stop_failure(payload: dict) -> int:
    lifecycle = _lifecycle()
    try:
        failure = str(payload.get("error", payload.get("error_type", payload.get("reason", "stop_failure"))))
        lifecycle.abort("claude_stop_failure:" + failure[:500])
        return 0
    finally:
        lifecycle.db.close()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"user_prompt", "stop", "stop_failure"}:
        print("usage: python -m clayverse.hook_bridge <user_prompt|stop|stop_failure>", file=sys.stderr)
        return 64
    payload = _read_input()
    if sys.argv[1] == "user_prompt":
        return user_prompt(payload)
    if sys.argv[1] == "stop":
        return stop(payload)
    return stop_failure(payload)


if __name__ == "__main__":
    raise SystemExit(main())
