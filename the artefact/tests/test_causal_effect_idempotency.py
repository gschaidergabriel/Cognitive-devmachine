import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class FakeEntityOS:
    sha256 = "a" * 64

    def __init__(self, *, die=False):
        self.calls = 0
        self.die = die

    def run(self, argv):
        self.calls += 1
        if self.die:
            raise SystemExit(99)
        return {"ok": True, "exit": 0, "stdout": "live", "stderr": ""}


def lifecycle(tmp_path, bridge):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    return db, TurnLifecycle(db, uid, sid, entityos_bridge=bridge)


def test_same_causal_turn_reuses_verified_receipt_without_second_execution(tmp_path):
    bridge = FakeEntityOS()
    db, life = lifecycle(tmp_path, bridge)
    turn = life.begin("check status")
    first = life.request_effect("entityos.exec", "status", ["status"])
    active = life.active()
    req = life.effects.execute
    from clayverse.effects import EffectRequest
    effect2, out2 = req(
        EffectRequest(life.user_id, life.session_id, "entityos.exec", "status", ["status"], int(active["generation"])),
        turn["episode_id"],
    )
    assert effect2 == first["effect_id"]
    assert bridge.calls == 1
    assert out2["ok"] is True and out2["replayed"] is True
    assert "stdout" not in out2
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_consumed_collision_regression_same_causal_id_different_intent_conflicts(tmp_path):
    # Regression only for the EFFECT_ID_INTENT_COLLISION experiment already consumed
    # earlier in this user-triggered go; this is not a second unusual experiment.
    bridge = FakeEntityOS()
    db, life = lifecycle(tmp_path, bridge)
    turn = life.begin("one action")
    life.request_effect("entityos.exec", "first", ["status"])
    active = life.active()
    from clayverse.effects import EffectRequest
    with pytest.raises(RuntimeError, match="EFFECT_REQUEST_CONFLICT"):
        life.effects.execute(
            EffectRequest(life.user_id, life.session_id, "entityos.exec", "second", ["different"], int(active["generation"])),
            turn["episode_id"],
        )
    assert bridge.calls == 1
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_restart_unknown_outcome_blocks_causal_turn_reexecution(tmp_path):
    dying = FakeEntityOS(die=True)
    db, life = lifecycle(tmp_path, dying)
    life.begin("effect may have happened")
    with pytest.raises(SystemExit):
        life.request_effect("entityos.exec", "status", ["status"])
    assert dying.calls == 1
    assert db.db.execute("SELECT status FROM effects").fetchone()[0] == "PENDING"
    db.close()

    healthy = FakeEntityOS()
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {}).resolve("g")
    life = TurnLifecycle(db, uid, sid, entityos_bridge=healthy)
    assert db.db.execute("SELECT status FROM effects").fetchone()[0] == "UNKNOWN_AFTER_RESTART"
    with pytest.raises(RuntimeError, match="EFFECT_REEXECUTION_BLOCKED:UNKNOWN_AFTER_RESTART"):
        life.request_effect("entityos.exec", "status", ["status"])
    assert healthy.calls == 0
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_schema_has_unique_effect_request_identity(tmp_path):
    db, _ = lifecycle(tmp_path, None)
    columns = {row[1] for row in db.db.execute("PRAGMA table_info(effects)")}
    assert {"request_key", "request_hash"} <= columns
    assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "5"
    indexes = {row[1] for row in db.db.execute("PRAGMA index_list(effects)")}
    assert "idx_effects_request_key" in indexes
    db.close()
