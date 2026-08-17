import pytest

from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


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


def test_complete_rejects_stale_same_generation_provider_response_after_newer_turn(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        db.ensure_user("gabriel", "Gabriel")
        db.ensure_session("gabriel", "clay-gabriel")
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")

        old = lifecycle.begin("old provider request", source="mistral-api:request")
        newer = lifecycle.begin("new provider request", source="mistral-api:request")
        assert old["generation"] == newer["generation"] == db.entity_generation()
        assert old["causal_id"] != newer["causal_id"]

        with pytest.raises(TurnLifecycleError, match="causal identity changed"):
            lifecycle.complete(
                "late response for old request",
                source="mistral-api:response",
                provider_receipt={"provider": "mistral", "response_id": "late-old"},
                expected_causal_id=old["causal_id"],
                expected_generation=old["generation"],
            )

        active = lifecycle.active()
        assert active is not None
        assert active["causal_id"] == newer["causal_id"]
        assert db.db.execute(
            "SELECT COUNT(*) FROM turns WHERE role='assistant' AND content='late response for old request'"
        ).fetchone()[0] == 0

        completed = lifecycle.complete(
            "fresh response for new request",
            source="mistral-api:response",
            provider_receipt={"provider": "mistral", "response_id": "fresh-new"},
            expected_causal_id=newer["causal_id"],
            expected_generation=newer["generation"],
        )
        assert completed["completed"] is True
        assert completed["causal_id"] == newer["causal_id"]
    finally:
        db.close()
