import json
import time
import uuid

import pytest

from clayverse.autonomy import (
    AutonomyIntegrityError,
    AutonomySupervisor,
    GoalLimits,
)
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    state = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(state, {"g": "gabriel", "a": "andreas"})
    yield state
    state.close()


def new_goal(
    db,
    *,
    verifiers=None,
    allowed_capabilities=(),
    limits=None,
    objective="finish the admitted bounded task",
):
    supervisor = AutonomySupervisor(db)
    goal_id = supervisor.store.create_goal(
        "gabriel",
        objective,
        verifiers=verifiers or [{"id": "owner-ack", "kind": "user_ack"}],
        allowed_capabilities=allowed_capabilities,
        limits=limits,
    )
    supervisor.store.activate(goal_id, "gabriel")
    return supervisor, goal_id


def test_identity_and_autonomy_are_state_not_agency_claims(db):
    supervisor, goal_id = new_goal(
        db,
        verifiers=[
            {
                "id": "real-effect",
                "kind": "effect_verified",
                "capability": "entityos.exec",
            }
        ],
        allowed_capabilities=["entityos.exec"],
    )
    step = supervisor.store.begin_step(supervisor.store.get(goal_id))
    context = supervisor.context_for(step)

    assert context["operational_identity"]["persistent_state_authority"] == "UnifiedDB"
    assert context["operational_identity"]["model_role"] == "planner_cognition_not_authority"
    assert context["laws"]["model_cannot_mark_goal_succeeded"] is True
    assert context["laws"]["effect_execution_requires_canonical_effectgate_receipt"] is True
    assert context["capabilities"] == []

    supervisor.store.block_step(step, "test_cleanup")


def test_model_cannot_smuggle_success_or_executed_fields(db):
    supervisor, goal_id = new_goal(db)
    executor_called = False

    def planner(_context):
        return {
            "selection": "no_effect",
            "effect": None,
            "reason": "pretend done",
            "succeeded": True,
            "executed": True,
        }

    def executor(_step, _proposal, _context):
        nonlocal executor_called
        executor_called = True
        return {"kind": "no_effect"}

    result = supervisor.tick(planner, executor)

    assert result["status"] == "STEP_FAILED"
    assert executor_called is False
    assert supervisor.store.get(goal_id).status == "ACTIVE"
    assert supervisor.store.get(goal_id).verified_ids == ()


def test_checkpoint_verifier_deterministically_completes_goal(db):
    supervisor, goal_id = new_goal(
        db,
        verifiers=[
            {
                "id": "verified-checkpoint",
                "kind": "checkpoint",
                "note_prefix": "autonomy-test:verified:",
            }
        ],
    )

    def planner(_context):
        return {"selection": "no_effect", "effect": None, "reason": "verify state"}

    def executor(_step, _proposal, _context):
        checkpoint_id, _ = db.checkpoint("autonomy-test:verified:source-bound")
        supervisor.store.record_checkpoint(
            goal_id, "verified-checkpoint", checkpoint_id
        )
        # The goal cannot complete while the admitted step is still open.
        assert supervisor.store.get(goal_id).status == "ACTIVE"
        return {"kind": "no_effect"}

    result = supervisor.tick(planner, executor)

    assert result["status"] == "SUCCEEDED"
    goal = supervisor.store.get(goal_id)
    assert goal.status == "SUCCEEDED"
    assert goal.verified_ids == ("verified-checkpoint",)
    assert any(
        event["event_type"] == "GOAL_SUCCEEDED"
        for event in supervisor.store.event_log(goal_id)
    )


def test_executor_exception_becomes_unknown_block_not_retry(db):
    supervisor, goal_id = new_goal(db)

    def planner(_context):
        return {"selection": "no_effect", "effect": None, "reason": "bounded work"}

    def executor(_step, _proposal, _context):
        raise RuntimeError("executor disappeared after an unknown boundary")

    result = supervisor.tick(planner, executor)

    assert result["status"] == "UNKNOWN_BLOCKED"
    assert supervisor.store.get(goal_id).status == "BLOCKED"
    row = db.db.execute(
        "SELECT status,failure_class FROM autonomy_steps WHERE goal_id=?",
        (goal_id,),
    ).fetchone()
    assert row["status"] == "UNKNOWN"
    assert row["failure_class"] == "executor_outcome_unknown"


def test_repeated_invalid_model_output_hits_deterministic_loop_brake(db):
    supervisor, goal_id = new_goal(
        db,
        limits=GoalLimits(
            max_steps=10,
            max_failures=10,
            max_effects=0,
            max_same_failure=2,
        ),
    )

    def invalid_planner(_context):
        return {"selection": "claim_success", "reason": "wrong protocol"}

    def executor(_step, _proposal, _context):
        pytest.fail("invalid model proposal must never reach executor")

    assert supervisor.tick(invalid_planner, executor)["status"] == "STEP_FAILED"
    assert supervisor.tick(invalid_planner, executor)["status"] == "STEP_FAILED"
    third = supervisor.tick(invalid_planner, executor)

    assert third["status"] == "LIMIT_REACHED"
    goal = supervisor.store.get(goal_id)
    assert goal.status == "BLOCKED"
    assert goal.same_failure_streak == 2


