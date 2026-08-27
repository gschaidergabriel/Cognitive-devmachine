from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController, CompletionNotVerified
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _EntityOS:
    sha256 = "d" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "argv": list(argv or [])}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("gabriel", "Gabriel")
    db.ensure_user("andreas", "Andreas")
    db.ensure_session("gabriel", "clayverse-gabriel")
    db.ensure_session("andreas", "clayverse-andreas")
    return db


def _run_effect(db, controller, goal, target: str, argv: list[str]):
    step = controller.propose_step(
        goal["goal_id"],
        "effect",
        f"Execute {target}",
        effect={"capability": "entityos.exec", "target": target, "argv": argv},
    )
    controller.admit_step(goal["goal_id"], step["step_id"])
    lifecycle = TurnLifecycle(
        db,
        "gabriel",
        "session:gabriel",
        entityos_bridge=_EntityOS(),
    )
    lifecycle.begin_autonomous(
        f"Execute {target}", goal["goal_id"], step["step_id"]
    )
    receipt = lifecycle.request_effect("entityos.exec", target, argv)
    result = controller.record_effect_result(
        goal["goal_id"], step["step_id"], receipt["effect_id"]
    )
    lifecycle.complete_autonomous(
        f"Recorded {target}", goal["goal_id"], step["step_id"]
    )
    assert result["verified"] is True
    return step, receipt


def test_intermediate_verified_effect_does_not_complete_target_bound_goal(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Probe first, then finalize the exact target.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target="final-target",
    )

    _probe_step, probe = _run_effect(
        db, controller, goal, "probe-target", ["probe", "probe-target"]
    )
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
    snapshot = controller.snapshot(user_id="gabriel")["goals"][0]
    assert snapshot["status"] == "ACTIVE"
    assert snapshot["evidence_effect_ids"] == [probe["effect_id"]]

    final_step, final = _run_effect(
        db, controller, goal, "final-target", ["finalize", "final-target"]
    )
    assert final_step["effect"]["target"] == "final-target"
    completed = controller.verify_completion(goal["goal_id"])
    assert completed == {
        "goal_id": goal["goal_id"],
        "status": "COMPLETED",
        "evidence": final["effect_id"],
    }


def test_new_verified_effect_goal_requires_explicit_completion_target(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel", "gabriel", "user", "Do not guess my completion target."
    )
    with pytest.raises(ValueError, match="explicit completion target"):
        controller.create_goal_from_turn(
            "gabriel",
            "session:gabriel",
            source,
            completion_mode="verified_effect",
            required_capability="entityos.exec",
        )


def test_legacy_unbound_verified_effect_contract_remains_readable_but_fails_closed(tmp_path):
    db = _db(tmp_path)
    controller = AutonomyController(db)
    source = db.append_turn(
        "session:gabriel",
        "gabriel",
        "user",
        "Legacy state must not gain completion semantics after upgrade.",
    )
    goal = controller.create_goal_from_turn(
        "gabriel",
        "session:gabriel",
        source,
        completion_mode="verified_effect",
        required_capability="entityos.exec",
        required_target="legacy-target",
    )

    raw = db.db.execute(
        "SELECT value FROM meta WHERE key='autonomy_state_v1'"
    ).fetchone()[0]
    state = controller._loads(raw)
    del state["goals"][goal["goal_id"]]["completion_contract"]["required_target_sha256"]
    db.db.execute(
        "UPDATE meta SET value=? WHERE key='autonomy_state_v1'",
        (controller._dumps(state),),
    )

    readable = controller.snapshot(user_id="gabriel")["goals"][0]
    assert readable["completion_contract"] == {
        "mode": "verified_effect",
        "required_capability": "entityos.exec",
    }

    _step, receipt = _run_effect(
        db, controller, readable, "legacy-target", ["finalize", "legacy-target"]
    )
    assert receipt["verified"] is True
    with pytest.raises(CompletionNotVerified):
        controller.verify_completion(goal["goal_id"])
    assert controller.snapshot(user_id="gabriel")["goals"][0]["status"] == "ACTIVE"
