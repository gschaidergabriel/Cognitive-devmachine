import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_abort_rejects_pre_recovery_generation_without_canonicalizing_failure(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
        lifecycle = TurnLifecycle(db, uid, sid)
        admission = lifecycle.begin("request before stale StopFailure")
        assert admission["generation"] == 1

        assert db.advance_entity_generation() == 2

        with pytest.raises(StaleGeneration):
            lifecycle.abort("claude_stop_failure:stale failure")

        rows = db.db.execute(
            "SELECT role,content FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [(row["role"], row["content"]) for row in rows] == [
            ("user", "request before stale StopFailure")
        ]
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
        assert lifecycle.active() is not None
        assert db.session_generation(sid) == db.entity_generation() == 2
    finally:
        db.close()
