from __future__ import annotations

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB


class _Bridge:
    sha256 = "a" * 64

    def __init__(self):
        self.called = False

    def run(self, argv):
        self.called = True
        return {"ok": True, "exit": 0}


def test_lease_rechecked_transactionally_before_pending_and_external_execution(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    lease = db.acquire_lease("repo:main", "worker", ttl=60)
    bridge = _Bridge()
    gate = EffectGate(db, entityos_bridge=bridge)
    original_assert = db.assert_lease

    def assert_then_replace(current):
        original_assert(current)
        db.db.execute(
            "UPDATE leases SET generation=generation+1, nonce='replacement' WHERE resource=?",
            (current.resource,),
        )

    monkeypatch.setattr(db, "assert_lease", assert_then_replace)

    # entityos.exec no longer accepts a caller-supplied lease at all (EffectGate
    # auto-leases it internally, see effects.py commit 18041d730 "forbid caller
    # EntityOS lease bypass"). state.noop still accepts one and exercises the
    # exact same transactional-recheck path this test is about.
    with pytest.raises(StaleGeneration):
        gate.execute(
            EffectRequest(uid, sid, "state.noop", "transport", None),
            lease=lease,
        )

    assert bridge.called is False
    assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
    db.close()
