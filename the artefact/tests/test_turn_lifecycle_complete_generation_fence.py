import pytest

from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_complete_rejects_active_turn_from_pre_recovery_generation(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        db.ensure_session("gabriel", "clay-gabriel")
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")

        admission = lifecycle.begin("provider request before recovery")
        assert admission["generation"] == 1
        assert lifecycle.active() is not None

        # Simulate Tier-2/recovery advancing the single global generation after
        # provider cognition but before Stop/provider completion is committed.
        assert db.advance_entity_generation() == 2

        with pytest.raises(StaleGeneration):
            lifecycle.complete(
                "stale provider response",
                source="mistral-api:response",
                provider_receipt={"provider": "mistral", "response_id": "stale-1"},
            )

        rows = db.db.execute(
            "SELECT role,content FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [(row["role"], row["content"]) for row in rows] == [
            ("user", "provider request before recovery")
        ]
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
        assert lifecycle.active() is not None
    finally:
        db.close()
