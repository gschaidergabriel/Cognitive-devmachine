import hashlib

import pytest

from clayverse.autonomy import AutonomyError, AutonomousGoalKernel, GoalContractError
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _user_turn(db, user_id="gabriel", content="Finish the admitted bounded task"):
    session_id = f"session:{user_id}"
    return db.append_turn(
        session_id,
        user_id,
        "user",
        content,
        provenance={"source": "test:authenticated-human"},
    )


def test_identity_is_persisted_state_but_makes_no_model_capability_claim(db):
    kernel = AutonomousGoalKernel(db)
    snapshot = kernel.identity_snapshot()
    assert snapshot["entity_name"] == "ClayVerse"
    assert snapshot["state_authority"] == "UnifiedDB"
    assert snapshot["operating_mode"] == "HIGH_AGENCY_GROUNDED"
    assert "model statements are proposals" in snapshot["epistemic_law"]
    assert "AGI" not in snapshot["mission"]
    assert "sovereign" not in snapshot["mission"].lower()


def test_model_or_system_turn_cannot_mint_goal(db):
    kernel = AutonomousGoalKernel(db)
    sid = "session:gabriel"
    model_turn = db.append_turn(sid, "gabriel", "assistant", "I declare a new goal")
    with pytest.raises(PermissionError, match="human user turn"):
        kernel.create_goal_from_user_turn(model_turn, {"type": "human_confirmation"})


def test_goal_objective_is_exact_human_turn_not_model_rewrite(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db, content="Refactor module X and prove its tests")
    goal_id = kernel.create_goal_from_user_turn(source, {"type": "human_confirmation"})
    assert kernel.goal(goal_id)["objective"] == "Refactor module X and prove its tests"


def test_proposal_never_completes_goal(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    goal_id = kernel.create_goal_from_user_turn(source, {"type": "human_confirmation"}, max_cycles=3)
    claim = kernel.claim_next("worker-A")
    assert claim and claim.goal_id == goal_id
    cycle = kernel.begin_cycle(claim)
    kernel.record_proposal(cycle["cycle"]["cycle_id"], {"text": "Done. Everything passed.", "effect": None})
    assert kernel.goal(goal_id)["status"] == "ACTIVE"
    kernel.release_claim(claim)


def test_human_confirmation_requires_same_owner_and_later_user_turn(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    goal_id = kernel.create_goal_from_user_turn(source, {"type": "human_confirmation"})
    wrong = _user_turn(db, user_id="andreas", content="confirm")
    with pytest.raises(PermissionError):
        kernel.confirm_goal(goal_id, wrong)
    confirmation = _user_turn(db, content="confirm")
    assert kernel.confirm_goal(goal_id, confirmation) is True
    assert kernel.goal(goal_id)["status"] == "COMPLETED"


def test_automatic_completion_contract_is_exact_and_refuses_noop(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    with pytest.raises(GoalContractError):
        kernel.create_goal_from_user_turn(
            source,
            {"type": "verified_effect", "capability": "state.noop", "target_sha256": "0" * 64},
        )


def test_hallucinated_or_unverified_effect_cannot_complete_goal(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    target = "bounded:artifact"
    goal_id = kernel.create_goal_from_user_turn(
        source,
        {
            "type": "verified_effect",
            "capability": "entityos.exec",
            "target_sha256": hashlib.sha256(target.encode()).hexdigest(),
        },
    )
    claim = kernel.claim_next("worker-A")
    cycle = kernel.begin_cycle(claim)
    cycle_id = cycle["cycle"]["cycle_id"]
    kernel.record_proposal(cycle_id, {"text": "I executed it successfully", "effect": None})
    with pytest.raises(KeyError):
        kernel.record_verified_effect(cycle_id, "invented-effect-id")
    assert kernel.goal(goal_id)["status"] == "ACTIVE"
    kernel.release_claim(claim)


class _FakeEntityOS:
    sha256 = "1" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0}


def test_only_verified_causally_reentered_exact_effect_can_auto_complete(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    target = "bounded:artifact"
    goal_id = kernel.create_goal_from_user_turn(
        source,
        {
            "type": "verified_effect",
            "capability": "entityos.exec",
            "target_sha256": hashlib.sha256(target.encode()).hexdigest(),
        },
    )
    claim = kernel.claim_next("worker-A")
    cycle = kernel.begin_cycle(claim)
    cycle_id = cycle["cycle"]["cycle_id"]
    kernel.record_proposal(cycle_id, {"text": "proposal", "effect": {"capability": "entityos.exec"}})

    lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=_FakeEntityOS())
    lifecycle.begin("Execute the exact admitted bounded effect")
    result = lifecycle.request_effect("entityos.exec", target, ["verify", "artifact"])
    assert result["verified"] is True

    assert kernel.record_verified_effect(cycle_id, result["effect_id"]) is True
    assert kernel.goal(goal_id)["status"] == "COMPLETED"
    kernel.release_claim(claim)


def test_cycle_and_failure_budgets_fail_closed(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    goal_id = kernel.create_goal_from_user_turn(
        source,
        {"type": "human_confirmation"},
        max_cycles=1,
        max_failures=1,
    )
    claim = kernel.claim_next("worker-A")
    cycle = kernel.begin_cycle(claim)
    failed = kernel.fail_cycle(cycle["cycle"]["cycle_id"], "validator rejected proposal")
    assert failed["status"] == "BLOCKED"
    assert failed["blocked_reason"] == "failure_budget_exhausted"
    kernel.release_claim(claim)
    assert kernel.claim_next("worker-B") is None


def test_stale_generation_fences_claimed_goal_cycle(db):
    kernel = AutonomousGoalKernel(db)
    source = _user_turn(db)
    kernel.create_goal_from_user_turn(source, {"type": "human_confirmation"})
    claim = kernel.claim_next("worker-A")
    db.advance_entity_generation()
    with pytest.raises(StaleGeneration):
        kernel.begin_cycle(claim)
    kernel.release_claim(claim)


def test_autonomy_state_is_folded_into_unifieddb_checkpoint_via_meta_hash(db):
    kernel = AutonomousGoalKernel(db)
    _, before = db.checkpoint("before-goal")
    source = _user_turn(db)
    kernel.create_goal_from_user_turn(source, {"type": "human_confirmation"})
    _, after = db.checkpoint("after-goal")
    assert before != after
    value = db.db.execute("SELECT value FROM meta WHERE key='autonomy_state_hash'").fetchone()[0]
    assert len(value) == 64
