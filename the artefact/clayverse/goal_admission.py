from __future__ import annotations

from dataclasses import dataclass

from .autonomy import AutonomyState


GOAL_COMMAND = "/goal "


@dataclass(frozen=True)
class GoalAdmission:
    goal_id: str
    step_id: str
    receipt_id: str
    objective: str
    source_turn_id: str


def explicit_goal_objective(prompt: str) -> str | None:
    """Return an explicitly user-marked persistent goal, never an inferred one."""
    if not isinstance(prompt, str):
        return None
    if not prompt.startswith(GOAL_COMMAND):
        return None
    objective = prompt[len(GOAL_COMMAND):].strip()
    return objective or None


def admit_explicit_user_goal(
    state: AutonomyState,
    *,
    user_id: str,
    source_turn_id: str,
    prompt: str,
) -> GoalAdmission | None:
    """Promote only an explicit user command into persistent autonomous goal state.

    The user's turn is already canonical when this function is called. The admission
    receipt proves where the goal came from, but is deliberately an OBSERVATION receipt
    so it cannot itself satisfy step-completion verification.
    """
    objective = explicit_goal_objective(prompt)
    if objective is None:
        return None
    goal_id = state.admit_goal(
        user_id,
        objective,
        success_contract={
            "kind": "trusted_verifier",
            "source_turn_id": source_turn_id,
            "model_self_completion_allowed": False,
            "unknown_is_success": False,
        },
        autonomous=True,
    )
    step_id = state.add_step(
        goal_id,
        objective,
        verification_contract={
            "kind": "trusted_verifier",
            "source_turn_id": source_turn_id,
            "requires_external_or_deterministic_evidence": True,
        },
    )
    receipt_id = state.record_receipt(
        goal_id,
        step_id,
        kind="OBSERVATION",
        source="explicit-user-goal-admission",
        verified=True,
        payload={
            "event": "goal_admitted",
            "source_turn_id": source_turn_id,
            "user_id": user_id,
            "objective": objective,
        },
        generation=state.db.entity_generation(),
    )
    return GoalAdmission(goal_id, step_id, receipt_id, objective, source_turn_id)
