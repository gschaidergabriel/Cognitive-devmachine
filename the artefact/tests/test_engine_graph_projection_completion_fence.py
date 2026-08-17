from __future__ import annotations

import pytest

from clayverse.engine import ClayVerseEngine
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB


class _NoopEffectInference:
    def reason(self, world, observation):
        return {
            "text": "provider response before bounded noop",
            "selection": "request_effect",
            "effect": {
                "capability": "state.noop",
                "target": "graph-completion-fence",
                "argv": None,
            },
        }


def _raise_graph_failure():
    raise RuntimeError("graph-rebuild-failure")


def test_no_effect_graph_failure_keeps_active_turn_recoverable(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(db, {"subject-g": "gabriel", "subject-a": "andreas"})
        monkeypatch.setattr(engine.graph, "rebuild_in_tx", _raise_graph_failure)

        with pytest.raises(RuntimeError, match="graph-rebuild-failure"):
            engine.ingest("subject-g", "respond without effect")

        active = db.db.execute("SELECT * FROM active_turns").fetchone()
        assert active is not None
        workspace = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchone()
        assert workspace["selected"] is None
        assert workspace["state"] == "OPEN"
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
        assert [row[0] for row in db.db.execute("SELECT role FROM turns ORDER BY ordinal")] == ["user"]

        recovery = recover_incomplete_episodes(db)
        assert recovery["aborted_no_effect"] == 1
        assert recovery["active_turns_closed"] == 1
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
    finally:
        db.close()


def test_effect_graph_failure_preserves_reentry_and_blocks_blind_retry(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"subject-g": "gabriel", "subject-a": "andreas"},
            inference=_NoopEffectInference(),
        )
        monkeypatch.setattr(engine.graph, "rebuild_in_tx", _raise_graph_failure)

        with pytest.raises(RuntimeError, match="graph-rebuild-failure"):
            engine.ingest("subject-g", "perform one bounded noop")

        active = db.db.execute("SELECT * FROM active_turns").fetchone()
        assert active is not None
        workspace = db.db.execute(
            "SELECT selected,state FROM workspace_episodes WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchone()
        assert workspace["selected"] == "request_effect"
        assert workspace["state"] == "SELECTED"

        effects = db.db.execute(
            "SELECT effect_id,status,outcome FROM effects WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchall()
        assert len(effects) == 1
        assert effects[0]["status"] == "VERIFIED"
        assert effects[0]["outcome"] is not None
        causal = db.db.execute(
            "SELECT causal_id,effect_id,reentered FROM causal_episodes WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchone()
        assert causal is not None
        assert causal["causal_id"] == active["causal_id"]
        assert causal["effect_id"] == effects[0]["effect_id"]
        assert causal["reentered"] == 1

        # A retry cannot start while the post-effect completion fence is still active.
        with pytest.raises(RuntimeError, match="canonical session already has an active turn"):
            engine.ingest("subject-g", "retry should not duplicate the effect")
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1

        recovery = recover_incomplete_episodes(db)
        assert recovery["existing_reentries_closed"] == 0
        assert recovery["active_turns_closed"] == 1
        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 1
        assert db.db.execute("SELECT COUNT(*) FROM active_turns").fetchone()[0] == 0
        state = db.db.execute(
            "SELECT state FROM workspace_episodes WHERE episode_id=?",
            (active["episode_id"],),
        ).fetchone()[0]
        assert state == "RECOVERY_CLOSED_AFTER_EFFECT_REENTRY"
    finally:
        db.close()
