import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


class FakeEntityOS:
    sha256 = "a" * 64
    def __init__(self, *, die=False):
        self.calls = 0
        self.die = die
    def run(self, argv):
        self.calls += 1
        if self.die:
            raise SystemExit(99)
        return {"ok": True, "exit": 0, "stdout": "ok", "stderr": ""}


def bound(tmp_path, bridge):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    return db, uid, sid, EffectGate(db, entityos_bridge=bridge)


def request(uid, sid, key, argv=None, target="test"):
    return EffectRequest(uid, sid, "entityos.exec", target, argv or ["status"], request_key=key)


def test_exact_retry_returns_same_effect_without_second_entityos_call(tmp_path):
    bridge = FakeEntityOS()
    db, uid, sid, gate = bound(tmp_path, bridge)
    req = request(uid, sid, "gabriel:req-idempotent:effect:0")
    eid1, out1 = gate.execute(req)
    eid2, out2 = gate.execute(req)
    assert eid1 == eid2
    assert out1 == out2
    assert bridge.calls == 1
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1
    assert db.db.execute("select status from effect_requests").fetchone()[0] == "VERIFIED"
    db.close()


def test_consumed_unusual_collision_regression_blocks_second_entityos_intent(tmp_path):
    # Regression of this go's already-consumed EFFECT_ID_INTENT_COLLISION
    # intervention; this is not a second unusual experiment.
    bridge = FakeEntityOS()
    db, uid, sid, gate = bound(tmp_path, bridge)
    key = "gabriel:req-collision:effect:0"
    gate.execute(request(uid, sid, key, ["status"], "first"))
    with pytest.raises(RuntimeError, match="EFFECT_REQUEST_CONFLICT"):
        gate.execute(request(uid, sid, key, ["different"], "second"))
    assert bridge.calls == 1
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1
    db.close()


def test_entityos_process_death_leaves_pending_and_restart_refuses_replay(tmp_path):
    dying = FakeEntityOS(die=True)
    db, uid, sid, gate = bound(tmp_path, dying)
    req = request(uid, sid, "gabriel:req-crash-window:effect:0")
    with pytest.raises(SystemExit):
        gate.execute(req)
    assert dying.calls == 1
    assert db.db.execute("select status from effect_requests").fetchone()[0] == "PENDING"
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 0
    db.close()

    healthy = FakeEntityOS()
    db = UnifiedDB(tmp_path / "unified.db")
    gate = EffectGate(db, entityos_bridge=healthy)
    with pytest.raises(RuntimeError, match="EFFECT_RECOVERY_REQUIRED"):
        gate.execute(req)
    assert healthy.calls == 0
    assert db.db.execute("select count(*) from effect_requests").fetchone()[0] == 1
    db.close()


def test_checkpoint_binds_pending_effect_request(tmp_path):
    dying = FakeEntityOS(die=True)
    db, uid, sid, gate = bound(tmp_path, dying)
    _, before = db.checkpoint("before")
    with pytest.raises(SystemExit):
        gate.execute(request(uid, sid, "gabriel:req-checkpoint:effect:0"))
    _, after = db.checkpoint("after")
    assert before != after
    db.close()
