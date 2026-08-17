import json

import pytest

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _turn_with_effect_status(tmp_path, status):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "effect-learning-memory",
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

    # Compatibility fixture for retained effect lane #430. Journal internals create
    # the exact terminal/status shape without requiring that candidate to be fused.
    journal = EffectJournal(db)
    effect_id = journal.begin(
        turn["episode_id"],
        "session:gabriel",
        "gabriel",
        "entityos.exec",
        f"effect-{status.lower()}",
        turn["generation"],
    )
    outcome = (
        {"ok": False, "reason": "known_failure"}
        if status == "FAILED"
        else {"certainty": "unknown", "reason": "uncertain_effect"}
    )
    with db.tx() as tx:
        causal_id = journal._finish_tx(tx, effect_id, outcome, status)
    assert causal_id == turn["causal_id"]
    return db, turn


@pytest.mark.parametrize(
    "status",
    ["UNKNOWN_OUTCOME", "UNKNOWN_AFTER_RESTART", "STALE_OUTCOME", "PENDING"],
)
def test_uncertain_or_nonterminal_effect_never_trains_selector_or_direct_credit(tmp_path, status):
    db, turn = _turn_with_effect_status(tmp_path, status)
    try:
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
            signal_class=f"effect_outcome:{status}",
        )
        assert direct == {"applied": False, "reason": "outcome_not_learning_eligible"}
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute(
            "SELECT COALESCE(SUM(pulls),0) FROM retrieval_entrypoint_policy"
        ).fetchone()[0] == 0
    finally:
        db.close()


def test_known_failed_effect_remains_an_eligible_negative_learning_signal(tmp_path):
    db, turn = _turn_with_effect_status(tmp_path, "FAILED")
    try:
        learned = MicroClayRetrieval(db).learn_from_verified_outcomes(
            session_id="session:gabriel",
            generation=turn["generation"],
        )
        assert learned == {"eligible": 1, "applied": 1}
        feedback = db.db.execute(
            "SELECT credit,signal_class FROM retrieval_feedback"
        ).fetchone()
        assert float(feedback["credit"]) == 0.0
        assert feedback["signal_class"] == "effect_outcome:FAILED"
        policy = db.db.execute(
            "SELECT COALESCE(SUM(pulls),0),COALESCE(SUM(capital),0.0) FROM retrieval_entrypoint_policy"
        ).fetchone()
        assert int(policy[0]) > 0
        assert float(policy[1]) < 0.0
    finally:
        db.close()
