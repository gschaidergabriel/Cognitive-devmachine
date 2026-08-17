from __future__ import annotations

from .autonomy import AutonomyState


def user_autonomy_context(state: AutonomyState, user_id: str, limit: int = 4) -> dict:
    """Bound model-visible goal state to the current authenticated perspective."""
    if user_id not in {"gabriel", "andreas"}:
        raise PermissionError("autonomy context requires a canonical user")
    rows = state.db.db.execute(
        "SELECT goal_id,creator_user_id,objective,priority,status,autonomous,attempt_budget,attempts_used "
        "FROM autonomy_goals WHERE creator_user_id=? AND status IN ('ACTIVE','PAUSED','BLOCKED') "
        "ORDER BY priority,created_at LIMIT ?",
        (user_id, int(limit)),
    ).fetchall()
    return {
        "entity_generation": state.db.entity_generation(),
        "identity_contract": {
            "entity": "ClayVerse",
            "state_authority": "UnifiedDB",
            "mode": "goal-directed-proactive",
            "perspective": user_id,
        },
        "active_goals": [dict(row) for row in rows],
        "truth_boundary": {
            "capability_claims": "must come from observed runtime capability state, never identity prose",
            "effect_success": "verified effect outcome only",
            "step_success": "trusted verification receipt only",
            "unknown": "remain UNKNOWN/BLOCKED",
            "cross_user_goals": "not injected by default; require separately admitted shared/collision context",
        },
    }


def autonomy_status_counts(state: AutonomyState) -> dict:
    """Non-sensitive process-status view; never emits objective/step text."""
    goal_rows = state.db.db.execute(
        "SELECT status,COUNT(*) AS n FROM autonomy_goals GROUP BY status ORDER BY status"
    ).fetchall()
    step_rows = state.db.db.execute(
        "SELECT status,COUNT(*) AS n FROM autonomy_steps GROUP BY status ORDER BY status"
    ).fetchall()
    return {
        "entity_generation": state.db.entity_generation(),
        "goal_counts": {row["status"]: int(row["n"]) for row in goal_rows},
        "step_counts": {row["status"]: int(row["n"]) for row in step_rows},
    }
