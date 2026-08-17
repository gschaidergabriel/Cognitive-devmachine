import json

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_unknown_effect_cannot_train_selector_or_direct_credit(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "unknown-credit-memory",
                "fact",
                "procedure:orchid",
                "orchid verified procedure",
                None,
                "gabriel",
                100.0,
                json.dumps({"source": "test"}),
            ),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("orchid verified procedure")
        assert db.db.execute(
            "SELECT retrieval_id FROM retrieval_episodes WHERE causal_id=?",
            (turn["causal_id"],),
        ).fetchone() is not None

        # Compatibility fixture for retained effect lane #430. Its terminal
        # UNKNOWN_OUTCOME is intentionally created through the canonical journal
        # internals without requiring that separate candidate to be fused first.
        journal = EffectJournal(db)
        effect_id = journal.begin(
            turn["episode_id"],
            "session:gabriel",
            "gabriel",
            "entityos.exec",
            "unknown-after-launch",
            turn["generation"],
        )
        with db.tx() as tx:
            causal_id = journal._finish_tx(
                tx,
                effect_id,
                {"certainty": "unknown", "reason": "entityos_outcome_unknown"},
                "UNKNOWN_OUTCOME",
            )
        assert causal_id == turn["causal_id"]

        organ = MicroClayRetrieval(db)
        learned = organ.learn_from_verified_outcomes(
            session_id="session:gabriel",
            generation=turn["generation"],
        )
        assert learned == {"eligible": 0, "applied": 0}
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 0

        direct = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=0.0,
            signal_class="effect_outcome:UNKNOWN_OUTCOME",
        )
        assert direct == {"applied": False, "reason": "outcome_not_learning_eligible"}
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 0
    finally:
        db.close()
