import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "a" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject="topic:test", user_id="gabriel", ts=100.0):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def test_product_turn_retrieval_is_query_sensitive_not_latest_n(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "old-match", "orchid launch code", ts=1.0)
        _add(db, "new-noise", "completely unrelated bicycle note", ts=999.0)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("where is the orchid launch code")
        values = [m["value"] for m in result["context"]["durable_memory"]]
        assert values and values[0] == "orchid launch code"
        assert "completely unrelated bicycle note" not in values
        assert result["context"]["retrieval_receipt"]["status"] == "PRESENT"
        life.abort("test-end")
    finally:
        db.close()


def test_no_matching_cue_is_unknown_not_recent_memory_guess(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "noise", "bicycle violet", ts=999.0)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("quantum pineapple")
        assert result["context"]["durable_memory"] == []
        receipt = result["context"]["retrieval_receipt"]
        assert receipt["status"] == "UNKNOWN"
        assert receipt["selected_count"] == 0
        life.abort("test-end")
    finally:
        db.close()


def test_current_prompt_explicit_extraction_does_not_echo_back_as_retrieval(tmp_path):
    db = _db(tmp_path)
    try:
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("FACT: unique-current-cue")
        assert db.db.execute(
            "SELECT COUNT(*) FROM durable_memory WHERE source_turn_id=? AND value='unique-current-cue'",
            (result["turn_id"],),
        ).fetchone()[0] == 1
        assert all(m["value"] != "unique-current-cue" for m in result["context"]["durable_memory"])
        life.abort("test-end")
    finally:
        db.close()


def test_shadow_learning_cannot_change_served_order(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "a", "alpha beta", subject="route:a", ts=100.0)
        _add(db, "b", "alpha beta", subject="route:b", ts=100.0)
        # Baseline tie resolves by memory_id descending -> b, a. Make the adaptive
        # policy strongly prefer a; SHADOW must still serve b, a.
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) VALUES(?,?,?,?,?)",
            ("subject:route:a", 4.0, 1.0, 10, 1.0),
        )
        db.db.execute(
            "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) VALUES(?,?,?,?,?)",
            ("subject:route:b", -2.0, -1.0, 10, 1.0),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("alpha beta")
        served = [m["memory_id"] for m in result["context"]["durable_memory"]]
        receipt_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids,mode FROM retrieval_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert receipt_row["mode"] == "SHADOW"
        assert served[:2] == ["b", "a"]
        assert json.loads(receipt_row["selected_memory_ids"])[:2] == ["b", "a"]
        assert json.loads(receipt_row["shadow_memory_ids"])[:2] == ["a", "b"]
        life.abort("test-end")
    finally:
        db.close()


def test_same_causal_query_replays_one_retrieval_receipt(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "alpha memory")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("alpha")
        organ = MicroClayRetrieval(db)
        replay = organ.retrieve(
            query="alpha",
            user_id="gabriel",
            session_id="session:gabriel",
            turn_id=result["turn_id"],
            episode_id=result["episode_id"],
            causal_id=result["causal_id"],
            generation=result["generation"],
        )
        assert replay["receipt"]["replayed"] is True
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_episodes WHERE causal_id=?", (result["causal_id"],)
        ).fetchone()[0] == 1
        with pytest.raises(StaleGeneration):
            organ.retrieve(
                query="different query",
                user_id="gabriel",
                session_id="session:gabriel",
                turn_id=result["turn_id"],
                episode_id=result["episode_id"],
                causal_id=result["causal_id"],
                generation=result["generation"],
            )
        life.abort("test-end")
    finally:
        db.close()


def test_verified_effect_outcome_updates_entrypoint_on_next_turn_only(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge())
        first = life.begin("orchid procedure")
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        effect = life.request_effect("entityos.exec", "retrieval-test", ["verified-outcome"])
        assert effect["verified"] is True
        life.complete("done")
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        second = life.begin("orchid procedure again")
        assert second["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
        feedback = db.db.execute("SELECT credit,signal_class FROM retrieval_feedback").fetchone()
        assert float(feedback["credit"]) == 1.0
        assert feedback["signal_class"] == "effect_outcome:VERIFIED"
        policy = db.db.execute(
            "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key='subject:procedure:orchid'"
        ).fetchone()
        assert policy is not None
        assert float(policy["capital"]) > 0.0
        assert int(policy["pulls"]) == 1
        life.abort("test-end")
    finally:
        db.close()


def test_state_noop_does_not_create_retrieval_feedback_or_access_rent(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        first = life.begin("orchid procedure")
        effect = life.request_effect("state.noop", "retrieval-test")
        assert effect["verified"] is True
        causal = db.db.execute(
            "SELECT credit,reentered FROM causal_episodes WHERE causal_id=?",
            (first["causal_id"],),
        ).fetchone()
        assert causal is not None
        assert int(causal["reentered"]) == 1
        assert float(causal["credit"]) == 0.0
        life.complete("done")

        second = life.begin("orchid procedure again")
        assert second["context"]["retrieval_receipt"]["outcome_learning_applied"] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        policy = db.db.execute(
            "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key='subject:procedure:orchid'"
        ).fetchone()
        assert policy is None
        life.abort("test-end")
    finally:
        db.close()


def test_feedback_is_idempotent_generation_bound_and_never_rewrites_memory(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db, "m1", "orchid procedure", subject="procedure:orchid")
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("orchid procedure")
        organ = MicroClayRetrieval(db)
        before = [tuple(r) for r in db.db.execute("SELECT * FROM durable_memory ORDER BY memory_id")]
        first = organ.credit(
            causal_id=result["causal_id"], generation=result["generation"],
            credit=0.75, signal_class="verified-test", receipt_id="receipt-fixed",
        )
        duplicate = organ.credit(
            causal_id=result["causal_id"], generation=result["generation"],
            credit=0.75, signal_class="verified-test", receipt_id="receipt-fixed",
        )
        after = [tuple(r) for r in db.db.execute("SELECT * FROM durable_memory ORDER BY memory_id")]
        assert first["applied"] is True
        assert duplicate == {"applied": False, "reason": "duplicate_receipt", "receipt_id": "receipt-fixed"}
        assert before == after
        assert first["truth_authority"] is False
        assert first["effect_authority"] is False

        db.db.execute("DELETE FROM active_turns WHERE session_id='session:gabriel'")
        db.advance_entity_generation()
        with pytest.raises(StaleGeneration):
            organ.credit(
                causal_id=result["causal_id"], generation=result["generation"],
                credit=1.0, signal_class="stale-test", receipt_id="receipt-stale",
            )
    finally:
        db.close()
