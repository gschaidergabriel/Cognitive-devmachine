from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any

from .autonomy import AUTONOMY_TURN_SOURCE, AutonomyController
from .autonomy_context import apply_explicit_goal_command, bounded_autonomy_context
from .autonomy_dispatch import AutonomyDispatch, consume_dispatch_prompt
from .autonomy_planner import AutonomyDecisionError, AutonomyPlanner
from .identity import CANONICAL_USER_IDS, IdentityRouter
from .store import UnifiedDB, resolve_db_path
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
    db = UnifiedDB(resolve_db_path(state_root))
    IdentityRouter(db, {})
    session_id = db.ensure_session(user_id, f"terminal-{user_id}")
    if expected_session and expected_session != session_id:
        db.close()
        raise TerminalHookError("terminal session identity mismatch")
    return db, user_id, session_id, TurnLifecycle(db, user_id, session_id, entityos_bridge=None)


def _active_turn_provenance(db: UnifiedDB, session_id: str) -> dict[str, Any] | None:
    row = db.db.execute(
        "SELECT t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id=?",
        (session_id,),
    ).fetchone()
    if not row:
        return None
    try:
        value = json.loads(row["provenance"])
    except Exception as exc:
        raise TerminalHookError("active turn provenance malformed") from exc
    if not isinstance(value, dict):
        raise TerminalHookError("active turn provenance must be an object")
    return value


def _active_claude_session(db: UnifiedDB, session_id: str) -> str | None:
    provenance = _active_turn_provenance(db, session_id)
    if provenance is None:
        return None
    value = provenance.get("claude_session_id")
    return value if isinstance(value, str) and value else None


def _bind_autonomy_transport_in_tx(
    db: UnifiedDB,
    *,
    turn_id: str,
    goal_id: str,
    step_id: str,
    claude_session_id: str,
    dispatch_nonce: str,
) -> None:
    """Bind the one-shot terminal transport to the autonomous observation atomically."""
    if not db.db.in_transaction:
        raise TerminalHookError("autonomy transport binding requires admission transaction")
    row = db.db.execute("SELECT provenance FROM turns WHERE turn_id=?", (turn_id,)).fetchone()
    if row is None:
        raise TerminalHookError("autonomous observation missing during transport bind")
    try:
        provenance = AutonomyController._loads(row["provenance"] or "{}")
    except Exception as exc:
        raise TerminalHookError("autonomous observation provenance malformed") from exc
    if (
        provenance.get("source") != AUTONOMY_TURN_SOURCE
        or provenance.get("goal_id") != goal_id
        or provenance.get("autonomy_step_id") != step_id
    ):
        raise TerminalHookError("autonomous observation identity drift during transport bind")
    if "claude_session_id" in provenance or "dispatch_nonce_sha256" in provenance:
        raise TerminalHookError("autonomous transport already bound")
    provenance["claude_session_id"] = claude_session_id
    provenance["dispatch_transport"] = "one-shot-unifieddb-lease"
    provenance["dispatch_nonce_sha256"] = hashlib.sha256(dispatch_nonce.encode("ascii")).hexdigest()
    updated = db.db.execute(
        "UPDATE turns SET provenance=? WHERE turn_id=?",
        (json.dumps(provenance, sort_keys=True), turn_id),
    )
    if updated.rowcount != 1:
        raise TerminalHookError("autonomous transport bind lost observation")


def _active_autonomy_preemption(db: UnifiedDB, session_id: str, user_id: str) -> dict[str, Any] | None:
    """Capture exact autonomous predecessor identity before a human prompt preempts it."""
    row = db.db.execute(
        "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,a.effect_id,t.provenance "
        "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
        "WHERE a.session_id=? AND a.user_id=?",
        (session_id, user_id),
    ).fetchone()
    if row is None:
        return None
    try:
        provenance = json.loads(row["provenance"])
    except Exception as exc:
        raise TerminalHookError("active turn provenance malformed before preemption") from exc
    if not isinstance(provenance, dict) or provenance.get("source") != AUTONOMY_TURN_SOURCE:
        return None
    goal_id = provenance.get("goal_id")
    step_id = provenance.get("autonomy_step_id")
    if not isinstance(goal_id, str) or not goal_id or not isinstance(step_id, str) or not step_id:
        raise TerminalHookError("autonomous predecessor identity missing")
    if provenance.get("causal_id") != row["causal_id"]:
        raise TerminalHookError("autonomous predecessor causal identity drift")
    try:
        entity_generation = int(provenance.get("entity_generation"))
        session_generation = int(provenance.get("session_generation"))
    except (TypeError, ValueError) as exc:
        raise TerminalHookError("autonomous predecessor generation provenance missing") from exc
    if entity_generation != int(row["generation"]) or session_generation != int(row["generation"]):
        raise TerminalHookError("autonomous predecessor generation drift")
    return {
        "goal_id": goal_id,
        "step_id": step_id,
        "turn_id": row["turn_id"],
        "episode_id": row["episode_id"],
        "causal_id": row["causal_id"],
        "generation": int(row["generation"]),
        "effect_id": row["effect_id"],
    }


