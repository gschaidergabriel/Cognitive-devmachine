from __future__ import annotations

import json
import uuid
from typing import Any

from .autonomy import AutonomyController, AutonomyStateError
from .identity import CANONICAL_USER_IDS
from .store import UnifiedDB

AUTONOMY_CONTEXT_SCHEMA = "ClayVerseAutonomyContext/v2"
AUTONOMY_CONTEXT_MAX_CHARS = 2_500
AUTONOMY_CONTEXT_MAX_GOALS = 4
GOAL_COMMAND_PREFIX = "/goal "
GOAL_ACK_PREFIX = "/goal-ack "
GOAL_CANCEL_PREFIX = "/goal-cancel "
_ATTENTION_STATUSES = {"ACTIVE", "WAITING", "VERIFYING", "BLOCKED"}
_SAFE_BLOCK_REASONS = {
    "retry_budget_exhausted",
    "step_failed",
    "unknown_effect_after_generation_change",
    "effect_evidence_requires_generation_rebind",
    "recovered_interrupted_no_effect_step",
    "human_preempted_autonomy_step",
    "autonomy_effect_not_dispatched_before_stop",
    "invalid_autonomy_planner_decision",
}


class AutonomyContextError(RuntimeError):
    pass


def _clip(value: Any, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1] + "…"


