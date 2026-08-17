from __future__ import annotations

import time

import pytest

from clayverse.autonomy import (
    STATE_KEY,
    AutonomyBudgetExceeded,
    AutonomyController,
    AutonomyStateError,
    CompletionNotVerified,
    GoalBudget,
)
from clayverse.effect_journal import EffectJournal
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _user_ack_goal(db, controller, *, objective="Finish the bounded task", priority=50, budget=None):
    source = db.append_turn("session:gabriel", "gabriel", "user", objective)
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
        priority=priority,
        budget=budget,
    )
    return source, goal


def _effect_goal(db, controller, *, objective="Finish the real bounded task", target="autonomy-target", budget=None):
    source = db.append_turn("session:gabriel", "gabriel", "user", objective)
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target=target,
        budget=budget,
    )
    return source, goal


class _FakeEntityOS:
    sha256 = "1" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0}


def _effect_through_turn(db, goal, step, *, target, argv, autonomous=True, resources=None):
    lifecycle = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_FakeEntityOS(),
    )
    refs = resources or [f"goal:{goal['goal_id']}", f"goal-step:{step['step_id']}"]
    if autonomous:
        lifecycle.begin_autonomous(
            f"Execute bounded autonomous effect for {target}",
            goal["goal_id"],
            step["step_id"],
            resources=refs,
        )
    else:
        lifecycle.begin(f"Interactive effect for {target}", resources=refs)
    result = lifecycle.request_effect("entityos.exec", target, argv)
    assert result["verified"] is True
    return result["effect_id"]


def _synthetic_effect(db, effect_id, *, target, argv, generation):
    target_receipt = EffectJournal._payload(EffectJournal._target_receipt(target))
    argv_receipt = EffectJournal._argv_receipt(argv)
    argv_payload = EffectJournal._payload(argv_receipt) if argv_receipt is not None else None
    outcome = EffectJournal._payload(EffectJournal._outcome_receipt({"ok": True, "exit": 0}))
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            None,
            "gabriel",
            "entityos.exec",
            target_receipt,
            argv_payload,
            generation,
            "VERIFIED",
            outcome,
            time.time(),
            time.time(),
        ),
    )