def test_state_digest_detects_out_of_band_goal_tampering(db):
    supervisor, goal_id = new_goal(db)
    assert supervisor.store.verify_integrity()

    db.db.execute(
        "UPDATE autonomy_goals SET objective='tampered outside autonomy state machine' "
        "WHERE goal_id=?",
        (goal_id,),
    )

    with pytest.raises(AutonomyIntegrityError, match="digest mismatch"):
        supervisor.store.verify_integrity()


def _insert_effect_fixture(
    db,
    *,
    goal_id,
    step,
    correct_resources,
    capability="entityos.exec",
    status="VERIFIED",
    ok=True,
):
    now = time.time()
    episode_id = str(uuid.uuid4())
    turn_id = db.append_turn(
        step.session_id,
        step.user_id,
        "system",
        "executor observation fixture",
        resources=(
            [step.goal_resource, step.step_resource]
            if correct_resources
            else [step.goal_resource, "goal-step:wrong"]
        ),
        provenance={"source": "test-executor-fixture"},
    )
    db.db.execute(
        "INSERT INTO workspace_episodes("
        "episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state"
        ") VALUES(?,?,?,?,?,?,?,?)",
        (
            episode_id,
            step.session_id,
            now,
            turn_id,
            0.5,
            json.dumps([{"id": "request_effect", "kind": "effect_intent"}]),
            "request_effect",
            "SELECTED",
        ),
    )
    effect_id = str(uuid.uuid4())
    outcome = {
        "audit": "redacted-outcome-v1",
        "sha256": "0" * 64,
        "bytes": 2,
        "ok": bool(ok),
        "boundary": "EntityOS",
    }
    db.db.execute(
        "INSERT INTO effects("
        "effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at"
        ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            step.user_id,
            capability,
            json.dumps({"audit": "redacted-target-v1", "sha256": "1" * 64, "bytes": 1}),
            None,
            step.generation,
            status,
            json.dumps(outcome, sort_keys=True, separators=(",", ":")),
            now,
            now,
        ),
    )
    causal_id = str(uuid.uuid4())
    db.db.execute(
        "INSERT INTO causal_episodes("
        "causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts"
        ") VALUES(?,?,?,?,?,?,?,?)",
        (
            causal_id,
            episode_id,
            effect_id,
            turn_id,
            "2" * 64,
            1.0 if status == "VERIFIED" and ok else 0.0,
            1,
            now,
        ),
    )
    return effect_id


def test_verified_effect_must_be_bound_to_exact_goal_step_resources(db):
    supervisor, goal_id = new_goal(
        db,
        verifiers=[
            {
                "id": "effect-proof",
                "kind": "effect_verified",
                "capability": "entityos.exec",
            }
        ],
        allowed_capabilities=["entityos.exec"],
    )
    step = supervisor.store.begin_step(supervisor.store.get(goal_id))
    supervisor.store.record_proposal(
        step,
        {
            "selection": "request_effect",
            "effect": {
                "capability": "entityos.exec",
                "target": "bounded-target",
                "argv": ["verify"],
            },
            "reason": "test receipt binding",
        },
    )
    effect_id = _insert_effect_fixture(
        db, goal_id=goal_id, step=step, correct_resources=True
    )

    goal = supervisor.store.record_effect(step, effect_id)

    assert goal.status == "SUCCEEDED"
    assert goal.verified_ids == ("effect-proof",)


def test_effect_from_other_resource_cannot_satisfy_goal(db):
    supervisor, goal_id = new_goal(
        db,
        verifiers=[
            {
                "id": "effect-proof",
                "kind": "effect_verified",
                "capability": "entityos.exec",
            }
        ],
        allowed_capabilities=["entityos.exec"],
    )
    step = supervisor.store.begin_step(supervisor.store.get(goal_id))
    supervisor.store.record_proposal(
        step,
        {
            "selection": "request_effect",
            "effect": {
                "capability": "entityos.exec",
                "target": "bounded-target",
                "argv": ["verify"],
            },
            "reason": "test receipt isolation",
        },
    )
    effect_id = _insert_effect_fixture(
        db, goal_id=goal_id, step=step, correct_resources=False
    )

    with pytest.raises(
        AutonomyIntegrityError, match="effect is not bound to this goal step"
    ):
        supervisor.store.record_effect(step, effect_id)

    goal = supervisor.store.get(goal_id)
    assert goal.status == "ACTIVE"
    assert goal.verified_ids == ()
