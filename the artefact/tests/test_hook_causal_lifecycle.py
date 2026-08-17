import json

from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB, StaleGeneration
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.advance_entity_generation()
    return db


def test_turn_effect_and_stop_share_one_predeclared_causal_identity(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        opened = life.begin("FACT: keep causal identity\nfile:shared.py inspect it")
        active = life.active()
        assert active["causal_id"] == opened["causal_id"]
        assert int(active["generation"]) == db.entity_generation()
        assert "file:shared.py" in json.loads(active["resource_refs"])

        effect = life.request_effect("state.noop", "test:no-op")
        assert effect["verified"] is True
        assert effect["status"] == "VERIFIED"
        assert effect["causal_id"] == opened["causal_id"]
        assert db.db.execute(
            "SELECT COUNT(*) FROM causal_episodes WHERE causal_id=?", (opened["causal_id"],)
        ).fetchone()[0] == 1

        result = life.complete("done")
        assert result["causal_id"] == opened["causal_id"]
        assert result["effect_id"] == effect["effect_id"]
        assert result["reentered"] is True
        assert life.active() is None
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)
        ).fetchone()[0] == "COMPLETED"
        roles = [r[0] for r in db.db.execute(
            "SELECT role FROM turns WHERE session_id='session:gabriel' ORDER BY ordinal"
        ).fetchall()]
        assert roles[-2:] == ["user", "assistant"]
    finally:
        db.close()


def test_no_effect_stop_keeps_causal_identity_without_effect_reentry(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "andreas", "session:andreas")
        opened = life.begin("answer without effect")
        result = life.complete("answer")
        rows = db.db.execute(
            "SELECT causal_id,effect_id,outcome_hash,credit,reentered FROM causal_episodes WHERE episode_id=?",
            (opened["episode_id"],),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["causal_id"] == opened["causal_id"]
        assert rows[0]["effect_id"] is None
        assert rows[0]["outcome_hash"] is None
        assert float(rows[0]["credit"]) == 0.0
        assert int(rows[0]["reentered"]) == 0
        assert result["reentered"] is False
    finally:
        db.close()


def test_restart_closes_pending_effect_without_replay_or_false_reentry_and_advances_both_sessions(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        opened = life.begin("resource:machine-x do one effect")
        effect_id = life.effects.journal.begin(
            opened["episode_id"], "session:gabriel", "gabriel", "entityos.exec",
            "machine-x", opened["generation"], ["probe"], lease=None,
        )
        before = db.entity_generation()
        lease = db.acquire_lease("machine-x", "session:gabriel", ttl=60)

        recovered = recover_incomplete_episodes(db)
        assert recovered["generation"] == before + 1
        assert recovered["active_turns_closed"] == 1
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        effect = db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
        assert effect["status"] == "UNKNOWN_AFTER_RESTART"
        causal = db.db.execute(
            "SELECT causal_id,effect_id,credit,reentered FROM causal_episodes WHERE episode_id=?",
            (opened["episode_id"],),
        ).fetchone()
        assert causal["causal_id"] == opened["causal_id"]
        assert causal["effect_id"] == effect_id
        assert float(causal["credit"]) == 0.0
        assert int(causal["reentered"]) == 0
        assert recovered["reentered_effects"] == 0
        assert db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?", (opened["episode_id"],)
        ).fetchone()[0] == "RECOVERY_CLOSED_AFTER_EFFECT_EVIDENCE"
        assert db.session_generation("session:gabriel") == recovered["generation"]
        assert db.session_generation("session:andreas") == recovered["generation"]
        assert db.entity_generation() == recovered["generation"]
        assert db.db.execute("SELECT expires_at FROM leases WHERE resource=?", (lease.resource,)).fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM effects WHERE episode_id=?", (opened["episode_id"],)
        ).fetchone()[0] == 1
    finally:
        db.close()


def test_old_generation_effect_is_rejected_after_global_generation_advance(tmp_path):
    db = _db(tmp_path)
    try:
        old = db.entity_generation()
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        opened = life.begin("resource:r generation test")
        assert opened["generation"] == old
        db.advance_entity_generation()
        try:
            life.request_effect("state.noop", "stale")
        except StaleGeneration:
            pass
        else:
            raise AssertionError("stale generation was accepted")
        assert db.db.execute(
            "SELECT COUNT(*) FROM effects WHERE episode_id=?", (opened["episode_id"],)
        ).fetchone()[0] == 0
    finally:
        db.close()
