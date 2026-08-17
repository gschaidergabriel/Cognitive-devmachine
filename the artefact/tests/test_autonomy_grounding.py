from __future__ import annotations

import pytest

from clayverse.autonomy import (
    AutonomyController,
    AutonomyState,
    GoalBlocked,
    VerificationResult,
)
from clayverse.autonomy_runtime import SupervisorAutonomyController
from clayverse.goal_admission import admit_explicit_user_goal
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "terminal-gabriel")
    db.ensure_session("andreas", "terminal-andreas")
    return db


def _goal(state: AutonomyState, *, budget=6):
    goal_id = state.admit_goal(
        "gabriel",
        "repair the bounded product path",
        success_contract={"kind": "typed_verifier", "required": ["TEST"]},
        attempt_budget=budget,
    )
    step_id = state.add_step(
        goal_id,
        "run the discriminating check",
        verification_contract={"kind": "typed_verifier", "required": "TEST"},
    )
    return goal_id, step_id


def _goal_verifier(goal, receipts):
    if any(row["kind"] == "TEST" and int(row["verified"]) == 1 for row in receipts):
        return VerificationResult(True, "goal contract satisfied", {"receipt_kind": "TEST"}, kind="TEST")
    return VerificationResult(False, "missing verified test receipt", {})


def test_model_cannot_mint_unobserved_capability(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        controller = AutonomyController(
            state,
            capability_provider=lambda: ("state.noop",),
            planner=lambda snapshot: {
                "kind": "effect",
                "capability": "process.exec",
                "target": "host",
            },
            effect_executor=lambda snapshot, proposal: pytest.fail("effect boundary must not run"),
            observer=lambda snapshot, proposal: pytest.fail("observer must not run"),
            step_verifier=lambda snapshot, proposal, receipt: pytest.fail("verifier must not run"),
            goal_verifier=_goal_verifier,
        )

        first = controller.tick()
        second = controller.tick()
        assert first.state == "FAILED"
        assert second.state == "BLOCKED"
        assert state.goal(goal_id)["status"] == "BLOCKED"
        assert state.step(step_id)["status"] == "BLOCKED"
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    finally:
        db.close()


def test_model_completion_proposal_is_rejected(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        controller = AutonomyController(
            state,
            capability_provider=lambda: (),
            planner=lambda snapshot: {"kind": "complete", "summary": "I finished it"},
            effect_executor=lambda snapshot, proposal: pytest.fail("effect boundary must not run"),
            observer=lambda snapshot, proposal: pytest.fail("observer must not run"),
            step_verifier=lambda snapshot, proposal, receipt: pytest.fail("verifier must not run"),
            goal_verifier=_goal_verifier,
        )
        controller.tick()
        controller.tick()
        assert state.goal(goal_id)["status"] == "BLOCKED"
        assert state.step(step_id)["status"] == "BLOCKED"
    finally:
        db.close()


def test_verified_effect_receipt_alone_cannot_complete_step(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        generation = db.entity_generation()
        receipt_id = state.record_receipt(
            goal_id,
            step_id,
            kind="EFFECT",
            source="effect-boundary",
            verified=True,
            payload={"verified": True, "ok": True},
            generation=generation,
        )
        with pytest.raises(GoalBlocked):
            state.verify_step(goal_id, step_id, receipt_id)
        assert state.step(step_id)["status"] == "PENDING"
        assert state.goal(goal_id)["status"] == "ACTIVE"
    finally:
        db.close()


def test_stale_generation_receipt_is_rejected(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        stale_generation = db.entity_generation()
        db.advance_entity_generation()
        with pytest.raises(GoalBlocked):
            state.record_receipt(
                goal_id,
                step_id,
                kind="TEST",
                source="test-runner",
                verified=True,
                payload={"passed": True},
                generation=stale_generation,
            )
        assert not state.verified_receipts(step_id)
    finally:
        db.close()


def test_typed_verifier_can_progress_and_goal_needs_goal_verifier(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        controller = AutonomyController(
            state,
            capability_provider=lambda: ("entityos.exec",),
            planner=lambda snapshot: {
                "kind": "effect",
                "capability": "entityos.exec",
                "target": "pytest",
                "argv": ["tests/test_target.py"],
            },
            effect_executor=lambda snapshot, proposal: {
                "verified": True,
                "ok": True,
                "effect_id": "effect:test",
                "exit_code": 0,
            },
            observer=lambda snapshot, proposal: pytest.fail("observer must not run"),
            step_verifier=lambda snapshot, proposal, receipt: VerificationResult(
                True,
                "test oracle passed",
                {"suite": "target", "exit_code": 0},
                source="isolated-test-oracle",
                kind="TEST",
            ),
            goal_verifier=_goal_verifier,
        )

        result = controller.tick()
        assert result.state == "VERIFIED"
        assert state.step(step_id)["status"] == "VERIFIED"
        assert state.goal(goal_id)["status"] == "DONE"
        kinds = [
            row[0]
            for row in db.db.execute(
                "SELECT kind FROM autonomy_receipts WHERE goal_id=? ORDER BY ts", (goal_id,)
            ).fetchall()
        ]
        assert kinds[0] == "EFFECT"
        assert "TEST" in kinds
    finally:
        db.close()


def test_negative_verifier_quiesces_without_reexecution(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        observations = []

        def observer(snapshot, proposal):
            observations.append(proposal)
            return {"verified": True, "value": "candidate"}

        controller = AutonomyController(
            state,
            capability_provider=lambda: (),
            planner=lambda snapshot: {"kind": "observe", "query": "inspect current state"},
            effect_executor=lambda snapshot, proposal: pytest.fail("effect boundary must not run"),
            observer=observer,
            step_verifier=lambda snapshot, proposal, receipt: VerificationResult(
                False, "observation is insufficient to prove success", {"value": "candidate"}
            ),
            goal_verifier=_goal_verifier,
        )
        first = controller.tick()
        second = controller.tick()
        assert first.state == "WAITING_VERIFICATION"
        assert second.state == "IDLE"
        assert len(observations) == 1
        assert state.step(step_id)["status"] == "WAITING_VERIFICATION"
        assert state.goal(goal_id)["status"] == "PAUSED"
    finally:
        db.close()


def test_ambiguous_effect_exception_blocks_without_retry(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        effects = []

        def executor(snapshot, proposal):
            effects.append(proposal)
            raise TimeoutError("acknowledgement lost")

        controller = AutonomyController(
            state,
            capability_provider=lambda: ("entityos.exec",),
            planner=lambda snapshot: {
                "kind": "effect",
                "capability": "entityos.exec",
                "target": "bounded-target",
                "argv": ["check"],
            },
            effect_executor=executor,
            observer=lambda snapshot, proposal: pytest.fail("observer must not run"),
            step_verifier=lambda snapshot, proposal, receipt: pytest.fail("verifier must not run"),
            goal_verifier=_goal_verifier,
        )
        first = controller.tick()
        second = controller.tick()
        assert first.state == "BLOCKED"
        assert second.state == "IDLE"
        assert len(effects) == 1
        assert state.goal(goal_id)["status"] == "BLOCKED"
        assert state.step(step_id)["status"] == "BLOCKED"
        assert "effect_outcome_unknown" in state.step(step_id)["last_error"]
    finally:
        db.close()


def test_explicit_goal_admission_is_user_grounded_and_not_completion(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        source_turn_id = db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            "/goal ship the verified artifact",
            provenance={"source": "test-user"},
        )
        admission = admit_explicit_user_goal(
            state,
            user_id="gabriel",
            source_turn_id=source_turn_id,
            prompt="/goal ship the verified artifact",
        )
        assert admission is not None
        assert state.goal(admission.goal_id)["objective"] == "ship the verified artifact"
        assert state.goal(admission.goal_id)["status"] == "ACTIVE"
        assert state.step(admission.step_id)["status"] == "PENDING"
        receipt = db.db.execute(
            "SELECT kind,source,verified,payload FROM autonomy_receipts WHERE receipt_id=?",
            (admission.receipt_id,),
        ).fetchone()
        assert receipt["kind"] == "OBSERVATION"
        assert receipt["source"] == "explicit-user-goal-admission"
        assert int(receipt["verified"]) == 1
        with pytest.raises(GoalBlocked):
            state.verify_step(admission.goal_id, admission.step_id, admission.receipt_id)
    finally:
        db.close()


def test_non_goal_prompt_cannot_create_goal(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        source_turn_id = db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            "please think about shipping something",
            provenance={"source": "test-user"},
        )
        admission = admit_explicit_user_goal(
            state,
            user_id="gabriel",
            source_turn_id=source_turn_id,
            prompt="please think about shipping something",
        )
        assert admission is None
        assert db.db.execute("SELECT COUNT(*) FROM autonomy_goals").fetchone()[0] == 0
    finally:
        db.close()


def test_planner_block_is_persisted_and_not_repolled(tmp_path):
    db = _db(tmp_path)
    try:
        state = AutonomyState(db)
        goal_id, step_id = _goal(state)
        calls = []

        def planner(snapshot):
            calls.append(snapshot["step"]["step_id"])
            return {"kind": "blocked", "reason": "credential_missing"}

        base = AutonomyController(
            state,
            capability_provider=lambda: (),
            planner=planner,
            effect_executor=lambda snapshot, proposal: pytest.fail("effect boundary must not run"),
            observer=lambda snapshot, proposal: pytest.fail("observer must not run"),
            step_verifier=lambda snapshot, proposal, receipt: pytest.fail("verifier must not run"),
            goal_verifier=_goal_verifier,
        )
        controller = SupervisorAutonomyController(base)
        first = controller.tick()
        second = controller.tick()
        assert first.state == "BLOCKED"
        assert second.state == "IDLE"
        assert calls == [step_id]
        assert state.goal(goal_id)["status"] == "BLOCKED"
        assert state.step(step_id)["status"] == "BLOCKED"
    finally:
        db.close()
