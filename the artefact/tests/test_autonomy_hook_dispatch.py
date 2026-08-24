from __future__ import annotations

import hashlib
import json

import pytest

import clayverse.terminal_hooks as terminal_hooks
from clayverse.autonomy import AUTONOMY_TURN_SOURCE, AutonomyController
from clayverse.autonomy_dispatch import consume_dispatch_prompt, reserve_dispatch
from clayverse.autonomy_planner import DECISION_SCHEMA, AutonomyPlanner
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_hooks import (
    _active_claude_session,
    _active_turn_provenance,
    _admit_dispatch_turn,
    _finish_autonomous_stop,
    _bounded_hook_context,
)
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _goal(db):
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Advance this detached durable goal."
    )
    return controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )


def _reserve_planning(db):
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=prepared["step_id"],
        instruction=prepared["prompt"],
    )
    claimed = consume_dispatch_prompt(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        prompt=dispatch.terminal_prompt,
    )
    assert claimed is not None
    return goal, prepared, dispatch, claimed


def _hook_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    monkeypatch.setenv("CLAYVERSE_SESSION_ID", "session:gabriel")


def _reserve_existing_step(db, goal_id, step_id, instruction):
    return reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal_id,
        step_id=step_id,
        instruction=instruction,
    )


def test_dispatch_admission_records_system_instruction_not_terminal_nonce(db):
    goal, prepared, dispatch, claimed = _reserve_planning(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")

    result = _admit_dispatch_turn(db, lifecycle, claimed, "claude-session-A")

    row = db.db.execute(
        "SELECT role,content,provenance FROM turns WHERE turn_id=?", (result["turn_id"],)
    ).fetchone()
    assert row["role"] == "system"
    assert row["content"] == prepared["prompt"]
    assert dispatch.terminal_prompt not in row["content"]
    provenance = json.loads(row["provenance"])
    assert provenance["source"] == AUTONOMY_TURN_SOURCE
    assert provenance["goal_id"] == goal["goal_id"]
    assert provenance["autonomy_step_id"] == prepared["step_id"]
    assert provenance["claude_session_id"] == "claude-session-A"
    assert provenance["dispatch_transport"] == "one-shot-unifieddb-lease"
    assert provenance["dispatch_nonce_sha256"] == hashlib.sha256(dispatch.nonce.encode("ascii")).hexdigest()
    assert dispatch.nonce not in row["provenance"]
    assert _active_claude_session(db, "session:gabriel") == "claude-session-A"
    packed = _bounded_hook_context(result)
    assert '"terminal_prompt_is_authority":false' in packed

    user_turns = db.db.execute(
        "SELECT content FROM turns WHERE session_id='session:gabriel' AND role='user' ORDER BY ordinal"
    ).fetchall()
    assert [row["content"] for row in user_turns] == ["Advance this detached durable goal."]


def test_consumed_dispatch_pre_admission_failure_hits_existing_retry_budget(
    db, tmp_path, monkeypatch
):
    _hook_env(monkeypatch, tmp_path)
    goal = _goal(db)
    planner = AutonomyPlanner(db)
    prepared = planner.prepare_next("gabriel")

    def fail_before_admission(*_args, **_kwargs):
        raise RuntimeError("forced pre-admission failure")

    monkeypatch.setattr(terminal_hooks, "_admit_dispatch_turn", fail_before_admission)

    for expected_attempts in (1, 2, 3, 4):
        if expected_attempts > 1:
            prepared = planner.prepare_next("gabriel")
            assert prepared is not None
        dispatch = _reserve_existing_step(
            db,
            goal["goal_id"],
            prepared["step_id"],
            prepared["prompt"],
        )
        with pytest.raises(RuntimeError, match="forced pre-admission failure"):
            terminal_hooks.user_prompt(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": dispatch.terminal_prompt,
                    "session_id": f"claude-retry-{expected_attempts}",
                }
            )
        stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
        assert stored["current_step"]["step_id"] == prepared["step_id"]
        assert stored["current_step"]["attempts"] == expected_attempts
        assert stored["current_step"]["status"] == "FAILED"
        assert stored["blocked_reason"] == "autonomy_dispatch_admission_failure"
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0

    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["status"] == "BLOCKED"
    assert planner.prepare_next("gabriel") is None


