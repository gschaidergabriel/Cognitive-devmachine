import pytest

from clayverse.goals import GoalIntegrityError, GoalKernel, GoalPolicyError
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {"g": "gabriel", "a": "andreas"})
    yield instance
    instance.close()


def _verified_goal(kernel, *, target="goal:test"):
    return kernel.create_goal(
        "gabriel",
        "Reach the requested state and prove it with the admitted effect receipt.",
        success_contract={
            "type": "verified_effects",
            "requirements": [
                {"capability": "state.noop", "target": target, "min_verified": 1}
            ],
        },
        allowed_capabilities=["state.noop"],
        max_steps=4,
        max_retries_per_proposal=1,
    )


def _execute_noop(db, target):
    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    lifecycle.begin(f"AUTONOMOUS_GOAL_STEP target={target}", resources=["goal:test"])
    result = lifecycle.request_effect("state.noop", target, None)
    lifecycle.complete(f"Goal step effect receipt: {result['effect_id']}")
    return result


def test_goal_success_requires_matching_verified_effect_receipt(db):
    kernel = GoalKernel(db)
    goal_id = _verified_goal(kernel, target="goal:verified")
    claim = kernel.claim_next("goal-worker")
    assert claim and claim.goal_id == goal_id

    step = kernel.admit_proposal(
        goal_id,
        {
            "capability": "state.noop",
            "target": "goal:verified",
            "argv": None,
            "summary": "Verify the bounded goal condition.",
        },
        runtime_capabilities=["state.noop"],
        lease=claim.lease,
    )
    effect = _execute_noop(db, "goal:verified")
    observed = kernel.observe_effect(step["step_id"], effect["effect_id"])

    assert observed["step_status"] == "VERIFIED"
    assert observed["goal_status"] == "SUCCEEDED"
    assert kernel.get_goal(goal_id)["status"] == "SUCCEEDED"


def test_model_proposal_cannot_mint_success_without_effect(db):
    kernel = GoalKernel(db)
    goal_id = _verified_goal(kernel)
    claim = kernel.claim_next("goal-worker")
    kernel.admit_proposal(
        goal_id,
        {
            "capability": "state.noop",
            "target": "goal:test",
            "argv": None,
            "summary": "I believe the goal is already complete.",
        },
        runtime_capabilities=["state.noop"],
        lease=claim.lease,
    )

    assert kernel.get_goal(goal_id)["status"] == "ACTIVE"
    assert kernel.success_satisfied(goal_id) is False


def test_mismatched_effect_cannot_be_rebound_to_goal_step(db):
    kernel = GoalKernel(db)
    goal_id = _verified_goal(kernel, target="goal:expected")
    claim = kernel.claim_next("goal-worker")
    step = kernel.admit_proposal(
        goal_id,
        {
            "capability": "state.noop",
            "target": "goal:expected",
            "argv": None,
            "summary": "Execute only the exact admitted target.",
        },
        runtime_capabilities=["state.noop"],
        lease=claim.lease,
    )
    wrong = _execute_noop(db, "goal:different")

    with pytest.raises(GoalIntegrityError, match="does not match admitted goal step"):
        kernel.observe_effect(step["step_id"], wrong["effect_id"])
    assert kernel.get_goal(goal_id)["status"] == "ACTIVE"


def test_unavailable_or_unapproved_capability_fails_closed(db):
    kernel = GoalKernel(db)
    goal_id = _verified_goal(kernel)
    claim = kernel.claim_next("goal-worker")

    with pytest.raises(GoalPolicyError, match="not currently available"):
        kernel.admit_proposal(
            goal_id,
            {
                "capability": "state.noop",
                "target": "goal:test",
                "argv": None,
                "summary": "Runtime falsely claims no capability.",
            },
            runtime_capabilities=[],
            lease=claim.lease,
        )

    with pytest.raises(GoalPolicyError):
        kernel.create_goal(
            "gabriel",
            "Never admit generic host execution.",
            success_contract={"type": "manual"},
            allowed_capabilities=["process.exec"],
        )


def test_restart_marks_unbound_autonomous_step_unknown_and_blocks_goal(db):
    kernel = GoalKernel(db)
    goal_id = _verified_goal(kernel)
    claim = kernel.claim_next("goal-worker")
    step = kernel.admit_proposal(
        goal_id,
        {
            "capability": "state.noop",
            "target": "goal:test",
            "argv": None,
            "summary": "Admit but do not execute before simulated restart.",
        },
        runtime_capabilities=["state.noop"],
        lease=claim.lease,
    )

    recovered = kernel.recover_after_restart()
    assert recovered == {"admitted_steps_marked_unknown": 1, "goals_blocked": 1}
    assert kernel.get_goal(goal_id)["status"] == "BLOCKED"
    assert kernel.steps(goal_id)[0]["step_id"] == step["step_id"]
    assert kernel.steps(goal_id)[0]["status"] == "UNKNOWN"


def test_goal_state_hash_is_bound_into_unifieddb_checkpoint(db):
    kernel = GoalKernel(db)
    _, before = db.checkpoint("before-goal")
    _verified_goal(kernel)
    _, after = db.checkpoint("after-goal")
    assert before != after
    digest = db.db.execute("SELECT value FROM meta WHERE key='goal_state_hash'").fetchone()[0]
    assert isinstance(digest, str) and len(digest) == 64


def test_manual_contract_never_auto_promotes_from_model_or_noop(db):
    kernel = GoalKernel(db)
    goal_id = kernel.create_goal(
        "gabriel",
        "Keep this goal human-verifiable only.",
        success_contract={"type": "manual"},
        allowed_capabilities=["state.noop"],
    )
    claim = kernel.claim_next("goal-worker")
    step = kernel.admit_proposal(
        goal_id,
        {
            "capability": "state.noop",
            "target": "goal:manual",
            "argv": None,
            "summary": "A successful effect still cannot satisfy a manual contract.",
        },
        runtime_capabilities=["state.noop"],
        lease=claim.lease,
    )
    effect = _execute_noop(db, "goal:manual")
    observed = kernel.observe_effect(step["step_id"], effect["effect_id"])
    assert observed["step_status"] == "VERIFIED"
    assert observed["goal_status"] == "ACTIVE"
    assert kernel.success_satisfied(goal_id) is False
