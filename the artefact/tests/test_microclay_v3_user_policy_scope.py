import json

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
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


def test_shared_memory_stays_shared_but_learned_alias_capital_is_user_scoped(tmp_path):
    """One central memory may be shared while Gabriel's learned entry never becomes Andreas' policy."""
    db = _db(tmp_path)
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                "shared-procedure",
                "fact",
                "procedure:shared",
                "orchid procedure",
                None,
                None,
                100.0,
                json.dumps({"source": "v3-user-scope-test"}),
            ),
        )

        gabriel = TurnLifecycle(
            db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge()
        )
        first = gabriel.begin("orchid procedure codename")
        assert [m["memory_id"] for m in first["context"]["durable_memory"]] == ["shared-procedure"]
        effect = gabriel.request_effect("entityos.exec", "learn-shared-memory-alias", ["verified"])
        assert effect["verified"] is True
        gabriel.complete("done")

        learned = gabriel.begin("codename")
        assert learned["context"]["durable_memory"] == []
        learned_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (learned["causal_id"],),
        ).fetchone()
        assert json.loads(learned_row["selected_memory_ids"]) == []
        assert json.loads(learned_row["shadow_memory_ids"]) == ["shared-procedure"]
        route_key = MicroClayRetrieval._route_key("gabriel", "codename", "shared-procedure")
        assert db.db.execute(
            "SELECT 1 FROM retrieval_entrypoint_policy WHERE entry_key=?", (route_key,)
        ).fetchone() is not None
        assert db.db.execute(
            "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE entry_key LIKE 'v3:user:andreas:%'"
        ).fetchone()[0] == 0
        gabriel.abort("test-end")

        andreas = TurnLifecycle(db, "andreas", "session:andreas")
        miss = andreas.begin("codename")
        assert miss["context"]["durable_memory"] == []
        miss_row = db.db.execute(
            "SELECT selected_memory_ids,shadow_memory_ids FROM retrieval_episodes WHERE causal_id=?",
            (miss["causal_id"],),
        ).fetchone()
        assert json.loads(miss_row["selected_memory_ids"]) == []
        assert json.loads(miss_row["shadow_memory_ids"]) == []
        andreas.abort("test-end")
    finally:
        db.close()
