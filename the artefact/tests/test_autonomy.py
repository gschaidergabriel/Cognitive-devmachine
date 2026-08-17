from __future__ import annotations

import time

import pytest

from clayverse.autonomy import (
    AutonomyBudgetExceeded,
    AutonomyController,
    AutonomyStateError,
    CompletionNotVerified,
    GoalBudget,
)
from clayverse.effect_journal import EffectJournal
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _FakeEntityOS:
    sha256 = "a" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "argv": list(argv or [])}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal(db, controller, *, objective="Finish the bounded task", **kwargs):
    turn_id = db.append_turn("session:gabriel", "gabriel", "user", objective)
    completion_mode = kwargs.pop("completion_mode", "user_ack")
    required_capability = kwargs.pop(
        "required_capability", "entityos.exec" if completion_mode == "verified_effect" else None
    )
    return controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        turn_id,
        completion_mode=completion_mode,
        required_capability=required_capability,
        **kwargs,
    )


def _effect(
    db,
    effect_id,
    capability,
    *,
    target="autonomy-test",
    argv=None,
    generation=1,
    status="VERIFIED",
    ok=True,
):
    target_receipt = EffectJournal._payload(EffectJournal._target_receipt(target))
    argv_receipt = EffectJournal._argv_receipt(argv)
    argv_payload = EffectJournal._payload(argv_receipt) if argv_receipt is not None else None
    outcome = (
        EffectJournal._payload(EffectJournal._outcome_receipt({"ok": ok}))
        if ok is not None
        else None
    )
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            None,
            "gabriel",
            capability,
            target_receipt,
            argv_payload,
            generation,
            status,
            outcome,
            time.time(),
            time.time() if status == "VERIFIED" else None,
        ),
    )


def test_goal_objective_is_copied_from_canonical_user_turn(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Exact owner objective")
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )
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


def test_model_cannot_self_complete_without_independent_evidence(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"], "complete_candidate", "I think the task is done"
    )
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "VERIFYING"
    assert snapshot["current_step"]["step_id"] == step["step_id"]


def test_verified_effect_receipt_is_required_and_exact_autonomous_step_bound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute the exact independently verifiable action",
        effect={
            "capability": "entityos.exec",
            "target": "autonomy-test",
            "argv": ["verify", "autonomy-test"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])

    lifecycle = TurnLifecycle(
        db, "gabriel", "session:gabriel", entityos_bridge=_FakeEntityOS()
    )
    lifecycle.begin_autonomous(
        "Run the admitted autonomous verification action", goal["goal_id"], step["step_id"]
    )
    receipt = lifecycle.request_effect(
        "entityos.exec", "autonomy-test", ["verify", "autonomy-test"]
    )
    result = controller.record_effect_result(
        goal["goal_id"], step["step_id"], receipt["effect_id"]
    )
    assert result["verified"] is True
    lifecycle.complete_autonomous(
        "Verified action completed", goal["goal_id"], step["step_id"]
    )
    done = controller.verify_completion(goal["goal_id"])
    assert done["status"] == "COMPLETED"
    assert done["evidence"] == receipt["effect_id"]


