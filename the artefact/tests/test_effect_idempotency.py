import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseEffectBridge
from clayverse.store import UnifiedDB


class FakeBridge:
    sha256 = "a" * 64

    def __init__(self, *, die=False):
        self.calls = 0
        self.die = die

    def run(self, argv):
        self.calls += 1
        if self.die:
            raise SystemExit(99)
        return {"ok": True, "exit": 0, "stdout": "live", "stderr": ""}


def setup(tmp_path, bridge=None):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    return db, uid, sid, EffectGate(db, entityos_bridge=bridge)


def test_exact_retry_reuses_verified_receipt_without_second_entityos_execution(tmp_path):
    bridge = FakeBridge()
    db, uid, sid, gate = setup(tmp_path, bridge)
    req = EffectRequest(uid, sid, "entityos.exec", "status", ["status"], request_key="web:gabriel:req-1:effect:0")
    effect1, out1 = gate.execute(req)
    effect2, out2 = gate.execute(req)
    assert effect1 == effect2
    assert bridge.calls == 1
    assert out1["stdout"] == "live"
    assert out2["ok"] is True and out2["replayed"] is True
    assert "stdout" not in out2
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_consumed_collision_regression_same_key_different_intent_fails_closed(tmp_path):
    # Regression of this go's already-consumed EFFECT_ID_INTENT_COLLISION experiment.
    # No second unusual intervention is introduced here.
    bridge = FakeBridge()
    db, uid, sid, gate = setup(tmp_path, bridge)
    key = "web:gabriel:req-collision:effect:0"
    gate.execute(EffectRequest(uid, sid, "entityos.exec", "first", ["status"], request_key=key))
    with pytest.raises(RuntimeError, match="EFFECT_REQUEST_CONFLICT"):
        gate.execute(EffectRequest(uid, sid, "entityos.exec", "second", ["different"], request_key=key))
    assert bridge.calls == 1
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_restart_unknown_outcome_blocks_same_request_reexecution(tmp_path):
    dying = FakeBridge(die=True)
    db, uid, sid, gate = setup(tmp_path, dying)
    req = EffectRequest(uid, sid, "entityos.exec", "status", ["status"], request_key="web:gabriel:req-crash:effect:0")
    with pytest.raises(SystemExit):
        gate.execute(req)
    assert dying.calls == 1
    assert db.db.execute("SELECT status FROM effects").fetchone()[0] == "PENDING"
    db.close()

    healthy = FakeBridge()
    db = UnifiedDB(tmp_path / "unified.db")
    gate = EffectGate(db, entityos_bridge=healthy)
    assert db.db.execute("SELECT status FROM effects").fetchone()[0] == "UNKNOWN_AFTER_RESTART"
    with pytest.raises(RuntimeError, match="EFFECT_REEXECUTION_BLOCKED:UNKNOWN_AFTER_RESTART"):
        gate.execute(req)
    assert healthy.calls == 0
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_denied_retry_reuses_denial_receipt_without_new_effect(tmp_path):
    db, uid, sid, gate = setup(tmp_path, None)
    req = EffectRequest(uid, sid, "entityos.exec", "status", ["status"], request_key="web:gabriel:req-denied:effect:0")
    effect1, out1 = gate.execute(req)
    effect2, out2 = gate.execute(req)
    assert effect1 == effect2
    assert out1["denied"] is True
    assert out2["denied"] is True and out2["replayed"] is True
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
    db.close()


def test_mcp_key_is_deterministic_for_same_turn_and_intent():
    active = {"observation_turn_id": "turn-123"}
    key1 = ClayVerseEffectBridge._request_key(active, "entityos.exec", "status", ["status"])
    key2 = ClayVerseEffectBridge._request_key(active, "entityos.exec", "status", ["status"])
    key3 = ClayVerseEffectBridge._request_key(active, "entityos.exec", "status", ["different"])
    assert key1 == key2
    assert key1 != key3
    assert key1.startswith("mcp:turn-123:")


def test_schema_upgrade_exposes_unique_request_identity(tmp_path):
    db, _, _, _ = setup(tmp_path)
    columns = {row[1] for row in db.db.execute("PRAGMA table_info(effects)")}
    assert {"request_key", "request_hash"} <= columns
    assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "4"
    db.close()
