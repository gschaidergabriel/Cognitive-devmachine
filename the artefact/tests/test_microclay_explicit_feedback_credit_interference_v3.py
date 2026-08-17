import hashlib
import time

from clayverse.identity import IdentityRouter
from clayverse.microclay_feedback import MicroClayExplicitFeedback
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_explicit_miss_receipt_does_not_block_or_rewrite_verified_outcome_credit(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        target_memory_id = db.add_memory(
            "fact",
            "topic:orchid",
            "orchid procedure",
            None,
            None,
            {"source": "explicit-feedback-credit-interference-test"},
        )
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        begun = lifecycle.begin("codename")
        row = db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (begun["causal_id"],),
        ).fetchone()
        assert row is not None
        assert row["status"] == "UNKNOWN"
        assert row["entry_keys"] == "[]"

        explicit = MicroClayExplicitFeedback(db).apply(
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
        assert explicit["applied"] is True
        assert explicit["updated_entrypoints"] == 1

        cue_hash = MicroClayRetrieval._token_key("codename")[4:]
        route_key = MicroClayExplicitFeedback._route_key(
            "gabriel", cue_hash, target_memory_id
        )
        route_before = db.db.execute(
            "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert route_before is not None
        assert int(route_before["pulls"]) == 1

        effect_id = db.record_effect(
            row["episode_id"],
            "gabriel",
            "state.noop",
            "explicit-feedback-credit-interference-test",
            int(row["generation"]),
            "VERIFIED",
            outcome={"ok": True},
        )
        outcome_hash = hashlib.sha256(b'{"ok":true}').hexdigest()
        db.db.execute(
            "INSERT INTO causal_episodes("
            "causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts"
            ") VALUES(?,?,?,?,?,?,?,?)",
            (
                row["causal_id"],
                row["episode_id"],
                effect_id,
                row["turn_id"],
                outcome_hash,
                1.0,
                1,
                time.time(),
            ),
        )

        automatic = MicroClayRetrieval(db).credit(
            causal_id=row["causal_id"],
            generation=int(row["generation"]),
            credit=1.0,
            signal_class="effect_outcome:VERIFIED",
        )
        assert automatic["applied"] is True
        assert automatic["updated_entrypoints"] == 0
        assert automatic["receipt_id"] != explicit["receipt_id"]

        feedback = db.db.execute(
            "SELECT receipt_id,signal_class FROM retrieval_feedback WHERE retrieval_id=? ORDER BY ts,receipt_id",
            (row["retrieval_id"],),
        ).fetchall()
        assert len(feedback) == 2
        assert {item["signal_class"] for item in feedback} == {
            f"user_explicit:v3:user_miss_target:{target_memory_id}",
            "effect_outcome:VERIFIED",
        }

        route_after = db.db.execute(
            "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (route_key,),
        ).fetchone()
        assert route_after is not None
        assert int(route_after["pulls"]) == 1
        assert float(route_after["capital"]) == float(route_before["capital"])
        assert float(route_after["reward_ema"]) == float(route_before["reward_ema"])
    finally:
        db.close()