def test_state_noop_cannot_be_automatic_completion_authority(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn("session:gabriel", "gabriel", "user", "Do a real task")
    with pytest.raises(ValueError, match="independently verifiable"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="verified_effect",
            required_capability="state.noop",
        )


def test_same_capability_wrong_target_receipt_cannot_be_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Verify only the exact requested target",
        effect={
            "capability": "entityos.exec",
            "target": "expected-target",
            "argv": ["verify", "expected-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    _effect(
        db,
        "e-wrong",
        "entityos.exec",
        target="different-target",
        argv=["verify", "expected-target"],
    )
    with pytest.raises(PermissionError, match="intent mismatch"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "e-wrong")
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["current_step"]["status"] == "ADMITTED"
    assert snapshot["evidence_effect_ids"] == []
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_same_target_wrong_argv_receipt_cannot_be_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
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
    _effect(
        db,
        "e-wrong-argv",
        "entityos.exec",
        target="entityos-target",
        argv=["operation", "different"],
    )
    with pytest.raises(PermissionError, match="intent mismatch"):
        controller.record_effect_result(
            goal["goal_id"], step["step_id"], "e-wrong-argv"
        )
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["current_step"]["status"] == "ADMITTED"
    assert snapshot["evidence_effect_ids"] == []


def test_identical_intent_from_different_autonomous_episode_cannot_be_rebound(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    expected = _goal(
        db,
        controller,
        objective="Expected goal",
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
    expected_step = controller.propose_step(
        expected["goal_id"],
        "effect",
        "Expected exact action",
        effect={
            "capability": "entityos.exec",
            "target": "same-target",
            "argv": ["verify", "same-target"],
        },
    )
    controller.admit_step(expected["goal_id"], expected_step["step_id"])

    other = _goal(db, controller, objective="Other goal")
    other_step = controller.propose_step(
        other["goal_id"],
        "effect",
        "Same bytes, different causal episode",
        effect={
            "capability": "entityos.exec",
            "target": "same-target",
            "argv": ["verify", "same-target"],
        },
    )
    controller.admit_step(other["goal_id"], other_step["step_id"])

    lifecycle = TurnLifecycle(
        db, "gabriel", "session:gabriel", entityos_bridge=_FakeEntityOS()
    )
    lifecycle.begin_autonomous(
        "Execute the other goal's identical intent", other["goal_id"], other_step["step_id"]
    )
    receipt = lifecycle.request_effect(
        "entityos.exec", "same-target", ["verify", "same-target"]
    )
    controller.record_effect_result(other["goal_id"], other_step["step_id"], receipt["effect_id"])
    lifecycle.complete_autonomous(
        "Other goal effect complete", other["goal_id"], other_step["step_id"]
    )

    with pytest.raises(PermissionError, match="goal-step provenance mismatch"):
        controller.record_effect_result(
            expected["goal_id"], expected_step["step_id"], receipt["effect_id"]
        )
    assert controller.snapshot(user_id="gabriel")["goals"][0]["evidence_effect_ids"] == []


def test_pending_effect_never_counts_as_success(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Pending effect",
        effect={"capability": "state.noop", "target": "x", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    _effect(db, "e1", "state.noop", target="x", status="PENDING", ok=None)
    with pytest.raises(AutonomyStateError):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "e1")
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_wrong_effect_capability_cannot_satisfy_completion(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Harmless probe",
        effect={"capability": "state.noop", "target": "x", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    _effect(db, "e1", "state.noop", target="x")
    with pytest.raises((PermissionError, AutonomyStateError)):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "e1")
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_synthetic_verified_effect_without_causal_reentry_is_rejected(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Synthetic receipts are not operational evidence",
        effect={"capability": "state.noop", "target": "synthetic", "argv": None},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    _effect(db, "synthetic", "state.noop", target="synthetic")
    with pytest.raises((PermissionError, AutonomyStateError)):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "synthetic")
    assert controller.snapshot(user_id="gabriel")["goals"][0]["evidence_effect_ids"] == []


def test_user_ack_requires_canonical_owner_user_turn(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller, objective="Prepare report")
    assistant = db.append_turn("session:gabriel", "gabriel", "assistant", "done")
    other = db.append_turn("session:andreas", "andreas", "user", "yes")
    owner = db.append_turn("session:gabriel", "gabriel", "user", "yes")
    with pytest.raises(PermissionError):
        controller.acknowledge_by_user(goal["goal_id"], assistant)
    with pytest.raises(PermissionError):
        controller.acknowledge_by_user(goal["goal_id"], other)
    controller.acknowledge_by_user(goal["goal_id"], owner)
    assert controller.verify_completion(goal["goal_id"])["evidence"] == owner


def test_process_exec_is_denied_at_proposal_boundary(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller)
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
    goal = _goal(
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
    goal = _goal(
        db,
        controller,
        budget=GoalBudget(max_steps=2, max_retries_per_step=0, max_effects=2),
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
    goal = _goal(db, controller)
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
    goal = _goal(db, controller)
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
    _goal(db, controller)
    db.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        ('{"schema":"ClayVerseAutonomyState/v1","revision":NaN,"goals":{},"queue":[]}',),
    )
    with pytest.raises(AutonomyStateError):
        controller.snapshot()


def test_priority_scheduler_selects_only_live_active_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    low = _goal(db, controller, objective="low", priority=10)
    high = _goal(db, controller, objective="high", priority=90)
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == high["goal_id"]
    controller.block_goal(high["goal_id"], "dependency")
    assert controller.next_runnable(user_id="gabriel")["goal_id"] == low["goal_id"]