def _reconcile_preempted_autonomy(db: UnifiedDB, user_id: str, captured: dict[str, Any] | None) -> dict[str, Any]:
    """Re-enter a preempted/failed goal step without replaying effects or inventing success."""
    if captured is None:
        return {"reconciled": False, "reason": "no_autonomous_predecessor"}
    controller = AutonomyController(db)
    snapshot = controller.snapshot(user_id=user_id)
    goal = next((item for item in snapshot["goals"] if item["goal_id"] == captured["goal_id"]), None)
    if goal is None:
        raise TerminalHookError("preempted autonomy goal disappeared")
    if int(goal["generation"]) != int(captured["generation"]):
        raise TerminalHookError("preempted autonomy goal generation changed")
    step = goal.get("current_step")
    if not isinstance(step, dict) or step.get("step_id") != captured["step_id"]:
        raise TerminalHookError("preempted autonomy step identity changed")
    if step.get("status") != "ADMITTED":
        return {
            "reconciled": False,
            "reason": "step_already_terminalized",
            "goal_id": captured["goal_id"],
            "step_id": captured["step_id"],
            "status": step.get("status"),
        }

    effects = db.db.execute(
        "SELECT effect_id,status FROM effects WHERE episode_id=? ORDER BY ts,effect_id",
        (captured["episode_id"],),
    ).fetchall()
    if len(effects) > 1:
        raise TerminalHookError("preempted autonomy episode has multiple effects")
    if effects:
        effect = effects[0]
        if effect["status"] == "PENDING":
            raise TerminalHookError("preempted autonomy effect is still pending")
        result = controller.record_effect_result(
            captured["goal_id"],
            captured["step_id"],
            effect["effect_id"],
            expected_generation=captured["generation"],
        )
        return {
            "reconciled": True,
            "mode": "final_effect_reentry",
            "goal_id": captured["goal_id"],
            "step_id": captured["step_id"],
            "effect_id": effect["effect_id"],
            "verified": bool(result["verified"]),
            "status": result["status"],
        }

    result = controller.record_step_failure(
        captured["goal_id"],
        captured["step_id"],
        "human_preempted_autonomy_step",
        expected_generation=captured["generation"],
    )
    return {
        "reconciled": True,
        "mode": "no_effect_requeue",
        "goal_id": captured["goal_id"],
        "step_id": captured["step_id"],
        "status": result["status"],
        "reason": result["reason"],
    }


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
        "autonomy": result.get("autonomy", {}),
        "autonomy_dispatch": result.get("autonomy_dispatch"),
        "autonomy_command": result.get("autonomy_command"),
        "effect_law": "Ordinary effects use mcp__clayverse__request_effect. An already-admitted autonomy effect step must use mcp__clayverse__request_autonomy_effect(goal_id,step_id), which dispatches only the stored canonical intent. Only verified EffectJournal outcomes are operational truth.",
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
    identity = context.get("canonical_identity")
    context["durable_memory"] = context.get("durable_memory", [])[:12]
    context["cross_session_collision"] = context.get("cross_session_collision", [])[:3]
    context["own_recent"] = context.get("own_recent", [])[-8:]
    if identity is not None:
        context["canonical_identity"] = identity
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


