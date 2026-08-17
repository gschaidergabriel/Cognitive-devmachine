import json

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


class _VerifiedEffectBridge:
    sha256 = "e" * 64

    def run(self, argv):
        return {"ok": True, "exit": 0, "stdout": "", "stderr": ""}


def test_live_v3_turn_ignores_verified_reward_from_legacy_policy_episode(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    try:
        db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) VALUES(?,?,?,?,?,?,?,?)",
            ("legacy-learning-memory", "fact", "procedure:orchid", "orchid verified procedure", None, "gabriel", 100.0, json.dumps({"source": "legacy-policy-filter-test"})),
        )
        life = TurnLifecycle(db, "gabriel", "session:gabriel", entityos_bridge=_VerifiedEffectBridge())
        first = life.begin("orchid verified procedure codename")
        effect = life.request_effect("entityos.exec", "legacy-policy-learning", ["verified"])
        assert effect["verified"] is True
        life.complete("done")
        db.db.execute(
            "UPDATE retrieval_episodes SET policy_version=2 WHERE causal_id=?", (first["causal_id"],)
        )

        second = life.begin("orchid")
        receipt = second["context"]["retrieval_receipt"]
        assert receipt["policy_version"] == 3
        assert receipt["outcome_learning_applied"] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_feedback").fetchone()[0] == 0
        assert db.db.execute("SELECT COUNT(*) FROM retrieval_entrypoint_policy").fetchone()[0] == 0
        life.abort("test-end")
    finally:
        db.close()
