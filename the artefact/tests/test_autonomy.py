from __future__ import annotations

import hashlib
import json
import time

import pytest

from clayverse.autonomy import (
    AutonomyBudgetExceeded,
    AutonomyController,
    AutonomyStateError,
    CompletionNotVerified,
    GoalBudget,
    IDENTITY_STATE,
    STATE_KEY,
    STATE_SCHEMA,
)
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _turn(db, user_id="gabriel", role="user", content="Finish the bounded task"):
    return db.append_turn(f"session:{user_id}", user_id, role, content)


def _goal(
    db,
    controller,
    *,
    objective="Finish the bounded task",
    target="autonomy-target",
    completion_mode="verified_effect",
    priority=50,
    budget=None,
):
    source = _turn(db, content=objective)
    kwargs = {
        "completion_mode": completion_mode,
        "priority": priority,
        "budget": budget,
    }
    if completion_mode == "verified_effect":
        kwargs.update(required_capability="entityos.exec", required_target=target)
    return controller.create_goal_from_turn("gabriel", "session:gabriel", source, **kwargs)


class _FakeEntityOS:
    sha256 = "1" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0}


def _real_effect(db, *, target="autonomy-target", capability="entityos.exec", argv=None):
    lifecycle = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_FakeEntityOS(),
    )
    lifecycle.begin(f"Execute bounded effect for {target}")
    if capability == "entityos.exec":
        argv = argv or ["verify", target]
    result = lifecycle.request_effect(capability, target, argv)
    assert result["verified"] is True
    return result["effect_id"]


def test_identity_is_persisted_control_state_not_model_persona(db):
    controller = AutonomyController(db)
    snap = controller.snapshot()
    assert snap["schema"] == STATE_SCHEMA
    assert snap["identity"] == IDENTITY_STATE
    assert snap["identity"]["operating_mode"] == "HIGH_AGENCY_GROUNDED"
    assert snap["identity"]["model_authority"] == "PROPOSAL_ONLY"
    assert "AGI" not in snap["identity"]["mission"]
    assert db.db.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone() is not None


def test_goal_objective_is_exact_canonical_user_turn(db):
    controller = AutonomyController(db)
    objective = "  Exact owner objective\n"
    source = _turn(db, content=objective)
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="user_ack",
    )
    assert goal["objective"] == objective
    assert goal["source_turn_id"] == source


def test_assistant_or_other_user_turn_cannot_mint_goal(db):
    controller = AutonomyController(db)
    assistant = _turn(db, role="assistant", content="invented goal")
    other = _turn(db, user_id="andreas", content="other perspective")
    with pytest.raises(PermissionError):
        controller.create_goal_from_turn(
            "gabriel", "session:gabriel", assistant, completion_mode="user_ack"
        )
    with pytest.raises(PermissionError):
        controller.create_goal_from_turn(
            "gabriel", "session:gabriel", other, completion_mode="user_ack"
        )


def test_state_noop_is_forbidden_as_automatic_completion_contract(db):
    controller = AutonomyController(db)
    source = _turn(db)
    with pytest.raises(ValueError, match="never state.noop"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="verified_effect",
            required_capability="state.noop",
            required_target="x",
        )


