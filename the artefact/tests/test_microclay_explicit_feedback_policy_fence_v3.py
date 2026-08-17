import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_explicit_feedback_requires_exact_admitted_policy_v3(tmp_path, monkeypatch):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        target_memory_id = db.add_memory(
            "fact",
            "topic:orchid",
            "orchid procedure",
            None,
            None,
            {"source": "explicit-feedback-policy-fence-test"},
        )
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = lifecycle.begin("codename")
        row = db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (begun["causal_id"],),
        ).fetchone()
        assert row is not None
        assert int(row["policy_version"]) == 3
        assert json.loads(row["selected_memory_ids"]) == []

        monkeypatch.setattr(MicroClayRetrieval, "POLICY_VERSION", 4)
        with pytest.raises(StaleGeneration, match="retrieval_feedback_policy_version"):
            MicroClayExplicitFeedback(db).apply(
                retrieval_id=row["retrieval_id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                turn_id=row["turn_id"],
                episode_id=row["episode_id"],
                causal_id=row["causal_id"],
                generation=int(row["generation"]),
                query_sha256=row["query_hash"],
                budget_chars=int(row["budget_chars"]),
                limit_items=int(row["limit_items"]),
                feedback_class="USER_MISS_TARGET",
                source="USER_EXPLICIT",
                target_memory_id=target_memory_id,
            )

        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        cue_hash = "0123456789abcdef"
        with pytest.raises(StaleGeneration, match="retrieval_feedback_policy_version"):
            MicroClayExplicitFeedback._route_key(
                "gabriel", cue_hash, target_memory_id
            )
    finally:
        db.close()
