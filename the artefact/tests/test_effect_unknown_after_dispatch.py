from __future__ import annotations

import os
import subprocess

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.entityos_bridge import EntityOSBridge, EntityOSOutcomeUnknown
from clayverse.store import UnifiedDB


class UnknownAfterDispatchBridge:
    sha256 = "a" * 64

    def __init__(self):
        self.calls = 0

    def run(self, _argv):
        self.calls += 1
        raise EntityOSOutcomeUnknown("lost return after observed process start")


class DefinitePreDispatchFailureBridge:
    sha256 = "b" * 64

    def __init__(self):
        self.calls = 0

    def run(self, _argv):
        self.calls += 1
        raise PermissionError("definite pre-dispatch failure")


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    db.ensure_user("user-1", "User One")
    session_id = db.ensure_session("user-1", "terminal-user-1")
    return db, session_id, db.session_generation(session_id)


def _request(session_id: str, generation: int) -> EffectRequest:
    return EffectRequest(
        user_id="user-1",
        session_id=session_id,
        capability="entityos.exec",
        target="candidate-zero-effect-target",
        argv=["candidate-zero-effect"],
        expected_generation=generation,
    )


def test_bridge_popen_failure_remains_pre_dispatch_error(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    bridge = EntityOSBridge("unused", "0" * 64)
    monkeypatch.setattr(EntityOSBridge, "_open_verified", lambda self: read_fd)

    def fail_before_child(*_args, **_kwargs):
        raise OSError("spawn denied before child exists")

    monkeypatch.setattr(subprocess, "Popen", fail_before_child)
    with pytest.raises(OSError, match="spawn denied before child exists"):
        bridge.run(["candidate"])


def test_bridge_timeout_after_popen_is_outcome_unknown(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    bridge = EntityOSBridge("unused", "0" * 64, timeout=0.01)
    monkeypatch.setattr(EntityOSBridge, "_open_verified", lambda self: read_fd)

    class StartedProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.waited = False

        def communicate(self, *, timeout):
            assert timeout == 0.01
            raise subprocess.TimeoutExpired(cmd="candidate", timeout=timeout)

        def kill(self):
            self.killed = True

        def wait(self, *, timeout):
            assert timeout == 1.0
            self.waited = True
            self.returncode = -9
            return self.returncode

    proc = StartedProcess()
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: proc)

    with pytest.raises(EntityOSOutcomeUnknown, match="TimeoutExpired") as caught:
        bridge.run(["candidate"])
    assert caught.value.replay_permitted is False
    assert proc.killed is True
    assert proc.waited is True


def test_gate_keeps_ambiguous_post_dispatch_outcome_pending_until_recovery(tmp_path):
    db, session_id, generation = _db(tmp_path)
    bridge = UnknownAfterDispatchBridge()
    gate = EffectGate(db, entityos_bridge=bridge)

    try:
        with pytest.raises(EntityOSOutcomeUnknown):
            gate.execute(_request(session_id, generation))

        row = db.db.execute(
            "SELECT effect_id,status,outcome FROM effects ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["status"] == "PENDING"
        assert row["outcome"] is None
        assert bridge.calls == 1

        # The automatically acquired entityos.exec lease must not survive the call.
        assert db.db.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0

        recovered = gate.journal.recover_pending()
        assert recovered == 1
        after = db.db.execute(
            "SELECT status,outcome FROM effects WHERE effect_id=?", (row["effect_id"],)
        ).fetchone()
        assert after["status"] == "UNKNOWN_AFTER_RESTART"
        assert '"certainty":"unknown"' in after["outcome"]

        causal = db.db.execute(
            "SELECT credit FROM causal_episodes WHERE effect_id=?", (row["effect_id"],)
        ).fetchone()
        assert causal is not None
        assert float(causal["credit"]) == 0.0
        assert bridge.calls == 1
    finally:
        db.close()


def test_gate_keeps_definite_pre_dispatch_failure_as_failed(tmp_path):
    db, session_id, generation = _db(tmp_path)
    bridge = DefinitePreDispatchFailureBridge()
    gate = EffectGate(db, entityos_bridge=bridge)

    try:
        with pytest.raises(PermissionError, match="definite pre-dispatch failure"):
            gate.execute(_request(session_id, generation))

        row = db.db.execute(
            "SELECT status,outcome FROM effects ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["status"] == "FAILED"
        assert "PermissionError" in row["outcome"]
        assert bridge.calls == 1
        assert db.db.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0
    finally:
        db.close()
