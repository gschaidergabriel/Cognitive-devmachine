from __future__ import annotations

import time

import pytest

from clayverse.effects import EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


class _Bridge:
    sha256 = "a" * 64

    def __init__(self):
        self.calls = 0

    def run(self, argv):
        self.calls += 1
        return {"ok": True, "exit": 0}


def _selected_effect_turn(db: UnifiedDB, lifecycle: TurnLifecycle) -> dict:
    turn = lifecycle.begin("effect predecessor")
    with db.tx() as sql:
        lifecycle.workspace.select_in_tx(turn["episode_id"], "request_effect")
        sql.execute(
            "UPDATE active_turns SET workspace_selected=1 WHERE session_id=? AND causal_id=?",
            (lifecycle.session_id, turn["causal_id"]),
        )
    return turn


def test_retired_predecessor_cannot_start_external_effect(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    bridge = _Bridge()
    lifecycle = TurnLifecycle(db, uid, sid, entityos_bridge=bridge)
    predecessor = _selected_effect_turn(db, lifecycle)

    successor = lifecycle.begin("successor")
    assert successor["episode_id"] != predecessor["episode_id"]

    request = EffectRequest(uid, sid, "entityos.exec", "transport", ["hello"], db.entity_generation())
    with pytest.raises(StaleGeneration, match="effect_active_turn"):
        lifecycle.effects.execute(request, predecessor["episode_id"])

    assert bridge.calls == 0
    assert db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE episode_id=?", (predecessor["episode_id"],)
    ).fetchone()[0] == 0
    assert lifecycle.active()["episode_id"] == successor["episode_id"]
    db.close()


def test_foreign_causal_row_cannot_reach_external_effect(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    bridge = _Bridge()
    lifecycle = TurnLifecycle(db, uid, sid, entityos_bridge=bridge)
    predecessor = _selected_effect_turn(db, lifecycle)

    db.db.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
        "VALUES(?,?,?,?,?,0,1,?)",
        ("causal-foreign", predecessor["episode_id"], None, predecessor["turn_id"], "0" * 64, time.time()),
    )

    request = EffectRequest(uid, sid, "entityos.exec", "transport", ["hello"], db.entity_generation())
    with pytest.raises(StaleGeneration, match="effect_causal_spine"):
        lifecycle.effects.execute(request, predecessor["episode_id"])

    assert bridge.calls == 0
    assert db.db.execute(
        "SELECT COUNT(*) FROM effects WHERE episode_id=?", (predecessor["episode_id"],)
    ).fetchone()[0] == 0
    assert lifecycle.active()["episode_id"] == predecessor["episode_id"]
    db.close()


def test_pending_journal_linearizes_before_successor_abort(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    lifecycle = TurnLifecycle(db, uid, sid)
    predecessor = _selected_effect_turn(db, lifecycle)

    effect_id = lifecycle.effects.journal.begin(
        predecessor["episode_id"],
        sid,
        uid,
        "state.noop",
        "linearization-test",
        predecessor["generation"],
    )

    with pytest.raises(TurnLifecycleError, match="pending"):
        lifecycle.begin("successor")

    active = lifecycle.active()
    assert active is not None and active["episode_id"] == predecessor["episode_id"]
    assert db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()[0] == "PENDING"
    db.close()
