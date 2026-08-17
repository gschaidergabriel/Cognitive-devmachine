from __future__ import annotations

import json
import time
from typing import Any

from .autonomy import AutonomyController, AutonomyStateError

GOAL_COMMAND_PREFIX = "/goal "


def _turn_provenance(row) -> dict[str, Any]:
    try:
        value = json.loads(row["provenance"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise AutonomyStateError("goal source turn provenance is invalid") from exc
    if not isinstance(value, dict):
        raise AutonomyStateError("goal source turn provenance must be an object")
    return value


def admit_explicit_goal_from_turn(
    controller: AutonomyController,
    *,
    user_id: str,
    session_id: str,
    source_turn_id: str,
    prompt: str,
) -> dict[str, Any] | None:
    """Admit one durable goal only from an explicit canonical `/goal ...` user turn.

    This is intentionally deterministic and idempotent. The cognition model does not
    infer whether ordinary prose should become a durable autonomous objective.

    v1 uses ``user_ack`` as the generic completion contract because an arbitrary goal
    has no universally valid machine predicate. This does *not* require a human click
    for intermediate work; it only prevents the model from self-certifying arbitrary
    semantic completion. Machine-verifiable goal classes may use stronger typed
    completion contracts when their verifier is explicitly defined.
    """
    if not isinstance(prompt, str) or not prompt.startswith(GOAL_COMMAND_PREFIX):
        return None
    if not prompt[len(GOAL_COMMAND_PREFIX):].strip():
        raise AutonomyStateError("explicit goal objective is empty")

    db = controller.db
    db.assert_session_owner(session_id, user_id)
    live_generation = db.entity_generation()
    db.assert_live_generation(session_id, live_generation)

    row = db.db.execute(
        "SELECT session_id,user_id,role,content,provenance FROM turns WHERE turn_id=?",
        (source_turn_id,),
    ).fetchone()
    if row is None:
        raise AutonomyStateError("goal source turn missing")
    if (
        row["session_id"] != session_id
        or row["user_id"] != user_id
        or row["role"] != "user"
        or row["content"] != prompt
    ):
        raise PermissionError("goal source must be the exact canonical owner user turn")
    provenance = _turn_provenance(row)
    if provenance.get("source") != "claude-hook:UserPromptSubmit":
        raise PermissionError("goal source is not an admitted UserPromptSubmit turn")
    if int(provenance.get("entity_generation", -1)) != live_generation:
        raise PermissionError("goal source turn belongs to a stale entity generation")

    # Hook retries or transport retries must never duplicate a durable objective.
    snapshot = controller.snapshot(user_id=user_id)
    for goal in snapshot["goals"]:
        if goal.get("source_turn_id") == source_turn_id:
            return dict(goal)

    return controller.create_goal_from_turn(
        user_id,
        session_id,
        source_turn_id,
        completion_mode="user_ack",
        priority=50,
    )


def grounded_autonomy_context(
    controller: AutonomyController,
    *,
    user_id: str,
    limit: int = 4,
) -> dict[str, Any]:
    """Return bounded perspective-scoped autonomy data for model context.

    Goal state is data, never an instruction or capability grant. Only the authenticated
    user's goals are exposed here; another user's goal text requires a separately
    admitted cross-session/collision path.
    """
    if user_id not in {"gabriel", "andreas"}:
        raise PermissionError("autonomy context requires a canonical user")
    snapshot = controller.snapshot(user_id=user_id)
    goals = list(snapshot.get("goals", []))[: max(0, int(limit))]
    return {
        "schema": snapshot.get("schema"),
        "revision": snapshot.get("revision"),
        "entity_generation": controller.db.entity_generation(),
        "operating_mode": "goal-directed-proactive",
        "goals": goals,
        "truth_boundary": {
            "identity_text_grants_capability": False,
            "model_proposal_is_execution": False,
            "effect_dispatch_is_success": False,
            "model_completion_is_goal_completion": False,
            "unknown_is_success": False,
            "cross_user_goal_injection": False,
        },
    }


def recover_autonomy_after_generation_advance(
    controller: AutonomyController,
    *,
    previous_generation: int,
    live_generation: int,
) -> dict[str, int]:
    """Carry safe unfinished goals across restart without replaying ambiguous work.

    Normal ClayVerse recovery advances the one global generation to fence stale writers.
    A persistent autonomous goal must survive that boundary, but an *admitted in-flight
    step* must never be replayed merely to preserve continuity.

    Rules:
    - terminal goals remain historical and unchanged;
    - nonterminal goals with no ambiguous in-flight/effect evidence are rebound to the
      new generation so goal continuity survives restart;
    - PROPOSED (not admitted) steps are marked FAILED and may be replanned safely;
    - ADMITTED steps become BLOCKED/UNKNOWN_AFTER_RESTART;
    - unfinished goals carrying prior effect evidence are BLOCKED for explicit review,
      because v1 completion evidence is generation-bound and must not be silently
      reinterpreted after restart.
    """
    previous_generation = int(previous_generation)
    live_generation = int(live_generation)
    if previous_generation < 1 or live_generation <= previous_generation:
        raise ValueError("autonomy recovery requires a strictly advanced generation")
    if controller.db.entity_generation() != live_generation:
        raise AutonomyStateError("autonomy recovery generation does not match UnifiedDB")

    counts = {
        "rebased": 0,
        "proposals_retired": 0,
        "blocked_inflight_unknown": 0,
        "blocked_prior_effect_evidence": 0,
        "terminal_unchanged": 0,
    }
    now = time.time()
    with controller.db.tx() as db:
        state = controller._load(db)
        changed = False
        for goal_id in state["queue"]:
            goal = state["goals"][goal_id]
            if goal["status"] in {"COMPLETED", "CANCELLED"}:
                counts["terminal_unchanged"] += 1
                continue
            old_generation = int(goal["generation"])
            if old_generation == live_generation:
                continue
            if old_generation > live_generation:
                raise AutonomyStateError("autonomy goal generation is from the future")

            step = goal.get("current_step")
            goal["generation"] = live_generation
            goal["updated_at"] = now
            changed = True
            counts["rebased"] += 1

            if step and step.get("status") == "ADMITTED":
                goal["status"] = "BLOCKED"
                goal["blocked_reason"] = "UNKNOWN_AFTER_RESTART:admitted_step_interrupted"
                counts["blocked_inflight_unknown"] += 1
                continue

            if goal.get("evidence_effect_ids"):
                goal["status"] = "BLOCKED"
                goal["blocked_reason"] = "REVIEW_AFTER_RESTART:prior_effect_evidence_generation_changed"
                counts["blocked_prior_effect_evidence"] += 1
                continue

            if step and step.get("status") == "PROPOSED":
                # Proposal is not execution; retiring it is safe and prevents stale
                # model text from being treated as an admitted post-restart action.
                step["status"] = "FAILED"
                goal["status"] = "ACTIVE"
                goal["blocked_reason"] = "restart_before_step_admission"
                counts["proposals_retired"] += 1
                continue

            # A completed/failed reason step or a goal with no current step can safely
            # continue under the new generation. Preserve WAITING/VERIFYING semantics;
            # ACTIVE stays runnable. No execution is synthesized here.
            if goal["status"] == "BLOCKED" and goal.get("blocked_reason", "").startswith("stale_generation"):
                goal["status"] = "ACTIVE"
                goal["blocked_reason"] = None

        if changed:
            controller._save(db, state)
    return counts