def _admit_dispatch_turn(
    db: UnifiedDB,
    lifecycle: TurnLifecycle,
    dispatch: AutonomyDispatch,
    claude_session_id: str,
) -> dict[str, Any]:
    with lifecycle.begin_autonomous_admission(
        dispatch.instruction,
        dispatch.goal_id,
        dispatch.step_id,
    ) as result:
        _bind_autonomy_transport_in_tx(
            db,
            turn_id=result["turn_id"],
            goal_id=dispatch.goal_id,
            step_id=dispatch.step_id,
            claude_session_id=claude_session_id,
            dispatch_nonce=dispatch.nonce,
        )
    result["autonomy"] = bounded_autonomy_context(db, dispatch.user_id)
    result["autonomy_dispatch"] = {
        "source": "one-shot-unifieddb-lease",
        "goal_id": dispatch.goal_id,
        "step_id": dispatch.step_id,
        "generation": dispatch.generation,
        "terminal_prompt_is_authority": False,
    }
    return result


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
        dispatch = consume_dispatch_prompt(
            db,
            user_id=user_id,
            session_id=session_id,
            prompt=prompt,
        )
        if dispatch is not None:
            try:
                result = _admit_dispatch_turn(db, lifecycle, dispatch, claude_session_id)
                additional_context = _bounded_hook_context(result)
            except Exception:
                active = lifecycle.active()
                if active is not None:
                    provenance = _active_turn_provenance(db, session_id) or {}
                    if (
                        provenance.get("source") == AUTONOMY_TURN_SOURCE
                        and provenance.get("goal_id") == dispatch.goal_id
                        and provenance.get("autonomy_step_id") == dispatch.step_id
                    ):
                        lifecycle.abort_autonomous(
                            "autonomy_dispatch_post_admission_failure",
                            dispatch.goal_id,
                            dispatch.step_id,
                        )
                raise
            return {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": additional_context,
                },
                "suppressOutput": True,
            }

        preempted = _active_autonomy_preemption(db, session_id, user_id)
        with lifecycle.begin_admission(prompt, claude_session_id=claude_session_id) as result:
            pass
        try:
            _reconcile_preempted_autonomy(db, user_id, preempted)
            result["autonomy_command"] = apply_explicit_goal_command(
                db,
                user_id=user_id,
                session_id=session_id,
                source_turn_id=result["turn_id"],
                prompt=prompt,
            )
            result["autonomy"] = bounded_autonomy_context(db, user_id)
            additional_context = _bounded_hook_context(result)
        except Exception:
            if lifecycle.active() is not None:
                lifecycle.abort("user_prompt_post_admission_failure")
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


def _finish_autonomous_stop(
    db: UnifiedDB,
    lifecycle: TurnLifecycle,
    provenance: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    goal_id = provenance.get("goal_id")
    step_id = provenance.get("autonomy_step_id")
    if not isinstance(goal_id, str) or not goal_id or not isinstance(step_id, str) or not step_id:
        raise TerminalHookError("autonomous Stop identity missing")
    try:
        generation = int(provenance.get("entity_generation"))
    except (TypeError, ValueError) as exc:
        raise TerminalHookError("autonomous Stop generation missing") from exc

    lifecycle_result = lifecycle.complete_autonomous(message, goal_id, step_id)
    controller = AutonomyController(db)
    snapshot = controller.snapshot(user_id=lifecycle.user_id)
    goal = next((item for item in snapshot["goals"] if item["goal_id"] == goal_id), None)
    if goal is None:
        raise TerminalHookError("autonomous goal missing after Stop")
    step = goal.get("current_step")
    if not isinstance(step, dict) or step.get("step_id") != step_id:
        raise TerminalHookError("autonomous step changed before Stop re-entry")

    transition: dict[str, Any] | None = None
    if step.get("kind") == "reason" and step.get("status") == "ADMITTED":
        transition = AutonomyPlanner(db).ingest_reason_response(
            goal_id,
            step_id,
            message,
            expected_generation=generation,
        )
    elif step.get("kind") == "effect" and step.get("status") == "ADMITTED":
        transition = controller.record_step_failure(
            goal_id,
            step_id,
            "autonomy_effect_not_dispatched_before_stop",
            expected_generation=generation,
        )
    elif step.get("kind") not in {"reason", "effect"}:
        raise TerminalHookError("autonomous Stop encountered unsupported step kind")

    return {
        "lifecycle": lifecycle_result,
        "transition": transition,
        "goal_id": goal_id,
        "step_id": step_id,
    }


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
        provenance = _active_turn_provenance(db, session_id) or {}
        if provenance.get("source") == AUTONOMY_TURN_SOURCE:
            _finish_autonomous_stop(db, lifecycle, provenance, message)
        else:
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
    db, user_id, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is not None and _active_claude_session(db, session_id) == claude_session_id:
            failure = str(payload.get("error", payload.get("error_type", "stop_failure")))[:500]
            provenance = _active_turn_provenance(db, session_id) or {}
            if provenance.get("source") == AUTONOMY_TURN_SOURCE:
                captured = _active_autonomy_preemption(db, session_id, user_id)
                if captured is None:
                    raise TerminalHookError("autonomous StopFailure lost predecessor identity")
                lifecycle.abort_autonomous(
                    "claude_autonomy_stop_failure:" + failure,
                    captured["goal_id"],
                    captured["step_id"],
                )
                _reconcile_preempted_autonomy(db, user_id, captured)
            else:
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
