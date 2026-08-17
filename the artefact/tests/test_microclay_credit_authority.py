import json

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            "credit-memory",
            "fact",
            "procedure:orchid",
            "orchid verified procedure",
            None,
            "gabriel",
            100.0,
            json.dumps({"source": "test"}),
        ),
    )


def test_credit_without_causal_effect_outcome_fails_closed(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("orchid verified procedure")
        organ = MicroClayRetrieval(db)

        before = db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0]
        forged = organ.credit(
            causal_id=turn["causal_id"],
            generation=turn["generation"],
            credit=0.75,
            signal_class="verified-test",
            receipt_id="forged-receipt",
        )
        after = db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0]

        assert forged == {"applied": False, "reason": "unverified_outcome"}
        assert before == after == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()


def test_only_exact_reentered_effect_outcome_can_credit_once(tmp_path):
    db = _db(tmp_path)
    try:
        _add(db)
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        turn = life.begin("orchid verified procedure")
        effect = life.request_effect("state.noop", "credit-authority-test")
        assert effect["verified"] is True
        life.complete("done")

        organ = MicroClayRetrieval(db)
        causal = db.db.execute(
            "SELECT c.credit,e.status FROM causal_episodes c JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE c.causal_id=? AND c.reentered=1",
            (turn["causal_id"],),
        ).fetchone()
        assert causal is not None
        expected_signal = f"effect_outcome:{causal['status']}"
        expected_credit = float(causal["credit"])

        bad_signal = organ.credit(
            causal_id=turn["causal_id"], generation=turn["generation"],
            credit=expected_credit, signal_class="verified-test",
        )
        bad_value = organ.credit(
            causal_id=turn["causal_id"], generation=turn["generation"],
            credit=-1.0 if expected_credit >= 0.0 else 1.0, signal_class=expected_signal,
        )
        bad_receipt = organ.credit(
            causal_id=turn["causal_id"], generation=turn["generation"],
            credit=expected_credit, signal_class=expected_signal, receipt_id="attacker-chosen",
        )
        assert bad_signal["reason"] == "outcome_claim_mismatch"
        assert bad_value["reason"] == "outcome_claim_mismatch"
        assert bad_receipt["reason"] == "receipt_identity_mismatch"
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0

        accepted = organ.credit(
            causal_id=turn["causal_id"], generation=turn["generation"],
            credit=expected_credit, signal_class=expected_signal,
        )
        replay = organ.credit(
            causal_id=turn["causal_id"], generation=turn["generation"],
            credit=expected_credit, signal_class=expected_signal,
        )
        assert accepted["applied"] is True
        assert replay["applied"] is False and replay["reason"] == "duplicate_receipt"
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 1
    finally:
        db.close()