def _blocked_reason_class(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text in _SAFE_BLOCK_REASONS:
        return text
    if text.startswith("effect_"):
        return "effect_not_verified"
    return "opaque"


def _snapshot(db: UnifiedDB, user_id: str) -> dict[str, Any]:
    """Read goal state and live generation from one UnifiedDB transaction."""
    if not db.db.in_transaction:
        with db.tx():
            return _snapshot(db, user_id)

    controller = AutonomyController(db)
    state = controller._load(db.db)
    goals = [
        state["goals"][goal_id]
        for goal_id in state["queue"]
        if state["goals"][goal_id]["user_id"] == user_id
    ]
    return {
        "schema": state["schema"],
        "revision": state["revision"],
        "generation": db.entity_generation(),
        "goals": goals,
    }


def _canonical_command_turn(
    db: UnifiedDB,
    *,
    user_id: str,
    session_id: str,
    source_turn_id: str,
    prompt: str,
):
    if user_id not in CANONICAL_USER_IDS or session_id != f"session:{user_id}":
        raise PermissionError("autonomy command requires canonical owner session")
    db.assert_session_owner(session_id, user_id)
    live_generation = db.entity_generation()
    db.assert_live_generation(session_id, live_generation)
    row = db.db.execute(
        "SELECT session_id,user_id,role,content,provenance FROM turns WHERE turn_id=?",
        (source_turn_id,),
    ).fetchone()
    if row is None:
        raise AutonomyStateError("autonomy command source turn missing")
    if (
        row["session_id"] != session_id
        or row["user_id"] != user_id
        or row["role"] != "user"
        or row["content"] != prompt
    ):
        raise PermissionError("autonomy command source must be exact canonical owner user turn")
    provenance = AutonomyController._loads(row["provenance"] or "{}")
    try:
        entity_generation = int(provenance.get("entity_generation"))
        session_generation = int(provenance.get("session_generation"))
    except (TypeError, ValueError) as exc:
        raise PermissionError("autonomy command generation provenance missing") from exc
    if (
        provenance.get("source") != "claude-hook:UserPromptSubmit"
        or entity_generation != live_generation
        or session_generation != live_generation
    ):
        raise PermissionError("autonomy command is not a live admitted UserPromptSubmit turn")
    return row, live_generation


def _goal_id_from_command(prompt: str, prefix: str) -> str:
    raw = prompt[len(prefix) :].strip()
    if not raw or any(char.isspace() for char in raw) or "\x00" in raw:
        raise AutonomyStateError("goal command requires exactly one goal id")
    try:
        parsed = uuid.UUID(raw)
    except (ValueError, AttributeError) as exc:
        raise AutonomyStateError("goal command id is not canonical UUID") from exc
    canonical = str(parsed)
    if canonical != raw.lower():
        raise AutonomyStateError("goal command id is not canonical UUID text")
    return canonical


def apply_explicit_goal_command(
    db: UnifiedDB,
    *,
    user_id: str,
    session_id: str,
    source_turn_id: str,
    prompt: str,
) -> dict[str, Any] | None:
    """Apply only exact typed goal create/ack/cancel commands from the live user turn."""
    if not isinstance(prompt, str):
        return None
    if prompt.startswith(GOAL_COMMAND_PREFIX):
        goal = admit_explicit_goal_from_turn(
            db,
            user_id=user_id,
            session_id=session_id,
            source_turn_id=source_turn_id,
            prompt=prompt,
        )
        return {"command": "create", "goal": goal}
    if not (prompt.startswith(GOAL_ACK_PREFIX) or prompt.startswith(GOAL_CANCEL_PREFIX)):
        return None

    _canonical_command_turn(
        db,
        user_id=user_id,
        session_id=session_id,
        source_turn_id=source_turn_id,
        prompt=prompt,
    )
    controller = AutonomyController(db)
    owned = {
        goal["goal_id"]: goal for goal in controller.snapshot(user_id=user_id)["goals"]
    }

    if prompt.startswith(GOAL_ACK_PREFIX):
        goal_id = _goal_id_from_command(prompt, GOAL_ACK_PREFIX)
        goal = owned.get(goal_id)
        if goal is None:
            raise PermissionError("goal acknowledgement target is not owned by current user")
        contract = goal.get("completion_contract")
        if not isinstance(contract, dict) or contract.get("mode") != "user_ack":
            raise AutonomyStateError("goal does not admit user acknowledgement completion")
        controller.acknowledge_by_user(goal_id, source_turn_id)
        completed = controller.verify_completion(goal_id)
        return {"command": "ack", "goal_id": goal_id, "result": completed}

    goal_id = _goal_id_from_command(prompt, GOAL_CANCEL_PREFIX)
    if goal_id not in owned:
        raise PermissionError("goal cancellation target is not owned by current user")
    cancelled = controller.cancel_goal(goal_id)
    return {"command": "cancel", "goal_id": goal_id, "result": cancelled}


def admit_explicit_goal_from_turn(
    db: UnifiedDB,
    *,
    user_id: str,
    session_id: str,
    source_turn_id: str,
    prompt: str,
) -> dict[str, Any] | None:
    """Admit `/goal ...` only from its exact live canonical UserPromptSubmit turn.

    Ordinary prose is never inferred into a durable goal. Sequential hook/transport
    replay is deduplicated by source turn. Generic natural-language goals use user_ack
    completion because model text is not an independent semantic completion verifier.
    """
    if not isinstance(prompt, str) or not prompt.startswith(GOAL_COMMAND_PREFIX):
        return None
    if not prompt[len(GOAL_COMMAND_PREFIX):].strip():
        raise AutonomyStateError("explicit goal objective is empty")
    _canonical_command_turn(
        db,
        user_id=user_id,
        session_id=session_id,
        source_turn_id=source_turn_id,
        prompt=prompt,
    )

    controller = AutonomyController(db)
    for goal in controller.snapshot(user_id=user_id)["goals"]:
        if goal.get("source_turn_id") == source_turn_id:
            return dict(goal)

    return controller.create_goal_from_turn(
        user_id,
        session_id,
        source_turn_id,
        completion_mode="user_ack",
        priority=50,
    )


def _is_runnable(goal: dict[str, Any]) -> bool:
    if goal.get("status") != "ACTIVE":
        return False
    counters = goal.get("counters")
    budget = goal.get("budget")
    if not isinstance(counters, dict) or not isinstance(budget, dict):
        return False
    if int(counters.get("steps", 0)) >= int(budget.get("max_steps", 0)):
        return False
    step = goal.get("current_step")
    return not (isinstance(step, dict) and step.get("status") in {"PROPOSED", "ADMITTED"})


def _select_attention(
    attention: list[dict[str, Any]],
    included: int,
    runnable: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if included <= 0:
        return []
    selected = list(attention[:included])
    if runnable is not None and all(goal.get("goal_id") != runnable.get("goal_id") for goal in selected):
        selected[-1] = runnable
    return selected


def _goal_view(goal: dict[str, Any], text_limit: int) -> dict[str, Any]:
    step = goal.get("current_step")
    step_view = None
    if isinstance(step, dict):
        step_view = {
            "step_id": step.get("step_id"),
            "kind": step.get("kind"),
            "status": step.get("status"),
            "attempts": step.get("attempts"),
            "description": _clip(step.get("description"), text_limit),
        }
        effect = step.get("effect")
        if isinstance(effect, dict):
            step_view["effect_capability"] = effect.get("capability")

    contract = goal.get("completion_contract")
    contract_view = None
    if isinstance(contract, dict):
        contract_view = {
            "mode": contract.get("mode"),
            "required_capability": contract.get("required_capability"),
        }

    evidence = goal.get("evidence_effect_ids")
    evidence_count = len(evidence) if isinstance(evidence, list) else 0
    return {
        "goal_id": goal.get("goal_id"),
        "source_turn_id": goal.get("source_turn_id"),
        "generation": goal.get("generation"),
        "priority": goal.get("priority"),
        "status": goal.get("status"),
        "objective": _clip(goal.get("objective"), text_limit),
        "completion_contract": contract_view,
        "budget": goal.get("budget"),
        "counters": goal.get("counters"),
        "current_step": step_view,
        "evidence_count": evidence_count,
        "blocked_reason_class": _blocked_reason_class(goal.get("blocked_reason")),
    }


def bounded_autonomy_context(
    db: UnifiedDB,
    user_id: str,
    *,
    max_chars: int = AUTONOMY_CONTEXT_MAX_CHARS,
    max_goals: int = AUTONOMY_CONTEXT_MAX_GOALS,
) -> dict[str, Any]:
    """Project user-scoped live-generation goal state into a prompt-safe view.

    This changes accessibility only. It does not create goals, schedule work, grant
    capabilities, execute effects, or treat model output as completion evidence.
    """
    if user_id not in CANONICAL_USER_IDS:
        raise PermissionError("autonomy context requires a canonical user")
    if not isinstance(max_chars, int) or max_chars < 512:
        raise ValueError("autonomy context max_chars is too small")
    if not isinstance(max_goals, int) or not 0 <= max_goals <= 32:
        raise ValueError("autonomy context max_goals out of range")

    snapshot = _snapshot(db, user_id)
    live_generation = int(snapshot["generation"])
    attention_all = [goal for goal in snapshot["goals"] if goal.get("status") in _ATTENTION_STATUSES]
    stale_attention = [goal for goal in attention_all if int(goal.get("generation", -1)) != live_generation]
    attention = [goal for goal in attention_all if int(goal.get("generation", -1)) == live_generation]
    runnable = next((goal for goal in attention if _is_runnable(goal)), None)
    runnable_id = runnable.get("goal_id") if runnable is not None else None
    goal_cap = min(max_goals, len(attention))

    for included in range(goal_cap, -1, -1):
        selected = _select_attention(attention, included, runnable)
        selected_ids = {goal.get("goal_id") for goal in selected}
        runnable_visible = runnable_id is not None and runnable_id in selected_ids
        for text_limit in (640, 400, 240, 140, 80):
            view = {
                "schema": AUTONOMY_CONTEXT_SCHEMA,
                "authority": "UnifiedDB",
                "source_schema": snapshot["schema"],
                "source_revision": snapshot["revision"],
                "user_id": user_id,
                "live_generation": live_generation,
                "model_authority": "PROPOSAL_ONLY",
                "completion_authority": "AutonomyController canonical evidence only",
                "effect_authority": "EffectGate/EffectJournal only",
                "attention_goal_count": len(attention),
                "stale_attention_goal_count": len(stale_attention),
                "included_goal_count": len(selected),
                "omitted_goal_count": len(attention) - len(selected),
                "next_runnable_goal_id": runnable_id if runnable_visible else None,
                "next_runnable_omitted_by_context_budget": bool(runnable_id is not None and not runnable_visible),
                "goals": [_goal_view(goal, text_limit) for goal in selected],
            }
            encoded = json.dumps(
                view,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
                default=str,
            )
            if len(encoded) <= max_chars:
                return view

    raise AutonomyContextError("canonical autonomy context cannot fit bounded envelope")