def test_goal_objective_is_copied_from_canonical_user_turn(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source, goal = _user_ack_goal(db, controller, objective="Exact owner objective")
    assert goal["objective"] == "Exact owner objective"
    assert goal["source_turn_id"] == source


def test_assistant_or_other_user_turn_cannot_mint_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    assistant = db.append_turn("session:gabriel", "gabriel", "assistant", "invented goal")
    other = db.append_turn("session:andreas", "andreas", "user", "other perspective")
    with pytest.raises(PermissionError):
        controller.create_goal_from_turn(
            "gabriel", "session:gabriel", assistant, completion_mode="user_ack"
        )
    with pytest.raises(PermissionError):
        controller.create_goal_from_turn(
            "gabriel", "session:gabriel", other, completion_mode="user_ack"
        )


def test_model_complete_candidate_is_not_goal_completion_evidence(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"], "complete_candidate", "I think the task is done"
    )
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "VERIFYING"
    assert snapshot["current_step"]["step_id"] == step["step_id"]


def test_state_noop_cannot_be_automatic_goal_completion_authority(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Perform a real bounded task")
    with pytest.raises(ValueError, match="cannot prove"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="verified_effect",
            required_capability="state.noop",
            required_target="noop-target",
        )


def test_legacy_v1_noop_contract_remains_readable_but_cannot_complete(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller)
    state = controller._loads(
        db.db.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()[0]
    )
    state["goals"][goal["goal_id"]]["completion_contract"] = {
        "mode": "verified_effect",
        "required_capability": "state.noop",
    }
    db.db.execute("UPDATE meta SET value=? WHERE key=?", (controller._dumps(state), STATE_KEY))
    assert controller.snapshot()["goals"][0]["goal_id"] == goal["goal_id"]
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_exact_autonomous_entityos_effect_completes_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="expected-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute exact completion contract",
        effect={
            "capability": "entityos.exec",
            "target": "expected-target",
            "argv": ["verify", "expected-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="expected-target",
        argv=["verify", "expected-target"],
    )
    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)
    assert result["verified"] is True
    assert result["completion_evidence"] is True
    done = controller.verify_completion(goal["goal_id"])
    assert done == {"goal_id": goal["goal_id"], "status": "COMPLETED", "evidence": effect_id}


def test_successful_intermediate_effect_cannot_complete_different_target_contract(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="required-final-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Run useful but non-final effect",
        effect={
            "capability": "entityos.exec",
            "target": "intermediate-target",
            "argv": ["verify", "intermediate-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="intermediate-target",
        argv=["verify", "intermediate-target"],
    )
    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)
    assert result["verified"] is True
    assert result["completion_evidence"] is False
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_same_capability_wrong_target_receipt_cannot_be_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="expected-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Verify only exact step intent",
        effect={
            "capability": "entityos.exec",
            "target": "expected-target",
            "argv": ["verify", "expected-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="different-target",
        argv=["verify", "different-target"],
    )
    with pytest.raises(PermissionError, match="intent mismatch"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)


def test_same_target_wrong_argv_receipt_cannot_be_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="entityos-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Verify exact argument identity",
        effect={
            "capability": "entityos.exec",
            "target": "entityos-target",
            "argv": ["operation", "expected"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="entityos-target",
        argv=["operation", "different"],
    )
    with pytest.raises(PermissionError, match="intent mismatch"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)


def test_synthetic_verified_effect_without_causal_episode_is_rejected(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="causal-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Require a real causal receipt",
        effect={
            "capability": "entityos.exec",
            "target": "causal-target",
            "argv": ["verify", "causal-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    _synthetic_effect(
        db,
        "synthetic-effect",
        target="causal-target",
        argv=["verify", "causal-target"],
        generation=db.entity_generation(),
    )
    with pytest.raises(PermissionError, match="causal binding"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "synthetic-effect")


def test_interactive_effect_with_exact_resources_cannot_masquerade_as_autonomous(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="shared-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Require autonomous provenance",
        effect={
            "capability": "entityos.exec",
            "target": "shared-target",
            "argv": ["verify", "shared-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="shared-target",
        argv=["verify", "shared-target"],
        autonomous=False,
    )
    with pytest.raises(PermissionError, match="autonomous goal-step provenance"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)


def test_causal_effect_from_other_goal_step_resources_is_rejected(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _effect_goal(db, controller, target="shared-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Do not borrow success from another goal step",
        effect={
            "capability": "entityos.exec",
            "target": "shared-target",
            "argv": ["verify", "shared-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _effect_through_turn(
        db,
        goal,
        step,
        target="shared-target",
        argv=["verify", "shared-target"],
        resources=["goal:other", "goal-step:other"],
    )
    with pytest.raises(PermissionError, match="different autonomous goal step"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)


def test_goal_source_turn_cannot_acknowledge_its_own_completion(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source, goal = _user_ack_goal(db, controller, objective="Prepare report")
    with pytest.raises(PermissionError, match="explicit later"):
        controller.acknowledge_by_user(goal["goal_id"], source)


def test_user_ack_requires_explicit_later_canonical_owner_turn(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller, objective="Prepare report")
    assistant = db.append_turn("session:gabriel", "gabriel", "assistant", "done")
    other = db.append_turn("session:andreas", "andreas", "user", "yes")
    owner = db.append_turn("session:gabriel", "gabriel", "user", "yes, this is complete")
    with pytest.raises(PermissionError):
        controller.acknowledge_by_user(goal["goal_id"], assistant)
    with pytest.raises(PermissionError):
        controller.acknowledge_by_user(goal["goal_id"], other)
    controller.acknowledge_by_user(goal["goal_id"], owner)
    assert controller.verify_completion(goal["goal_id"])["evidence"] == owner


def test_process_exec_is_denied_at_proposal_boundary(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller)
    with pytest.raises(PermissionError):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "bypass",
            effect={"capability": "process.exec", "target": "host", "argv": ["id"]},
        )


def test_reasoning_remains_runnable_when_effect_budget_is_zero(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(
        db,
        controller,
        budget=GoalBudget(max_steps=2, max_retries_per_step=0, max_effects=0),
    )
    step = controller.propose_step(goal["goal_id"], "reason", "Reason without effect authority")
    controller.admit_step(goal["goal_id"], step["step_id"])
    controller.record_reason_success(goal["goal_id"], step["step_id"])
    with pytest.raises(AutonomyBudgetExceeded, match="effect budget exhausted"):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "Effect remains forbidden",
            effect={"capability": "state.noop", "target": "x", "argv": None},
        )


def test_retry_budget_blocks_runaway_loop(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(
        db,
        controller,
        budget=GoalBudget(max_steps=2, max_retries_per_step=0, max_effects=0),
    )
    step = controller.propose_step(goal["goal_id"], "reason", "Try once")
    controller.admit_step(goal["goal_id"], step["step_id"])
    result = controller.record_step_failure(goal["goal_id"], step["step_id"], "failed")
    assert result["status"] == "BLOCKED"
    with pytest.raises(AutonomyStateError):
        controller.propose_step(goal["goal_id"], "reason", "silent infinite retry")


def test_global_generation_advance_fences_stale_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller)
    db.advance_entity_generation()
    with pytest.raises(StaleGeneration):
        controller.propose_step(goal["goal_id"], "reason", "stale continuation")
    assert controller.next_runnable(user_id="gabriel") is None


def test_state_persists_and_duplicate_json_fails_closed(tmp_path):
    path = tmp_path / "state.db"
    db = UnifiedDB(path)
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    controller = AutonomyController(db)
    _, goal = _user_ack_goal(db, controller)
    db.close()

    reopened = UnifiedDB(path)
    again = AutonomyController(reopened)
    assert again.snapshot(user_id="gabriel")["goals"][0]["goal_id"] == goal["goal_id"]
    reopened.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        ('{"schema":"ClayVerseAutonomyState/v1","schema":"evil"}',),
    )
    with pytest.raises(AutonomyStateError):
        again.snapshot()


def test_nonfinite_state_fails_closed(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _user_ack_goal(db, controller)
    db.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        ('{"schema":"ClayVerseAutonomyState/v1","revision":NaN,"goals":{},"queue":[]}',),
    )
    with pytest.raises(AutonomyStateError):
        controller.snapshot()


def test_priority_scheduler_selects_only_live_active_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    _, low = _user_ack_goal(db, controller, objective="low", priority=10)
    _, high = _user_ack_goal(db, controller, objective="high", priority=90)
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == high["goal_id"]
    controller.block_goal(high["goal_id"], "dependency")
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == low["goal_id"]