import os
import subprocess

import pytest

from clayverse.entityos_bridge import EntityOSBridge, EntityOSOutcomeUnknown
from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


class _TimeoutBridge:
    sha256 = "0" * 64

    def __init__(self):
        self.calls = 0

    def run(self, argv):
        self.calls += 1
        raise EntityOSOutcomeUnknown("post-start outcome uncertain")


def test_entityos_bridge_types_post_start_timeout_as_unknown(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.close(write_fd)

    def fake_open_verified(self):
        return read_fd

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["EntityOS", "noop"], timeout=0.01)

    monkeypatch.setattr(EntityOSBridge, "_open_verified", fake_open_verified)
    monkeypatch.setattr(subprocess, "run", fake_run)
    bridge = EntityOSBridge(path="/ignored", sha256="0" * 64, timeout=0.01)

    with pytest.raises(EntityOSOutcomeUnknown, match="external outcome is uncertain"):
        bridge.run(["noop"])

    with pytest.raises(OSError):
        os.fstat(read_fd)


def test_timeout_stays_pending_and_retry_does_not_execute_twice(tmp_path):
    db = _db(tmp_path)
    try:
        bridge = _TimeoutBridge()
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        life.effects.entityos_bridge = bridge
        turn = life.begin("run the admitted EntityOS effect")

        with pytest.raises(EntityOSOutcomeUnknown):
            life.request_effect("entityos.exec", "timeout-test", ["noop"])

        effect = db.db.execute(
            "SELECT effect_id,status,outcome FROM effects WHERE episode_id=?",
            (turn["episode_id"],),
        ).fetchone()
        assert effect is not None
        assert effect["status"] == "PENDING"
        assert effect["outcome"] is None
        assert db.db.execute(
            "SELECT COUNT(*) FROM causal_episodes WHERE effect_id=?", (effect["effect_id"],)
        ).fetchone()[0] == 0
        assert bridge.calls == 1

        with pytest.raises(TurnLifecycleError, match="effect outcome pending"):
            life.request_effect("entityos.exec", "timeout-test", ["noop"])
        assert bridge.calls == 1
    finally:
        db.close()


def test_recovery_converts_ambiguous_timeout_to_unknown_without_replay(tmp_path):
    db = _db(tmp_path)
    try:
        bridge = _TimeoutBridge()
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        life.effects.entityos_bridge = bridge
        turn = life.begin("run the admitted EntityOS effect")
        generation_before = turn["generation"]

        with pytest.raises(EntityOSOutcomeUnknown):
            life.request_effect("entityos.exec", "timeout-test", ["noop"])
        assert bridge.calls == 1

        recovery = recover_incomplete_episodes(db)
        assert bridge.calls == 1
        assert recovery["generation"] > generation_before
        assert db.db.execute(
            "SELECT COUNT(*) FROM active_turns WHERE session_id='session:gabriel'"
        ).fetchone()[0] == 0

        effect = db.db.execute(
            "SELECT effect_id,status,outcome FROM effects WHERE episode_id=?",
            (turn["episode_id"],),
        ).fetchone()
        assert effect["status"] == "UNKNOWN_AFTER_RESTART"
        assert '"certainty":"unknown"' in effect["outcome"]
        assert '"reason":"restart_before_verified_outcome"' in effect["outcome"]

        causal = db.db.execute(
            "SELECT causal_id,credit,reentered FROM causal_episodes WHERE effect_id=?",
            (effect["effect_id"],),
        ).fetchone()
        assert causal is not None
        assert causal["causal_id"] == turn["causal_id"]
        assert float(causal["credit"]) == 0.0
        assert int(causal["reentered"]) == 1
    finally:
        db.close()
