import json

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.recovery import recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "d" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add_memory(db):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) VALUES(?,?,?,?,?,?,?,?)",
        ("restart-learning-memory", "fact", "procedure:orchid", "orchid verified procedure", None, "gabriel", 100.0, json.dumps({"source": "test"})),
    )


def test_restart_drains_verified_rewarding_retrieval_learning_before_generation_advance(tmp_path):
    db = _db(tmp_path)
    try:
        _add_memory(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge())
        turn = life.begin("orchid verified procedure")
        retrieval = db.db.execute(
            "SELECT retrieval_id,generation FROM retrieval_episodes WHERE causal_id=?", (turn["causal_id"],)
        ).fetchone()
        assert retrieval is not None
        effect = life.request_effect("entityos.exec", "restart-learning", ["verified"])
        assert effect["verified"] is True
        assert life.complete("done")["completed"] is True
        causal_credit = db.db.execute(
            "SELECT credit FROM causal_episodes WHERE causal_id=?", (turn["causal_id"],)
        ).fetchone()[0]
        assert float(causal_credit) == 1.0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        old_generation = db.entity_generation()
        recovered = recover_incomplete_episodes(db)
        assert recovered["retrieval_learning_eligible"] == 1
        assert recovered["retrieval_learning_applied"] == 1
        assert recovered["retrieval_learning_uncertain_ignored"] == 0
        assert recovered["generation"] == old_generation + 1
        feedback = db.db.execute(
            "SELECT generation,credit,signal_class FROM retrieval_feedback WHERE retrieval_id=?", (retrieval["retrieval_id"],)
        ).fetchone()
        assert dict(feedback) == {
            "generation": old_generation,
            "credit": 1.0,
            "signal_class": "effect_outcome:VERIFIED",
        }
        pulls = db.db.execute("SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy").fetchone()[0]
        assert pulls > 0
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'v3:user:gabriel:%'"
        ).fetchone()[0] > 0

        again = recover_incomplete_episodes(db)
        assert again["retrieval_learning_eligible"] == 0
        assert again["retrieval_learning_applied"] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1
        assert db.db.execute("SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy").fetchone()[0] == pulls
    finally:
        db.close()


def test_restart_unknown_or_nonrewarding_effect_is_not_retrieval_learning(tmp_path):
    db = _db(tmp_path)
    try:
        _add_memory(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("orchid verified procedure")
        assert db.db.execute(
            "SELECT retrieval_id FROM retrieval_episodes WHERE causal_id=?", (turn["causal_id"],)
        ).fetchone() is not None

        journal = EffectJournal(db)
        effect_id = journal.begin(
            turn["episode_id"], "session:gabriel", "gabriel", "state.noop",
            "restart-unknown", db.entity_generation(),
        )
        recovered = recover_incomplete_episodes(db)
        assert db.db.execute("SELECT status FROM effects WHERE effect_id=?", (effect_id,)).fetchone()[0] == "UNKNOWN_AFTER_RESTART"
        assert recovered["retrieval_learning_eligible"] == 0
        assert recovered["retrieval_learning_applied"] == 0
        assert recovered["retrieval_learning_uncertain_ignored"] == 1
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
    finally:
        db.close()
