from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController, AutonomyStateError
from clayverse.autonomy_integration import (
    admit_explicit_goal_from_turn,
    grounded_autonomy_context,
    recover_autonomy_after_generation_advance,
)
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "terminal-gabriel")
    db.ensure_session("andreas", "terminal-andreas")
    return db


def _hook_turn(db: UnifiedDB, user_id: str, prompt: str) -> str:
    generation = db.entity_generation()
    return db.append_turn(
        f"session:{user_id}",
        user_id,
        "user",
        prompt,
        provenance={
            "source": "claude-hook:UserPromptSubmit",
            "session_generation": generation,
            "entity_generation": generation,
            "causal_id": f"causal:{user_id}:{generation}:{prompt[:8]}",
        },
    )


def _admit(controller: AutonomyController, user_id: str, prompt: str):
    turn_id = _hook_turn(controller.db, user_id, prompt)
    goal = admit_explicit_goal_from_turn(
        controller,
        user_id=user_id,
        session_id=f"session:{user_id}",
        source_turn_id=turn_id,
        prompt=prompt,
    )
    assert goal is not None
    return goal, turn_id


def test_only_explicit_goal_turn_is_admitted(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        turn_id = _hook_turn(db, "gabriel", "please improve the artifact")
        result = admit_explicit_goal_from_turn(
            controller,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt="please improve the artifact",
        )
        assert result is None
        assert controller.snapshot(user_id="gabriel")["goals"] == []
    finally:
        db.close()


def test_explicit_goal_is_bound_to_exact_hook_turn_and_is_idempotent(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        prompt = "/goal ship the verified artifact"
        turn_id = _hook_turn(db, "gabriel", prompt)
        first = admit_explicit_goal_from_turn(
            controller,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt=prompt,
        )
        second = admit_explicit_goal_from_turn(
            controller,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=turn_id,
            prompt=prompt,
        )
        assert first is not None
        assert second is not None
        assert first["goal_id"] == second["goal_id"]
        assert first["source_turn_id"] == turn_id
        assert first["completion_contract"]["mode"] == "user_ack"
        assert len(controller.snapshot(user_id="gabriel")["goals"]) == 1
    finally:
        db.close()


def test_forged_non_hook_user_turn_cannot_admit_goal(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        prompt = "/goal forged objective"
        turn_id = db.append_turn(
            "session:gabriel",
            "gabriel",
            "user",
            prompt,
            provenance={"source": "synthetic-test", "entity_generation": db.entity_generation()},
        )
        with pytest.raises(PermissionError):
            admit_explicit_goal_from_turn(
                controller,
                user_id="gabriel",
                session_id="session:gabriel",
                source_turn_id=turn_id,
                prompt=prompt,
            )
        assert controller.snapshot(user_id="gabriel")["goals"] == []
    finally:
        db.close()


def test_model_visible_goal_context_is_perspective_scoped(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        gabriel, _ = _admit(controller, "gabriel", "/goal gabriel private objective")
        andreas, _ = _admit(controller, "andreas", "/goal andreas private objective")

        context = grounded_autonomy_context(controller, user_id="gabriel")
        ids = {goal["goal_id"] for goal in context["goals"]}
        rendered = repr(context)
        assert gabriel["goal_id"] in ids
        assert andreas["goal_id"] not in ids
        assert "gabriel private objective" in rendered
        assert "andreas private objective" not in rendered
        assert context["truth_boundary"]["identity_text_grants_capability"] is False
        assert context["truth_boundary"]["model_completion_is_goal_completion"] is False
    finally:
        db.close()


def test_safe_pending_goal_survives_generation_advance(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal, _ = _admit(controller, "gabriel", "/goal continue after restart")
        previous = db.entity_generation()
        live = db.advance_entity_generation()

        result = recover_autonomy_after_generation_advance(
            controller,
            previous_generation=previous,
            live_generation=live,
        )
        recovered = controller.snapshot(user_id="gabriel")["goals"][0]
        assert result["rebased"] == 1
        assert recovered["goal_id"] == goal["goal_id"]
        assert recovered["generation"] == live
        assert recovered["status"] == "ACTIVE"
        assert controller.next_runnable(user_id="gabriel")["goal_id"] == goal["goal_id"]
    finally:
        db.close()


def test_proposed_but_unadmitted_step_is_retired_not_executed_after_restart(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal, _ = _admit(controller, "gabriel", "/goal replan safely")
        step = controller.propose_step(goal["goal_id"], "reason", "candidate plan")
        assert step["status"] == "PROPOSED"
        previous = db.entity_generation()
        live = db.advance_entity_generation()

        result = recover_autonomy_after_generation_advance(
            controller,
            previous_generation=previous,
            live_generation=live,
        )
        recovered = controller.snapshot(user_id="gabriel")["goals"][0]
        assert result["proposals_retired"] == 1
        assert recovered["current_step"]["status"] == "FAILED"
        assert recovered["status"] == "ACTIVE"
        assert recovered["blocked_reason"] == "restart_before_step_admission"
    finally:
        db.close()


def test_admitted_inflight_step_becomes_unknown_blocked_after_restart(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal, _ = _admit(controller, "gabriel", "/goal never blind replay")
        step = controller.propose_step(goal["goal_id"], "reason", "work unit")
        controller.admit_step(goal["goal_id"], step["step_id"])
        previous = db.entity_generation()
        live = db.advance_entity_generation()

        result = recover_autonomy_after_generation_advance(
            controller,
            previous_generation=previous,
            live_generation=live,
        )
        recovered = controller.snapshot(user_id="gabriel")["goals"][0]
        assert result["blocked_inflight_unknown"] == 1
        assert recovered["generation"] == live
        assert recovered["status"] == "BLOCKED"
        assert recovered["current_step"]["status"] == "ADMITTED"
        assert recovered["blocked_reason"] == "UNKNOWN_AFTER_RESTART:admitted_step_interrupted"
        assert controller.next_runnable(user_id="gabriel") is None
    finally:
        db.close()


def test_prior_effect_evidence_is_not_silently_reinterpreted_after_restart(tmp_path):
    db = _db(tmp_path)
    try:
        controller = AutonomyController(db)
        goal, _ = _admit(controller, "gabriel", "/goal effect evidence review")
        with db.tx() as sql:
            state = controller._load(sql)
            stored = state["goals"][goal["goal_id"]]
            stored["evidence_effect_ids"].append("effect:verified-before-restart")
            controller._save(sql, state)
        previous = db.entity_generation()
        live = db.advance_entity_generation()

        result = recover_autonomy_after_generation_advance(
            controller,
            previous_generation=previous,
            live_generation=live,
        )
        recovered = controller.snapshot(user_id="gabriel")["goals"][0]
        assert result["blocked_prior_effect_evidence"] == 1
        assert recovered["status"] == "BLOCKED"
        assert recovered["blocked_reason"] == "REVIEW_AFTER_RESTART:prior_effect_evidence_generation_changed"
    finally:
        db.close()
