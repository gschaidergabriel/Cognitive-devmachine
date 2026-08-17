import pytest

from clayverse.engine import ClayVerseEngine
from clayverse.store import StaleGeneration, UnifiedDB


class GenerationAdvancingInference:
    def __init__(self, db):
        self.db = db

    def reason(self, world, observation):
        # Simulate Tier-2/recovery advancing the single global generation while a
        # provider request is in flight. The returned response belongs to the old
        # reasoning generation and must never become a canonical assistant turn.
        self.db.advance_entity_generation()
        return {
            "text": "stale provider response",
            "selection": "respond",
            "effect": None,
            "inference_receipt": {
                "provider": "mistral",
                "model_requested": "model-x",
                "model_returned": "model-x",
                "response_id": "stale-response",
                "finish_reason": "stop",
                "request_sha256": "1" * 64,
                "response_sha256": "2" * 64,
            },
        }


def test_provider_response_from_stale_generation_is_never_reingested(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"g": "gabriel"},
            inference=GenerationAdvancingInference(db),
        )

        with pytest.raises(StaleGeneration):
            engine.ingest("g", "hello across recovery")

        rows = db.db.execute(
            "SELECT role,content FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [(row["role"], row["content"]) for row in rows] == [
            ("user", "hello across recovery")
        ]

        workspace = db.db.execute(
            "SELECT state,selected FROM workspace_episodes"
        ).fetchone()
        assert workspace["state"] == "OPEN"
        assert workspace["selected"] is None

        assert db.db.execute("SELECT COUNT(*) FROM effects").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM causal_episodes").fetchone()[0] == 0
        assert db.session_generation("session:gabriel") == db.entity_generation() == 2
    finally:
        db.close()
