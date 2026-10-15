"""Regressions for definite versus uncertain EntityOS execution outcomes.

Candidate-only coverage for the retained PR #430 lane. The tests exercise no real
external effect. Most bridge execution is replaced by deterministic fakes; one focused
zero-real-effect test runs an exact local marker fixture solely to prove that the child
can cross process start before a timeout destroys outcome certainty.
"""
import hashlib
import json
import os
import subprocess

import pytest

from clayverse.effects import EffectGate, EffectRequest
from clayverse.entityos_bridge import EntityOSBridge, EntityOSOutcomeUnknown
from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class UnknownOutcomeBridge:
    sha256 = "a" * 64

    def __init__(self):
        self.calls = 0

    def run(self, argv):
        self.calls += 1
        raise EntityOSOutcomeUnknown("result channel lost after launch")


def _effect_row(db):
    return db.db.execute(
        "SELECT effect_id,status,outcome FROM effects ORDER BY ts DESC LIMIT 1"
    ).fetchone()


def test_entityos_post_launch_uncertainty_reenters_as_unknown(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    bridge = UnknownOutcomeBridge()
    gate = EffectGate(db, entityos_bridge=bridge)

    with pytest.raises(EntityOSOutcomeUnknown):
        gate.execute(EffectRequest(uid, sid, "entityos.exec", "transport", ["hello"]))

    effect = _effect_row(db)
    assert effect["status"] == "UNKNOWN_OUTCOME"
    receipt = json.loads(effect["outcome"])
    assert receipt["certainty"] == "unknown"
    assert receipt["reason"] == "entityos_outcome_unknown"
    assert receipt["error"] == "EntityOSOutcomeUnknown"
    assert "ok" not in receipt

    causal = db.db.execute(
        "SELECT credit,reentered FROM causal_episodes WHERE effect_id=?",
        (effect["effect_id"],),
    ).fetchone()
    assert causal["credit"] == 0.0
    assert causal["reentered"] == 1
    assert bridge.calls == 1
    assert db.db.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0
    db.close()


def test_entityos_bridge_popen_failure_remains_definite(monkeypatch):
    bridge = EntityOSBridge("/unused", "a" * 64, timeout=0.01)
    monkeypatch.setattr(
        EntityOSBridge,
        "_open_verified",
        lambda self: os.open("/dev/null", os.O_RDONLY),
    )

    def fail_before_child(*_args, **_kwargs):
        raise OSError("spawn denied before child exists")

    monkeypatch.setattr(subprocess, "Popen", fail_before_child)
    with pytest.raises(OSError, match="spawn denied before child exists"):
        bridge.run(["hello"])


def test_entityos_bridge_types_timeout_after_popen_as_unknown(monkeypatch):
    bridge = EntityOSBridge("/unused", "a" * 64, timeout=0.01)
    monkeypatch.setattr(
        EntityOSBridge,
        "_open_verified",
        lambda self: os.open("/dev/null", os.O_RDONLY),
    )

    class StartedProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.waited = False

        def communicate(self, *, timeout):
            assert timeout == 0.01
            raise subprocess.TimeoutExpired(cmd=["EntityOS"], timeout=timeout)

        def kill(self):
            self.killed = True

        def wait(self, *, timeout):
            assert timeout == 1.0
            self.waited = True
            self.returncode = -9
            return self.returncode

    proc = StartedProcess()
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: proc)
    with pytest.raises(EntityOSOutcomeUnknown, match="TimeoutExpired") as raised:
        bridge.run(["hello"])
    assert raised.value.replay_permitted is False
    assert proc.killed is True
    assert proc.waited is True


def test_entityos_bridge_types_other_return_path_error_after_popen_as_unknown(monkeypatch):
    bridge = EntityOSBridge("/unused", "a" * 64, timeout=0.01)
    monkeypatch.setattr(
        EntityOSBridge,
        "_open_verified",
        lambda self: os.open("/dev/null", os.O_RDONLY),
    )

    class StartedProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.waited = False

        def communicate(self, *, timeout):
            raise OSError("result channel lost")

        def kill(self):
            self.killed = True

        def wait(self, *, timeout):
            self.waited = True
            self.returncode = -9
            return self.returncode

    proc = StartedProcess()
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: proc)
    with pytest.raises(EntityOSOutcomeUnknown, match="OSError") as raised:
        bridge.run(["hello"])
    assert raised.value.replay_permitted is False
    assert proc.killed is True
    assert proc.waited is True


