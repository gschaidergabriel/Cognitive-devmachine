from __future__ import annotations

import json
from typing import Any

from .autonomy import AutonomyController
from .identity import CANONICAL_USER_IDS
from .store import UnifiedDB

AUTONOMY_CONTEXT_SCHEMA = "ClayVerseAutonomyContext/v1"
AUTONOMY_CONTEXT_MAX_CHARS = 2_500
AUTONOMY_CONTEXT_MAX_GOALS = 4
_ATTENTION_STATUSES = {"ACTIVE", "WAITING", "VERIFYING", "BLOCKED"}


class AutonomyContextError(RuntimeError):
    pass


def _clip(value: Any, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    return text[: limit - 1] + "…"


def _snapshot(db: UnifiedDB, user_id: str) -> dict[str, Any]:
    """Read canonical autonomy state without opening a nested transaction."""
    controller = AutonomyController(db)
    if db.db.in_transaction:
        state = controller._load(db.db)
        goals = [
            state["goals"][goal_id]
            for goal_id in state["queue"]
            if state["goals"][goal_id]["user_id"] == user_id
        ]
        return {"schema": state["schema"], "revision": state["revision"], "goals": goals}
    return controller.snapshot(user_id=user_id)


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
            # Capability is useful routing state. Raw target/argv remain behind the
            # canonical EffectGate/EffectJournal boundary and are not prompt material.
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
        "blocked_reason": _clip(goal.get("blocked_reason"), min(text_limit, 240)) if goal.get("blocked_reason") else None,
    }


def bounded_autonomy_context(
    db: UnifiedDB,
    user_id: str,
    *,
    max_chars: int = AUTONOMY_CONTEXT_MAX_CHARS,
    max_goals: int = AUTONOMY_CONTEXT_MAX_GOALS,
) -> dict[str, Any]:
    """Project user-scoped canonical goal state into a deterministic prompt-safe view.

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
    attention = [goal for goal in snapshot["goals"] if goal.get("status") in _ATTENTION_STATUSES]
    goal_cap = min(max_goals, len(attention))

    for included in range(goal_cap, -1, -1):
        for text_limit in (640, 400, 240, 140, 80):
            view = {
                "schema": AUTONOMY_CONTEXT_SCHEMA,
                "authority": "UnifiedDB",
                "source_schema": snapshot["schema"],
                "source_revision": snapshot["revision"],
                "user_id": user_id,
                "model_authority": "PROPOSAL_ONLY",
                "completion_authority": "AutonomyController canonical evidence only",
                "effect_authority": "EffectGate/EffectJournal only",
                "attention_goal_count": len(attention),
                "included_goal_count": included,
                "omitted_goal_count": len(attention) - included,
                "goals": [_goal_view(goal, text_limit) for goal in attention[:included]],
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
