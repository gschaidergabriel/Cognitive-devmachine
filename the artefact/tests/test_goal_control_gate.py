from __future__ import annotations

import hashlib
import json

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


def test_goal_create_requires_exact_quote_and_copies_full_canonical_user_turn(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path)
    prompt = "Please make this a durable goal: build a verified clay module without inventing progress."
    admitted = lifecycle.begin(prompt)

    with pytest.raises(PermissionError, match="not present"):
        bridge.goal_create("invented authorization text")

    quote = "make this a durable goal"
    result = bridge.goal_create(quote, completion_mode="user_ack", priority=70)
    assert result["admission_turn_id"] == admitted["turn_id"]
    assert result["status"] == "ACTIVE"
    assert result["objective_source"] == "canonical_user_turn"

    goal = bridge.autonomy.snapshot(user_id="gabriel")["goals"][0]
    assert goal["objective"] == prompt
    assert goal["completion_contract"] == {"mode": "user_ack", "required_capability": None}

    receipt = db.db.execute(
        "SELECT content FROM turns WHERE role='system' AND provenance LIKE '%agency-gate%' ORDER BY ordinal DESC LIMIT 1"
    ).fetchone()
    payload = json.loads(receipt["content"])
    assert payload["authorization_quote_sha256"] == hashlib.sha256(quote.encode()).hexdigest()
    assert quote not in receipt["content"]
    db.close()


def test_goal_control_is_bound_to_current_turn_and_canonical_owner(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path, "gabriel")
    lifecycle.begin("Create this durable goal for me: produce grounded evidence.")
    created = bridge.goal_create("Create this durable goal")

    lifecycle.begin("Pause that durable goal now.")
    with pytest.raises(PermissionError, match="not present"):
        bridge.goal_set_status("Create this durable goal", created["goal_id"], "PAUSE")
    paused = bridge.goal_set_status("Pause that durable goal", created["goal_id"], "PAUSE")
    assert paused["status"] == "BLOCKED"
    assert paused["reason"] == "user_paused"

    lifecycle.begin("Resume that durable goal now.")
    resumed = bridge.goal_set_status("Resume that durable goal", created["goal_id"], "RESUME")
    assert resumed["status"] == "ACTIVE"

    andreas = TurnLifecycle(db, "andreas", "session:andreas", entityos_bridge=None)
    andreas.begin("Cancel that durable goal now.")
    other = ClayVerseEffectBridge(andreas)
    with pytest.raises(PermissionError, match="owner mismatch"):
        other.goal_set_status("Cancel that durable goal", created["goal_id"], "CANCEL")
    db.close()


def test_user_ack_completion_requires_fresh_owner_turn(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path)
    lifecycle.begin("Create a durable goal: prepare a result for my explicit final approval.")
    created = bridge.goal_create("Create a durable goal", completion_mode="user_ack")

    lifecycle.begin("I explicitly approve completion of that durable goal now.")
    result = bridge.goal_acknowledge("explicitly approve completion", created["goal_id"])
    assert result["verification"]["status"] == "COMPLETED"
    goal = bridge.autonomy.snapshot(user_id="gabriel")["goals"][0]
    assert goal["status"] == "COMPLETED"
    assert goal["user_ack_turn_id"] is not None
    db.close()


def test_goal_state_is_read_only_and_user_scoped(tmp_path):
    db, lifecycle, bridge = _bridge(tmp_path, "gabriel")
    prompt = "Make this a durable goal: keep private-gabriel-objective isolated from the other user."
    lifecycle.begin(prompt)
    bridge.goal_create("Make this a durable goal")

    andreas = TurnLifecycle(db, "andreas", "session:andreas", entityos_bridge=None)
    other = ClayVerseEffectBridge(andreas)
    assert "private-gabriel-objective" in str(bridge.goal_state())
    assert "private-gabriel-objective" not in str(other.goal_state())
    db.close()
