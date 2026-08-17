import subprocess
import sys

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def bound(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    return db, uid, sid


def test_exact_retry_returns_same_effect_without_second_execution(tmp_path):
    db, uid, sid = bound(tmp_path)
    gate = EffectGate(db, allow_process=True)
    req = EffectRequest(
        uid,
        sid,
        "process.exec",
        "echo",
        ["/bin/echo", "once"],
        request_key="gabriel:req-idempotent:effect:0",
    )
    eid1, out1 = gate.execute(req)
    eid2, out2 = gate.execute(req)
    assert eid1 == eid2
    assert out1 == out2
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1
    db.close()


def test_consumed_unusual_collision_regression_blocks_second_intent(tmp_path):
    # Regression of this go's already-consumed EFFECT_ID_INTENT_COLLISION
    # experiment. It is not a second unusual intervention.
    db, uid, sid = bound(tmp_path)
    gate = EffectGate(db, allow_process=True)
    key = "gabriel:req-collision:effect:0"
    gate.execute(
        EffectRequest(
            uid,
            sid,
            "process.exec",
            "echo",
            ["/bin/echo", "first"],
            request_key=key,
        )
    )
    marker = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="EFFECT_REQUEST_CONFLICT"):
        gate.execute(
            EffectRequest(
                uid,
                sid,
                "process.exec",
                "different-intent",
                [sys.executable, "-c", f"open({str(marker)!r},'w').write('BAD')"],
                request_key=key,
            )
        )
    assert not marker.exists()
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1
    db.close()


def test_process_death_leaves_pending_and_restart_refuses_replay(tmp_path, monkeypatch):
    db, uid, sid = bound(tmp_path)
    req = EffectRequest(
        uid,
        sid,
        "process.exec",
        "echo",
        ["/bin/echo", "once"],
        request_key="gabriel:req-crash-window:effect:0",
    )
    gate = EffectGate(db, allow_process=True)

    def simulated_process_death(*args, **kwargs):
        raise SystemExit(99)

    monkeypatch.setattr(subprocess, "run", simulated_process_death)
    with pytest.raises(SystemExit):
        gate.execute(req)
    assert db.db.execute("select status from effects").fetchone()[0] == "PENDING"
    db.close()

    db = UnifiedDB(tmp_path / "unified.db")
    gate = EffectGate(db, allow_process=True)
    with pytest.raises(RuntimeError, match="EFFECT_RECOVERY_REQUIRED"):
        gate.execute(req)
    assert db.db.execute("select count(*) from effects").fetchone()[0] == 1
    db.close()