def test_verified_effect_completion_requires_exact_target(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller, target="expected-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Run a different but valid intermediate effect",
        effect={"capability": "entityos.exec", "target": "other-target", "argv": ["verify", "other"]},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _real_effect(db, target="other-target", argv=["verify", "other"])
    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)
    assert result["verified"] is True
    assert result["completion_evidence"] is False
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_exact_verified_causally_reentered_effect_completes_goal(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller, target="expected-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Execute exact success contract",
        effect={
            "capability": "entityos.exec",
            "target": "expected-target",
            "argv": ["verify", "expected-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _real_effect(
        db,
        target="expected-target",
        argv=["verify", "expected-target"],
    )
    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)
    assert result["verified"] is True
    assert result["completion_evidence"] is True
    done = controller.verify_completion(goal["goal_id"])
    assert done == {"goal_id": goal["goal_id"], "status": "COMPLETED", "evidence": effect_id}


def test_model_complete_candidate_is_never_completion_evidence(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    step = controller.propose_step(
        goal["goal_id"], "complete_candidate", "I think the task is done"
    )
    assert step["kind"] == "complete_candidate"
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "VERIFYING"


def test_synthetic_verified_row_without_session_and_causal_reentry_is_rejected(db):
    controller = AutonomyController(db)
    target = "expected-target"
    goal = _goal(db, controller, target=target)
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "Attempt synthetic evidence",
        effect={"capability": "entityos.exec", "target": target, "argv": ["verify", target]},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    target_receipt = json.dumps(
        {
            "audit": "redacted-target-v1",
            "sha256": hashlib.sha256(target.encode()).hexdigest(),
            "bytes": len(target.encode()),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "synthetic-effect",
            None,
            "gabriel",
            "entityos.exec",
            target_receipt,
            None,
            db.entity_generation(),
            "VERIFIED",
            json.dumps({"ok": True}),
            time.time(),
            time.time(),
        ),
    )
    with pytest.raises(PermissionError, match="owner/session mismatch"):
        controller.record_effect_result(goal["goal_id"], step["step_id"], "synthetic-effect")
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_user_ack_requires_explicit_later_owner_turn(db):
    controller = AutonomyController(db)
    source = _turn(db, content="Prepare report")
    goal = controller.create_goal_from_turn(
        "gabriel", "session:gabriel", source, completion_mode="user_ack"
    )
    with pytest.raises(PermissionError, match="explicit later"):
        controller.acknowledge_by_user(goal["goal_id"], source)
    wrong = _turn(db, user_id="andreas", content="yes")
    with pytest.raises(PermissionError):
        controller.acknowledge_by_user(goal["goal_id"], wrong)
    owner = _turn(db, content="yes, this goal is complete")
    controller.acknowledge_by_user(goal["goal_id"], owner)
    assert controller.verify_completion(goal["goal_id"])["evidence"] == owner


def test_process_exec_is_denied_at_proposal_boundary(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller)
    with pytest.raises(PermissionError):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "bypass",
            effect={"capability": "process.exec", "target": "host", "argv": ["id"]},
        )


def test_zero_effect_budget_still_allows_reasoning_steps(db):
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="user_ack",
        budget=GoalBudget(max_steps=2, max_retries_per_step=0, max_effects=0),
    )
    reason = controller.propose_step(goal["goal_id"], "reason", "derive next bounded action")
    controller.admit_step(goal["goal_id"], reason["step_id"])
    controller.record_reason_success(goal["goal_id"], reason["step_id"])
    with pytest.raises(AutonomyBudgetExceeded, match="effect budget"):
        controller.propose_step(
            goal["goal_id"],
            "effect",
            "no effect budget",
            effect={"capability": "state.noop", "target": "x", "argv": None},
        )


def test_step_budget_is_hard_bound(db):
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="user_ack",
        budget=GoalBudget(max_steps=1, max_retries_per_step=0, max_effects=0),
    )
    step = controller.propose_step(goal["goal_id"], "reason", "one allowed step")
    controller.admit_step(goal["goal_id"], step["step_id"])
    controller.record_reason_success(goal["goal_id"], step["step_id"])
    with pytest.raises(AutonomyBudgetExceeded, match="step budget"):
        controller.propose_step(goal["goal_id"], "reason", "must not loop")


def test_retry_budget_eventually_blocks_same_failed_step(db):
    controller = AutonomyController(db)
    goal = _goal(
        db,
        controller,
        completion_mode="user_ack",
        budget=GoalBudget(max_steps=4, max_retries_per_step=1, max_effects=0),
    )
    step = controller.propose_step(goal["goal_id"], "reason", "repair")
    controller.admit_step(goal["goal_id"], step["step_id"])
    first = controller.record_step_failure(goal["goal_id"], step["step_id"], "bad")
    assert first["status"] == "ACTIVE"
    controller.admit_step(goal["goal_id"], step["step_id"])
    second = controller.record_step_failure(goal["goal_id"], step["step_id"], "bad again")
    assert second["status"] == "BLOCKED"
    assert second["reason"] == "retry_budget_exhausted"


def test_stale_generation_fences_goal_progress(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller, completion_mode="user_ack")
    db.advance_entity_generation()
    with pytest.raises(StaleGeneration):
        controller.propose_step(goal["goal_id"], "reason", "stale worker")


def test_goal_claim_lease_prevents_duplicate_worker_claim(db):
    controller = AutonomyController(db)
    goal = _goal(db, controller, completion_mode="user_ack")
    first = controller.claim_next("worker-A", ttl=30)
    assert first is not None and first.goal_id == goal["goal_id"]
    controller.assert_claim(first)
    assert controller.claim_next("worker-B", ttl=30) is None
    controller.release_claim(first)
    second = controller.claim_next("worker-B", ttl=30)
    assert second is not None and second.goal_id == goal["goal_id"]
    controller.release_claim(second)


def test_autonomy_state_changes_canonical_checkpoint_hash(db):
    _, before = db.checkpoint("before-autonomy")
    controller = AutonomyController(db)
    _, initialized = db.checkpoint("after-autonomy-init")
    assert initialized != before
    _goal(db, controller, completion_mode="user_ack")
    _, after_goal = db.checkpoint("after-goal")
    assert after_goal != initialized


def test_corrupt_or_drifting_identity_state_fails_closed(db):
    controller = AutonomyController(db)
    state = json.loads(db.db.execute("SELECT value FROM meta WHERE key=?", (STATE_KEY,)).fetchone()[0])
    state["identity"]["model_authority"] = "SELF_AUTHORIZING"
    db.db.execute(
        "UPDATE meta SET value=? WHERE key=?",
        (json.dumps(state, sort_keys=True, separators=(",", ":")), STATE_KEY),
    )
    with pytest.raises(AutonomyStateError, match="identity contract mismatch"):
        controller.snapshot()
