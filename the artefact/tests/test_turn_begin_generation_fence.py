import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_begin_rejects_stale_predecessor_without_retiring_it(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        uid, sid = IdentityRouter(db, {"g": "gabriel"}).resolve("g")
        lifecycle = TurnLifecycle(db, uid, sid)
        admission = lifecycle.begin("request before recovery")
        assert admission["generation"] == 1

        assert db.advance_entity_generation() == 2

        with pytest.raises(StaleGeneration):
            lifecycle.begin("new prompt while stale predecessor is still active")

        rows = db.db.execute(
            "SELECT role,content FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [(row["role"], row["content"]) for row in rows] == [
            ("user", "request before recovery")
        ]
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
        active = lifecycle.active()
        assert active is not None
        assert active["generation"] == 1
        assert db.session_generation(sid) == db.entity_generation() == 2
    finally:
        db.close()
