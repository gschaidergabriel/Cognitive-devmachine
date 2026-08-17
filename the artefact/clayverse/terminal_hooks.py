from __future__ import annotations

import json
import os
import sys
from typing import Any

from .autonomy import AutonomyController
from .autonomy_integration import admit_explicit_goal_from_turn, grounded_autonomy_context
from .identity import CANONICAL_USER_IDS, IdentityRouter
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle


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


def _compact_autonomy(autonomy: dict[str, Any]) -> None:
    goals = list(autonomy.get("goals", []))[:2]
    compact_goals: list[dict[str, Any]] = []
    for raw in goals:
        if not isinstance(raw, dict):
            continue
        goal = dict(raw)
        objective = str(goal.get("objective", ""))
        if len(objective) > 500:
            goal["objective"] = objective[:500] + "…"
        evidence = goal.get("evidence_effect_ids")
        if isinstance(evidence, list):
            goal["evidence_effect_ids"] = evidence[-8:]
        step = goal.get("current_step")
        if isinstance(step, dict):
            step = dict(step)
            description = str(step.get("description", ""))
            if len(description) > 300:
                step["description"] = description[:300] + "…"
            goal["current_step"] = step
        compact_goals.append(goal)
    autonomy["goals"] = compact_goals


def _minimal_autonomy(autonomy: dict[str, Any]) -> None:
    minimal = []
    for raw in list(autonomy.get("goals", []))[:2]:
        if not isinstance(raw, dict):
            continue
        step = raw.get("current_step") if isinstance(raw.get("current_step"), dict) else None
        minimal.append({
            "goal_id": raw.get("goal_id"),
            "status": raw.get("status"),
            "objective": str(raw.get("objective", ""))[:300],
            "priority": raw.get("priority"),
            "generation": raw.get("generation"),
            "budget": raw.get("budget"),
            "counters": raw.get("counters"),
            "completion_contract": raw.get("completion_contract"),
            "current_step": None if step is None else {
                "step_id": step.get("step_id"),
                "kind": step.get("kind"),
                "status": step.get("status"),
                "attempts": step.get("attempts"),
                "description": str(step.get("description", ""))[:180],
            },
            "blocked_reason": raw.get("blocked_reason"),
        })
    autonomy["goals"] = minimal


def _bounded_hook_context(
    result: dict[str, Any],
    autonomy: dict[str, Any] | None = None,
    limit: int = HOOK_CONTEXT_MAX_CHARS,
) -> str:
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
        "autonomy": autonomy or {
            "goals": [],
            "operating_mode": "goal-directed-proactive",
            "truth_boundary": {
                "identity_text_grants_capability": False,
                "model_proposal_is_execution": False,
                "effect_dispatch_is_success": False,
                "model_completion_is_goal_completion": False,
                "unknown_is_success": False,
            },
        },
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
    if isinstance(compact.get("autonomy"), dict):
        _compact_autonomy(compact["autonomy"])

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
        if isinstance(compact.get("autonomy"), dict):
            _minimal_autonomy(compact["autonomy"])
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
        controller = AutonomyController(db)
        # Canonical turn admission commits first. Only then can an explicit /goal turn
        # be adopted, so a failed prompt admission cannot create a durable objective.
        with lifecycle.begin_admission(prompt, claude_session_id=claude_session_id) as result:
            pass

        admit_explicit_goal_from_turn(
            controller,
            user_id=user_id,
            session_id=session_id,
            source_turn_id=result["turn_id"],
            prompt=prompt,
        )
        additional_context = _bounded_hook_context(
            result,
            autonomy=grounded_autonomy_context(controller, user_id=user_id),
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": additional_context,
            },
            "suppressOutput": True,
        }
    except Exception:
        # If a post-admission autonomy/context operation fails, close the active turn
        # explicitly rather than leaving a dangling causal episode. The exact user
        # turn remains canonical evidence; no effect or completion is synthesized.
        try:
            if lifecycle.active() is not None:
                lifecycle.abort("user_prompt_post_admission_failure")
        except Exception:
            pass
        raise
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
