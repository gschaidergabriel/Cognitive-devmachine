from __future__ import annotations

import time

import pytest

from clayverse.autonomy import AutonomyController, CompletionNotVerified
from clayverse.effect_journal import EffectJournal
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _goal(db, controller, *, required_target):
    source_turn = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Finish the exact admitted target without borrowing unrelated success.",
    )
    return controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source_turn,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target=required_target,
    )


def _causal_verified_effect(db, goal, step, *, effect_id, target, argv):
    generation = db.entity_generation()
    causal_id = f"causal:{effect_id}"
    episode_id = f"episode:{effect_id}"
    observation_turn_id = db.append_turn(
        goal["session_id"],
        goal["user_id"],
        "system",
        "verified autonomous effect outcome",
        resources=[f"goal:{goal['goal_id']}", f"goal-step:{step['step_id']}"],
        provenance={
            "source": "clayverse-autonomy:goal-step",
            "goal_id": goal["goal_id"],
            "autonomy_step_id": step["step_id"],
            "entity_generation": generation,
            "causal_id": causal_id,
        },
    )
    now = time.time()
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            episode_id,
            goal["session_id"],
            now,
            observation_turn_id,
            1.0,
            "[]",
            None,
            "OPEN",
        ),
    )
    target_receipt = EffectJournal._payload(EffectJournal._target_receipt(target))
    argv_receipt = EffectJournal._argv_receipt(argv)
    argv_payload = EffectJournal._payload(argv_receipt) if argv_receipt is not None else None
    outcome = EffectJournal._payload(
        EffectJournal._outcome_receipt({"ok": True, "exit": 0})
    )
    db.db.execute(
        "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            effect_id,
            episode_id,
            goal["user_id"],
            "entityos.exec",
            target_receipt,
            argv_payload,
            generation,
            "VERIFIED",
            outcome,
            now,
            now,
        ),
    )
    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            causal_id,
            episode_id,
            effect_id,
            observation_turn_id,
            "0" * 64,
            1.0,
            1,
            now,
        ),
    )
    return effect_id


def test_exact_predeclared_target_can_complete_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller, required_target="required-final-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "execute exact completion target",
        effect={
            "capability": "entityos.exec",
            "target": "required-final-target",
            "argv": ["verify", "required-final-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _causal_verified_effect(
        db,
        goal,
        step,
        effect_id="effect:final",
        target="required-final-target",
        argv=["verify", "required-final-target"],
    )

    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)

    assert result["verified"] is True
    assert result["completion_evidence"] is True
    assert controller.verify_completion(goal["goal_id"])["evidence"] == effect_id


def test_successful_intermediate_target_is_step_success_not_goal_success(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    goal = _goal(db, controller, required_target="required-final-target")
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "perform useful intermediate work",
        effect={
            "capability": "entityos.exec",
            "target": "intermediate-target",
            "argv": ["verify", "intermediate-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _causal_verified_effect(
        db,
        goal,
        step,
        effect_id="effect:intermediate",
        target="intermediate-target",
        argv=["verify", "intermediate-target"],
    )

    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)

    assert result["verified"] is True
    assert result["completion_evidence"] is False
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])


def test_legacy_unbound_verified_effect_goal_fails_closed_on_completion(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source_turn = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Legacy-compatible verified-effect goal without a target contract.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source_turn,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
    )
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        "legacy bounded effect",
        effect={
            "capability": "entityos.exec",
            "target": "legacy-target",
            "argv": ["verify", "legacy-target"],
        },
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    effect_id = _causal_verified_effect(
        db,
        goal,
        step,
        effect_id="effect:legacy",
        target="legacy-target",
        argv=["verify", "legacy-target"],
    )

    result = controller.record_effect_result(goal["goal_id"], step["step_id"], effect_id)

    assert result["verified"] is True
    assert result["completion_evidence"] is False
    assert effect_id in controller.snapshot(user_id="gabriel")["goals"][0]["evidence_effect_ids"]
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
