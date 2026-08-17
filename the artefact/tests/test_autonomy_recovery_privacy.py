from __future__ import annotations

from clayverse.autonomy import AutonomyState
from clayverse.autonomy_context import autonomy_status_counts, user_autonomy_context
from clayverse.autonomy_runtime import recover_autonomy_after_restart
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "terminal-gabriel")
    db.ensure_session("andreas", "terminal-andreas")
    return db


def _add_goal(state: AutonomyState, user_id: str, objective: str):
    goal_id = state.admit_goal(
        user_id,
        objective,
        success_contract={"kind": "trusted_verifier"},
    )
    step_id = state.add_step(
        goal_id,
        objective,
        verification_contract={"kind": "trusted_verifier"},
    )
    return goal_id, step_id


def test_user_context_does_not_inject_other_users_goal_text(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        gabriel_goal, _ = _add_goal(state, "gabriel", "gabriel private frontier")
        andreas_goal, _ = _add_goal(state, "andreas", "andreas private frontier")

        context = user_autonomy_context(state, "gabriel")
        ids = {item["goal_id"] for item in context["active_goals"]}
        text = repr(context)
        assert gabriel_goal in ids
        assert andreas_goal not in ids
        assert "gabriel private frontier" in text
        assert "andreas private frontier" not in text
    finally:
        db.close()


def test_process_status_counts_never_emit_goal_text(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        _add_goal(state, "gabriel", "sensitive objective text")
        status = autonomy_status_counts(state)
        assert status["goal_counts"]["ACTIVE"] == 1
        assert status["step_counts"]["PENDING"] == 1
        assert "sensitive objective text" not in repr(status)
    finally:
        db.close()


def test_restart_blocks_inflight_step_as_unknown_instead_of_replay(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _add_goal(state, "gabriel", "perform one bounded action")
        state.start_attempt(goal_id, step_id)
        assert state.step(step_id)["status"] == "RUNNING"

        db.advance_entity_generation()
        result = recover_autonomy_after_restart(state)

        assert result["running_blocked_unknown"] == 1
        assert result["generation"] == db.entity_generation()
        assert state.step(step_id)["status"] == "BLOCKED"
        assert state.goal(goal_id)["status"] == "BLOCKED"
        assert state.step(step_id)["last_error"] == "UNKNOWN_AFTER_RESTART:autonomy_step_interrupted"
        tick = db.db.execute(
            "SELECT trigger,action_state,reason,generation FROM autonomy_ticks WHERE step_id=? ORDER BY ts DESC LIMIT 1",
            (step_id,),
        ).fetchone()
        assert tick["trigger"] == "recovery"
        assert tick["action_state"] == "BLOCKED"
        assert "UNKNOWN_AFTER_RESTART" in tick["reason"]
        assert int(tick["generation"]) == db.entity_generation()
    finally:
        db.close()


def test_autonomy_state_changes_canonical_checkpoint_hash(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        _, before = db.checkpoint("before-autonomy-goal")
        _add_goal(state, "gabriel", "checkpoint-bound objective")
        _, after = db.checkpoint("after-autonomy-goal")
        assert before != after
    finally:
        db.close()
