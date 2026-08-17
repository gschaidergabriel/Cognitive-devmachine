from __future__ import annotations

import hashlib
import json
import time
import uuid
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
    if not isinstance(prompt, str) or not prompt.startswith(GOAL_COMMAND):
        return None
    objective = prompt[len(GOAL_COMMAND):].strip()
    return objective or None


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def admit_explicit_user_goal(
    state: AutonomyState,
    *,
    user_id: str,
    source_turn_id: str,
    prompt: str,
) -> GoalAdmission | None:
    """Atomically promote only explicit user intent into autonomous persistent state.

    Goal, first step and source receipt are one transaction in the same UnifiedDB.
    The source receipt is OBSERVATION, not completion evidence, so merely asking for
    a goal can never prove that the goal was achieved.
    """
    objective = explicit_goal_objective(prompt)
    if objective is None:
        return None
    if len(objective) > state.policy.max_objective_chars:
        raise ValueError("goal objective is oversized")

    db = state.db
    generation = db.entity_generation()
    now = time.time()
    goal_id = str(uuid.uuid4())
    step_id = str(uuid.uuid4())
    receipt_id = str(uuid.uuid4())
    success_contract = {
        "kind": "trusted_verifier",
        "source_turn_id": source_turn_id,
        "model_self_completion_allowed": False,
        "unknown_is_success": False,
    }
    verification_contract = {
        "kind": "trusted_verifier",
        "source_turn_id": source_turn_id,
        "requires_external_or_deterministic_evidence": True,
    }
    receipt_payload = {
        "event": "goal_admitted",
        "source_turn_id": source_turn_id,
        "user_id": user_id,
        "objective": objective,
    }
    receipt_json = _canonical_json(receipt_payload)
    receipt_hash = hashlib.sha256(receipt_json.encode("utf-8")).hexdigest()

    with db.tx() as conn:
        user = conn.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone()
        turn = conn.execute(
            "SELECT 1 FROM turns WHERE turn_id=? AND user_id=? AND role='user'",
            (source_turn_id, user_id),
        ).fetchone()
        if not user or not turn:
            raise PermissionError("goal admission source is not a canonical user turn")
        if generation != db.entity_generation():
            raise RuntimeError("entity generation changed during goal admission")
        conn.execute(
            "INSERT INTO autonomy_goals(goal_id,creator_user_id,objective,success_contract,priority,status,autonomous,attempt_budget,attempts_used,created_generation,created_at,updated_at) VALUES(?,?,?,?,100,'ACTIVE',1,?,0,?,?,?)",
            (
                goal_id,
                user_id,
                objective,
                _canonical_json(success_contract),
                state.policy.max_goal_attempt_budget,
                generation,
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO autonomy_steps(step_id,goal_id,ordinal,description,verification_contract,status,max_attempts,attempts_used,repeated_failures,created_at,updated_at) VALUES(?,?,1,?,?,'PENDING',?,0,0,?,?)",
            (
                step_id,
                goal_id,
                objective,
                _canonical_json(verification_contract),
                state.policy.default_step_max_attempts,
                now,
                now,
            ),
        )
        conn.execute(
            "INSERT INTO autonomy_receipts(receipt_id,goal_id,step_id,generation,kind,source,verified,payload,payload_hash,ts) VALUES(?,?,?,?, 'OBSERVATION','explicit-user-goal-admission',1,?,?,?)",
            (
                receipt_id,
                goal_id,
                step_id,
                generation,
                receipt_json,
                receipt_hash,
                now,
            ),
        )
        conn.execute(
            "UPDATE autonomy_steps SET last_receipt_id=? WHERE step_id=?",
            (receipt_id, step_id),
        )

    return GoalAdmission(goal_id, step_id, receipt_id, objective, source_turn_id)
