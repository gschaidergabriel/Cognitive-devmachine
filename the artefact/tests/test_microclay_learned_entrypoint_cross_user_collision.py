import json

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "b" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def _add(db, memory_id, value, *, subject, user_id, ts):
    db.db.execute(
        "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (memory_id, "fact", subject, value, None, user_id, ts, json.dumps({"source": "test"})),
    )


def test_exact_memory_route_does_not_open_other_users_private_same_subject_memory(tmp_path):
    db = _db(tmp_path)
    try:
        subject = "procedure:shared-label"
        _add(db, "gabriel-memory", "orchid procedure", subject=subject, user_id="gabriel", ts=200.0)
        _add(db, "andreas-memory", "violet bicycle", subject=subject, user_id="andreas", ts=300.0)

        gabriel = TurnLifecycle(
            db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge()
        )
        first = gabriel.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["gabriel-memory"]
        effect = gabriel.request_effect("entityos.exec", "learn-gabriel-private-alias", ["verified-outcome"])
        assert effect["verified"] is True
        gabriel.complete("done")

        # Drain Gabriel's verified outcome and learn the exact-memory alias route.
        learned = gabriel.begin("codename")
        assert learned["context"]["retrieval_receipt"]["outcome_learning_applied"] == 1
        learned_row = db.db.execute(
            "SELECT shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (learned["causal_id"],),
        ).fetchone()
        assert json.loads(learned_row["shadow_memory_ids"]) == ["gabriel-memory"]
        gabriel.abort("switch-user")

        andreas = TurnLifecycle(db, "andreas", "session:andreas")
        other = andreas.begin("codename")
        assert other["context"]["durable_memory"] == []
        assert other["context"]["retrieval_receipt"]["status"] == "UNKNOWN"
        other_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (other["causal_id"],),
        ).fetchone()
        assert json.loads(other_row["selected_memory_ids"]) == []
        assert json.loads(other_row["shadow_memory_ids"]) == []
        andreas.abort("test-end")
    finally:
        db.close()
