from __future__ import annotations

import json
import os
import sys
from typing import Any

from .agency import AgencyView
from .identity import CANONICAL_USER_IDS, IdentityRouter
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle


class TerminalHookError(RuntimeError):
    pass


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


def _active_claude_session(db: UnifiedDB, session_id: str) -> str | None:
    row = db.db.execute(
        "SELECT t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id=?",
        (session_id,),
    ).fetchone()
    if not row:
        return None
    try:
        provenance = json.loads(row["provenance"])
    except Exception:
        return None
    value = provenance.get("claude_session_id") if isinstance(provenance, dict) else None
    return value if isinstance(value, str) and value else None


def _truncate(value: Any, limit: int) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    return value


def _compact_agency(agency: dict[str, Any]) -> dict[str, Any]:
    compact = dict(agency)
    autonomy = dict(compact.get("autonomy", {}))
    goals = []
    for raw in list(autonomy.get("goals", []))[:4]:
        if not isinstance(raw, dict):
            continue
        goal = dict(raw)
        goal["objective"] = _truncate(goal.get("objective"), 900)
        step = goal.get("current_step")
        if isinstance(step, dict):
            step = dict(step)
            step["description"] = _truncate(step.get("description"), 700)
            goal["current_step"] = step
        goal["evidence_effect_ids"] = list(goal.get("evidence_effect_ids", []))[-6:]
        goals.append(goal)
    autonomy["goals"] = goals
    compact["autonomy"] = autonomy
    return compact


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
        "agency": _compact_agency(result.get("agency", {})),
        "context": result["context"],
        "effect_law": "Operational effects use mcp__clayverse__request_effect and only verified EffectGate outcomes are operational truth. Durable goal changes use owner-scoped goal tools bound to an exact quote from the active user prompt; goal objective text is copied from the canonical user turn.",
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
        compact["agency"]["autonomy"]["goals"] = compact["agency"].get("autonomy", {}).get("goals", [])[:2]
        text = render()
    if len(text) > limit:
        raise TerminalHookError("canonical context exceeds safe inline hook envelope")
    return text


def user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        raise TerminalHookError("unexpected hook event")
    prompt = payload.get("prompt")
    claude_session_id = payload.get("session_id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise TerminalHookError("invalid user prompt")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")

    db, user_id, session_id, lifecycle = _runtime()
    try:
        with lifecycle.begin_admission(prompt, claude_session_id=claude_session_id) as result:
            enriched = dict(result)
            enriched["agency"] = AgencyView(db).snapshot(user_id=user_id)
            additional_context = _bounded_hook_context(enriched)
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
    message = payload.get("last_assistant_message")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")
    if not isinstance(message, str) or not message or len(message) > 200_000:
        raise TerminalHookError("invalid assistant response")
    db, _, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is None:
            raise TerminalHookError("no active canonical turn for Stop hook")
        if _active_claude_session(db, session_id) != claude_session_id:
            raise TerminalHookError("Stop belongs to a different Claude session")
        lifecycle.complete(message)
        return {"suppressOutput": True}
    finally:
        db.close()


def stop_failure(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "StopFailure":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return {"suppressOutput": True}
    db, _, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is not None and _active_claude_session(db, session_id) == claude_session_id:
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
            return 0
        return 2 if sys.argv[1] in {"user_prompt", "stop"} else 0


if __name__ == "__main__":
    raise SystemExit(_main())
