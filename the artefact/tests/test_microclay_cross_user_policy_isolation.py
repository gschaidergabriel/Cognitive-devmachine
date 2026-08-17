import json

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "a" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def _add(db, memory_id, value, *, subject, user_id, ts):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def test_learned_entrypoint_capital_does_not_cross_user_perspectives(tmp_path):
    """RED GATE: one user's adaptive retrieval behavior must not retune the other's perspective.

    The durable facts remain user-filtered already. This test is stricter: Gabriel's
    outcome-backed cue->subject learning must not make an otherwise UNKNOWN Andreas
    query acquire a SHADOW candidate merely because Andreas owns a memory with the
    same subject label.
    """
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        subject = "procedure:shared-label"
        _add(db, "gabriel-memory", "orchid procedure", subject=subject, user_id="gabriel", ts=200.0)
        _add(db, "andreas-memory", "violet bicycle", subject=subject, user_id="andreas", ts=100.0)

        gabriel = TurnLifecycle(
            db,
            "gabriel",
            "session:gabriel",
            entityos_bridge=_VerifiedEffectBridge(),
        )
        first = gabriel.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["gabriel-memory"]
        effect = gabriel.request_effect("entityos.exec", "learn-private-route", ["verified-outcome"])
        assert effect["verified"] is True
        gabriel.complete("done")

        # Outcome-backed learning is consumed on Gabriel's next turn.
        learning_turn = gabriel.begin("orchid")
        assert learning_turn["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
        gabriel.abort("learning-consumed")
        learned_key = MicroClayRetrieval._route_key("codename", subject)
        assert db.db.execute(
            "SELECT capital FROM retrieval_entrypoint_policy WHERE entry_key=?",
            (learned_key,),
        ).fetchone() is not None

        andreas = TurnLifecycle(db, "andreas", "session:andreas")
        result = andreas.begin("codename")
        assert result["context"]["durable_memory"] == []
        assert result["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert json.loads(row["selected_memory_ids"]) == []
        # Required privacy/perspective contract. The current unscoped policy table is
        # expected to violate this until policy identity/versioning gains user scope.
        assert json.loads(row["shadow_memory_ids"]) == []
        andreas.abort("test-end")
    finally:
        db.close()
