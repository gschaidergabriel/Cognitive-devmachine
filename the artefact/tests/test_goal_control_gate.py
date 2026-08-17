from __future__ import annotations

import hashlib

import pytest

from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _bridge(tmp_path, user_id="gabriel"):
    db = UnifiedDB(tmp_path / "goal-control.db")
    IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    lifecycle = TurnLifecycle(db, user_id, f"session:{user_id}", entityos_bridge=None)
    return db, lifecycle, ClayVerseEffectBridge(lifecycle)


def test_goal_create_requires_exact_quote_from_active_user_prompt(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path)
    admitted = lifecycle.begin("Please make this a durable goal: build a verified clay module.")

    with pytest.raises(PermissionError, match="not present"):
        bridge.goal_create(
            "invented authorization",
            "Build clay module",
            "Build and verify the module",
            "Acceptance tests pass",
        )

    result = bridge.goal_create(
        "make this a durable goal",
        "Build clay module",
        "Build and verify the module",
        "Acceptance tests pass",
        20,
    )
    assert result["admission_turn_id"] == admitted["turn_id"]
    assert result["status"] == "ACTIVE"
    assert len(result["milestone_ids"]) == 3

    rows = db.db.execute(
        "SELECT phase,status FROM agency_milestones WHERE goal_id=? ORDER BY created_at",
        (result["goal_id"],),
    ).fetchall()
    assert [row["phase"] for row in rows] == ["CONCEPT", "PROTOTYPE", "FINAL"]
    assert all(row["status"] == "PENDING" for row in rows)

    event = db.db.execute(
        "SELECT payload FROM agency_events WHERE event_type='agency.control_admitted' ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    assert event is not None
    expected = hashlib.sha256("make this a durable goal".encode()).hexdigest()
    assert expected in event["payload"]
    assert "Please make this" not in event["payload"]
    db.close()


def test_goal_control_is_bound_to_canonical_owner_and_current_turn(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path, "gabriel")
    lifecycle.begin("Create a goal for me: produce grounded evidence.")
    created = bridge.goal_create(
        "Create a goal for me",
        "Grounded evidence",
        "Produce reviewable grounded evidence",
        "Evidence is accepted",
    )

    # A new active turn is required for a later control decision; stale text from the
    # prior user turn is not accepted as authorization.
    lifecycle.begin("Pause that goal now.")
    with pytest.raises(PermissionError, match="not present"):
        bridge.goal_set_status("Create a goal for me", created["goal_id"], "PAUSED")
    paused = bridge.goal_set_status("Pause that goal now", created["goal_id"], "PAUSED")
    assert paused["status"] == "PAUSED"

    # Another canonical user's bridge cannot mutate this user's goal even when that
    # user's own active prompt contains a syntactically valid authorization quote.
    andreas = TurnLifecycle(db, "andreas", "session:andreas", entityos_bridge=None)
    andreas.begin("Pause that goal now.")
    other = ClayVerseEffectBridge(andreas)
    with pytest.raises(Exception, match="owner mismatch"):
        other.goal_set_status("Pause that goal now", created["goal_id"], "PAUSED")
    db.close()


def test_goal_state_is_read_only_and_user_scoped(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path, "gabriel")
    lifecycle.begin("Make this a goal: keep my private objective isolated.")
    bridge.goal_create(
        "Make this a goal",
        "Private Gabriel goal",
        "private-gabriel-objective",
        "done",
    )

    andreas = TurnLifecycle(db, "andreas", "session:andreas", entityos_bridge=None)
    other = ClayVerseEffectBridge(andreas)
    assert "private-gabriel-objective" in str(bridge.goal_state())
    assert "private-gabriel-objective" not in str(other.goal_state())
    db.close()
