from __future__ import annotations

import pytest

from clayverse.autonomy import AutonomyController, AutonomyStateError
from clayverse.autonomy_context import apply_explicit_goal_command
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


@pytest.fixture
def db(tmp_path):
    instance = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(instance, {})
    yield instance
    instance.close()


def _admit_user_turn(db, user_id, prompt):
    lifecycle = TurnLifecycle(db, user_id, f"session:{user_id}")
    admitted = lifecycle.begin(prompt)
    return lifecycle, admitted


def test_explicit_goal_ack_completes_only_from_later_owner_user_turn(db):
    lifecycle, source = _admit_user_turn(db, "gabriel", "/goal finish the bounded migration")
    created = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=source["turn_id"],
        prompt="/goal finish the bounded migration",
    )
    goal_id = created["goal"]["goal_id"]
    lifecycle.complete("Goal stored")

    lifecycle, ack = _admit_user_turn(db, "gabriel", f"/goal-ack {goal_id}")
    result = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=ack["turn_id"],
        prompt=f"/goal-ack {goal_id}",
    )

    assert result["command"] == "ack"
    assert result["result"] == {
        "goal_id": goal_id,
        "status": "COMPLETED",
        "evidence": ack["turn_id"],
    }
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["status"] == "COMPLETED"
    assert stored["user_ack_turn_id"] == ack["turn_id"]
    lifecycle.complete("Acknowledged")


def test_other_user_cannot_ack_foreign_goal_even_with_exact_id(db):
    lifecycle, source = _admit_user_turn(db, "gabriel", "/goal private gabriel goal")
    created = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=source["turn_id"],
        prompt="/goal private gabriel goal",
    )
    goal_id = created["goal"]["goal_id"]
    lifecycle.complete("Stored")

    other, ack = _admit_user_turn(db, "andreas", f"/goal-ack {goal_id}")
    with pytest.raises(PermissionError, match="not owned"):
        apply_explicit_goal_command(
            db,
            user_id="andreas",
            session_id="session:andreas",
            source_turn_id=ack["turn_id"],
            prompt=f"/goal-ack {goal_id}",
        )
    assert AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]["status"] == "ACTIVE"
    other.abort("expected foreign ack rejection")


def test_owner_can_explicitly_cancel_live_goal(db):
    lifecycle, source = _admit_user_turn(db, "gabriel", "/goal cancelable work")
    created = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=source["turn_id"],
        prompt="/goal cancelable work",
    )
    goal_id = created["goal"]["goal_id"]
    lifecycle.complete("Stored")

    lifecycle, cancel = _admit_user_turn(db, "gabriel", f"/goal-cancel {goal_id}")
    result = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=cancel["turn_id"],
        prompt=f"/goal-cancel {goal_id}",
    )
    assert result["result"] == {"goal_id": goal_id, "status": "CANCELLED"}
    assert AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]["status"] == "CANCELLED"
    lifecycle.complete("Cancelled")


def test_noncanonical_goal_id_text_is_rejected_without_state_mutation(db):
    lifecycle, source = _admit_user_turn(db, "gabriel", "/goal bounded work")
    created = apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=source["turn_id"],
        prompt="/goal bounded work",
    )
    lifecycle.complete("Stored")
    before = AutonomyController(db).snapshot(user_id="gabriel")

    lifecycle, malformed = _admit_user_turn(db, "gabriel", "/goal-ack NOT-A-UUID")
    with pytest.raises(AutonomyStateError, match="canonical UUID"):
        apply_explicit_goal_command(
            db,
            user_id="gabriel",
            session_id="session:gabriel",
            source_turn_id=malformed["turn_id"],
            prompt="/goal-ack NOT-A-UUID",
        )
    after = AutonomyController(db).snapshot(user_id="gabriel")
    assert after["goals"][0]["status"] == before["goals"][0]["status"] == "ACTIVE"
    assert after["goals"][0]["user_ack_turn_id"] is None
    lifecycle.abort("expected malformed ack rejection")


def test_ordinary_language_never_becomes_goal_command(db):
    lifecycle, turn = _admit_user_turn(db, "gabriel", "I think goal abc is done")
    assert apply_explicit_goal_command(
        db,
        user_id="gabriel",
        session_id="session:gabriel",
        source_turn_id=turn["turn_id"],
        prompt="I think goal abc is done",
    ) is None
    assert AutonomyController(db).snapshot(user_id="gabriel")["goals"] == []
    lifecycle.complete("No mutation")
