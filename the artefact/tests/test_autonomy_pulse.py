from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from clayverse.autonomy import AutonomyController
from clayverse.autonomy_dispatch import DISPATCH_PREFIX
from clayverse.autonomy_pulse import AutonomyPulse
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.terminal_activity import TerminalActivityRegistry
from clayverse.terminal_sessions import TerminalRuntimeError
from clayverse.turn_lifecycle import TurnLifecycle


class _FakeTerminals:
    def __init__(self):
        self.activity = TerminalActivityRegistry()
        self.dispatched = []
        self.fail_dispatch = False
        self.safe = True

    def assert_detached_idle_claude(self, user_id):
        if not self.safe:
            raise TerminalRuntimeError("not safe")
        return SimpleNamespace(user_id=user_id, tmux_name=f"clayverse-{user_id}"), "%0"

    def _run_tmux(self, binding, *args):
        assert args[:4] == ("display-message", "-p", "-t", "%0")
        return SimpleNamespace(returncode=0, stdout=f"{os.getpid()}\n", stderr="")

    def dispatch_autonomy_prompt(self, user_id, prompt):
        if self.fail_dispatch:
            raise TerminalRuntimeError("synthetic failure")
        assert self.activity.snapshot(user_id).autonomy_reserved is True
        self.dispatched.append((user_id, prompt))


@pytest.fixture
def state_root(tmp_path):
    root = tmp_path / "state"
    root.mkdir()
    db = UnifiedDB(root / "unified.db")
    IdentityRouter(db, {})
    db.close()
    return root


def _completed_human_roundtrip(root, user_id="gabriel"):
    db = UnifiedDB(root / "unified.db")
    lifecycle = TurnLifecycle(db, user_id, f"session:{user_id}")
    lifecycle.begin("human readiness roundtrip")
    lifecycle.complete("ready")
    db.close()


def _goal(root, user_id="gabriel"):
    db = UnifiedDB(root / "unified.db")
    controller = AutonomyController(db)
    source = db.append_turn(
        f"session:{user_id}", user_id, "user", "Continue this durable background goal."
    )
    goal = controller.create_goal_from_turn(
        user_id,
        f"session:{user_id}",
        source,
        completion_mode="user_ack",
    )
    db.close()
    return goal


def test_pulse_requires_human_roundtrip_on_current_claude_process(state_root, monkeypatch):
    terminals = _FakeTerminals()
    goal = _goal(state_root)
    pulse = AutonomyPulse(state_root, terminals)
    monkeypatch.setattr(pulse, "_pane_process_start", lambda user_id: 10**12)

    result = pulse.tick_user("gabriel")

    assert result.status == "CLAUDE_RUNTIME_NOT_HUMAN_ATTESTED"
    assert terminals.dispatched == []
    db = UnifiedDB(state_root / "unified.db")
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["goal_id"] == goal["goal_id"]
    assert stored["current_step"] is None
    db.close()


def test_pulse_prepares_one_step_and_dispatches_only_one_shot_nonce(state_root, monkeypatch):
    terminals = _FakeTerminals()
    _completed_human_roundtrip(state_root)
    goal = _goal(state_root)
    pulse = AutonomyPulse(state_root, terminals)
    monkeypatch.setattr(pulse, "_pane_process_start", lambda user_id: 0.0)

    result = pulse.tick_user("gabriel")

    assert result.status == "DISPATCHED"
    assert result.goal_id == goal["goal_id"]
    assert len(terminals.dispatched) == 1
    user_id, terminal_prompt = terminals.dispatched[0]
    assert user_id == "gabriel"
    assert terminal_prompt.startswith(DISPATCH_PREFIX)
    assert "Continue this durable background goal" not in terminal_prompt
    assert terminals.activity.snapshot("gabriel").autonomy_reserved is False

    db = UnifiedDB(state_root / "unified.db")
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["status"] == "ADMITTED"
    assert stored["current_step"]["kind"] == "reason"
    lease = db.db.execute(
        "SELECT nonce FROM leases WHERE resource='autonomy-dispatch:session:gabriel'"
    ).fetchone()
    assert lease is not None
    assert terminal_prompt.endswith(lease["nonce"])
    db.close()


def test_human_activity_blocks_pulse_before_goal_or_lease_mutation(state_root, monkeypatch):
    terminals = _FakeTerminals()
    _completed_human_roundtrip(state_root)
    _goal(state_root)
    pulse = AutonomyPulse(state_root, terminals)
    monkeypatch.setattr(pulse, "_pane_process_start", lambda user_id: 0.0)
    assert terminals.activity.begin_human("gabriel") is True
    try:
        result = pulse.tick_user("gabriel")
    finally:
        terminals.activity.end_human("gabriel")

    assert result.status == "HUMAN_OR_AUTONOMY_ACTIVE"
    assert terminals.dispatched == []
    db = UnifiedDB(state_root / "unified.db")
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"] is None
    assert db.db.execute(
        "SELECT COUNT(*) FROM leases WHERE resource='autonomy-dispatch:session:gabriel'"
    ).fetchone()[0] == 0
    db.close()


def test_terminal_dispatch_failure_cancels_exact_lease_but_preserves_admitted_step(state_root, monkeypatch):
    terminals = _FakeTerminals()
    terminals.fail_dispatch = True
    _completed_human_roundtrip(state_root)
    _goal(state_root)
    pulse = AutonomyPulse(state_root, terminals)
    monkeypatch.setattr(pulse, "_pane_process_start", lambda user_id: 0.0)

    result = pulse.tick_user("gabriel")

    assert result.status == "TERMINAL_NOT_SAFE"
    assert terminals.activity.snapshot("gabriel").autonomy_reserved is False
    db = UnifiedDB(state_root / "unified.db")
    stored = AutonomyController(db).snapshot(user_id="gabriel")["goals"][0]
    assert stored["current_step"]["status"] == "ADMITTED"
    assert db.db.execute(
        "SELECT COUNT(*) FROM leases WHERE resource='autonomy-dispatch:session:gabriel'"
    ).fetchone()[0] == 0
    db.close()


def test_existing_canonical_turn_blocks_pulse_even_when_terminal_is_detached(state_root, monkeypatch):
    terminals = _FakeTerminals()
    _completed_human_roundtrip(state_root)
    _goal(state_root)
    db = UnifiedDB(state_root / "unified.db")
    active_lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
    active_lifecycle.begin("human turn still active")
    db.close()
    pulse = AutonomyPulse(state_root, terminals)
    monkeypatch.setattr(pulse, "_pane_process_start", lambda user_id: 0.0)

    result = pulse.tick_user("gabriel")

    assert result.status == "CANONICAL_TURN_ACTIVE"
    assert terminals.dispatched == []