def test_entityos_bridge_real_harmless_child_start_then_timeout_is_unknown(tmp_path):
    """Executable falsifier: timeout can happen after the child crossed start."""

    marker = tmp_path / "marker.txt"
    fixture = tmp_path / "marker-fixture.sh"
    fixture_bytes = (
        b"#!/bin/sh\n"
        b"set -eu\n"
        b"marker=\"$1\"\n"
        b"printf 'PROCESS_STARTED\\n' > \"$marker\"\n"
        b"sleep 2\n"
        b"printf 'PROCESS_FINISHED\\n' >> \"$marker\"\n"
    )
    fixture.write_bytes(fixture_bytes)
    fixture.chmod(0o755)
    digest = hashlib.sha256(fixture_bytes).hexdigest()
    bridge = EntityOSBridge(str(fixture), digest, timeout=0.2)

    with pytest.raises(EntityOSOutcomeUnknown) as raised:
        bridge.run([str(marker)])

    assert isinstance(raised.value.__cause__, subprocess.TimeoutExpired)
    assert raised.value.replay_permitted is False
    assert marker.read_text() == "PROCESS_STARTED\n"
    assert "PROCESS_FINISHED" not in marker.read_text()


def test_entityos_pre_launch_validation_failure_remains_definite(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    gate = EffectGate(db, entityos_bridge=EntityOSBridge("/unused", "a" * 64))

    with pytest.raises(ValueError):
        gate.execute(EffectRequest(uid, sid, "entityos.exec", "bad-argv", []))

    effect = _effect_row(db)
    assert effect["status"] == "FAILED"
    receipt = json.loads(effect["outcome"])
    assert receipt["ok"] is False
    assert receipt["reason"] == "entityos_execution_failure"
    assert receipt["error"] == "ValueError"
    assert db.db.execute("SELECT COUNT(*) FROM leases").fetchone()[0] == 0
    db.close()


def test_unknown_outcome_turn_retry_rebinds_without_reexecution(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    bridge = UnknownOutcomeBridge()
    life = TurnLifecycle(db, uid, sid, entityos_bridge=bridge)
    turn = life.begin("run the admitted EntityOS effect once")

    with pytest.raises(EntityOSOutcomeUnknown):
        life.request_effect("entityos.exec", "transport", ["hello"])
    assert bridge.calls == 1

    rebound = life.request_effect("entityos.exec", "transport", ["hello"])
    assert bridge.calls == 1
    assert rebound["causal_id"] == turn["causal_id"]
    assert rebound["verified"] is False
    assert rebound["outcome"]["recovered"] is True
    assert rebound["outcome"]["replayed"] is False
    assert rebound["outcome"]["status"] == "UNKNOWN_OUTCOME"

    effect = _effect_row(db)
    assert effect["status"] == "UNKNOWN_OUTCOME"
    assert db.db.execute(
        "SELECT COUNT(*) FROM causal_episodes WHERE effect_id=?",
        (effect["effect_id"],),
    ).fetchone()[0] == 1
    db.close()


def test_unknown_outcome_remains_terminal_across_restart_recovery(tmp_path):
    path = tmp_path / "unified.db"
    db = UnifiedDB(path)
    uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
    bridge = UnknownOutcomeBridge()
    gate = EffectGate(db, entityos_bridge=bridge)

    with pytest.raises(EntityOSOutcomeUnknown):
        gate.execute(EffectRequest(uid, sid, "entityos.exec", "transport", ["hello"]))

    effect = _effect_row(db)
    effect_id = effect["effect_id"]
    assert effect["status"] == "UNKNOWN_OUTCOME"
    assert bridge.calls == 1
    db.close()

    db = UnifiedDB(path)
    recover_incomplete_episodes(db)
    effect = db.db.execute(
        "SELECT status,outcome FROM effects WHERE effect_id=?",
        (effect_id,),
    ).fetchone()
    receipt = json.loads(effect["outcome"])
    assert effect["status"] == "UNKNOWN_OUTCOME"
    assert receipt["certainty"] == "unknown"
    assert "ok" not in receipt
    assert db.db.execute(
        "SELECT COUNT(*) FROM causal_episodes WHERE effect_id=?",
        (effect_id,),
    ).fetchone()[0] == 1
    db.close()