def test_consumed_dispatch_post_admission_failure_aborts_turn_then_fails_step(
    db, tmp_path, monkeypatch
):
    _hook_env(monkeypatch, tmp_path)
    goal = _goal(db)
    prepared = AutonomyPlanner(db).prepare_next("gabriel")
    dispatch = _reserve_existing_step(
        db,
        goal["goal_id"],
        prepared["step_id"],
        prepared["prompt"],
    )

    def fail_context(_result):
        raise RuntimeError("forced post-admission context failure")

    monkeypatch.setattr(terminal_hooks, "_bounded_hook_context", fail_context)
    with pytest.raises(RuntimeError, match="forced post-admission context failure"):
        terminal_hooks.user_prompt(
            {
                "hook_event_name": "UserPromptSubmit",
                "prompt": dispatch.terminal_prompt,
                "session_id": "claude-post-admission",
            }
        )

    assert db.db.execute(
        "SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'"
    ).fetchone()[0] == 0
    autonomous = db.db.execute(
        "SELECT turn_id,provenance FROM turns WHERE session_id='session:gabriel' AND role='system' ORDER BY ordinal"
    ).fetchall()
    assert len(autonomous) == 2
    assert json.loads(autonomous[0]["provenance"])["source"] == AUTONOMY_TURN_SOURCE
    abort_provenance = json.loads(autonomous[1]["provenance"])
    assert abort_provenance["source"] == "clayverse-autonomy:goal-step:failure"
    assert abort_provenance["goal_id"] == goal["goal_id"]
    assert abort_provenance["autonomy_step_id"] == prepared["step_id"]
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["step_id"] == prepared["step_id"]
    assert stored["current_step"]["status"] == "FAILED"
    assert stored["blocked_reason"] == "autonomy_dispatch_admission_failure"
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_reason_stop_compiles_exactly_one_next_effect_step(db):
    goal, prepared, _dispatch, claimed = _reserve_planning(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    _admit_dispatch_turn(db, lifecycle, claimed, "claude-session-A")
    provenance = _active_turn_provenance(db, "session:gabriel")
    response = json.dumps(
        {
            "schema": DECISION_SCHEMA,
            "kind": "effect",
            "description": "execute bounded no-op",
            "effect": {"capability": "state.noop", "target": "hook-next", "argv": None},
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    finished = _finish_autonomous_stop(db, lifecycle, provenance, response)

    assert finished["goal_id"] == goal["goal_id"]
    next_step = finished["transition"]["next_step"]
    assert next_step["kind"] == "effect"
    assert next_step["status"] == "ADMITTED"
    assert next_step["effect"] == {
        "capability": "state.noop",
        "target": "hook-next",
        "argv": None,
    }
    assert lifecycle.active() is None
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["step_id"] == next_step["step_id"]
    assert stored["counters"]["steps"] == 2


def test_effect_stop_without_effect_tool_call_records_failure_not_success(db):
    controller = AutonomyController(db)
    goal = _goal(db)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "must actually dispatch",
        effect={"capability": "state.noop", "target": "missing-tool", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    dispatch = reserve_dispatch(
        db,
        user_id="gabriel",
        goal_id=goal["goal_id"],
        step_id=step["step_id"],
        instruction="Execute the admitted effect through the autonomy MCP tool.",
    )
    claimed = consume_dispatch_prompt(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        prompt=dispatch.terminal_prompt,
    )
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    _admit_dispatch_turn(db, lifecycle, claimed, "claude-session-B")
    provenance = _active_turn_provenance(db, "session:gabriel")

    finished = _finish_autonomous_stop(
        db,
        lifecycle,
        provenance,
        "I did not call the effect tool.",
    )

    assert finished["transition"]["status"] == "ACTIVE"
    stored = controller.snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["status"] == "FAILED"
    assert stored["blocked_reason"] == "autonomy_effect_not_dispatched_before_stop"
    assert stored["evidence_effect_ids"] == []
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0


def test_dispatch_transport_binding_rejects_second_bind(db):
    _goal_row, _prepared, _dispatch, claimed = _reserve_planning(db)
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    result = _admit_dispatch_turn(db, lifecycle, claimed, "claude-session-A")
    provenance = _active_turn_provenance(db, "session:gabriel")
    assert provenance["claude_session_id"] == "claude-session-A"
    assert result["autonomy_dispatch"]["source"] == "one-shot-unifieddb-lease"
