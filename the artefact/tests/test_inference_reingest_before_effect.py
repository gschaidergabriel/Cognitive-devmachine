import json

from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


class ReceiptEffectInference:
    def reason(self, world, observation):
        return {
            "text": "model proposes bounded status effect",
            "selection": "request_effect",
            "effect": {
                "capability": "entityos.exec",
                "target": "transport",
                "argv": ["status"],
            },
            "inference_receipt": {
                "provider": "mistral",
                "model_requested": "model-x",
                "model_returned": "model-x-immutable",
                "response_id": "cmpl-test",
                "finish_reason": "stop",
                "request_sha256": "1" * 64,
                "response_sha256": "2" * 64,
            },
        }


class InspectingBridge:
    sha256 = "b" * 64

    def __init__(self, db):
        self.db = db
        self.saw_reingested_proposal = False

    def run(self, argv):
        rows = self.db.db.execute(
            "SELECT role,content,provenance FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [row["role"] for row in rows] == ["user", "assistant"]
        assert rows[-1]["content"] == "model proposes bounded status effect"
        provenance = json.loads(rows[-1]["provenance"])
        assert provenance["phase"] == "pre-effect-reingest"
        assert provenance["inference_receipt"]["provider"] == "mistral"
        assert provenance["inference_receipt"]["response_id"] == "cmpl-test"
        self.saw_reingested_proposal = True
        return {"ok": True, "exit": 0, "stdout": "ok", "stderr": ""}


def test_model_proposal_is_in_unifieddb_before_entityos_can_run(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    bridge = InspectingBridge(db)
    try:
        result = ClayVerseEngine(
            db,
            {"g": "gabriel"},
            inference=ReceiptEffectInference(),
            entityos_bridge=bridge,
        ).ingest("g", "run bounded status")

        assert bridge.saw_reingested_proposal is True
        assert result["effect_id"] is not None
        assert result["outcome"]["ok"] is True
        assistant = db.db.execute(
            "SELECT role,provenance FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        assert assistant["role"] == "assistant"
        provenance = json.loads(assistant["provenance"])
        assert provenance["reasoning_generation"] == db.entity_generation()
        assert provenance["workspace_episode_id"] == result["workspace"]["episode_id"]
        assert provenance["inference_receipt"]["provider"] == "mistral"
    finally:
        db.close()


def test_denied_effect_notice_reenters_after_original_model_proposal(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        result = ClayVerseEngine(
            db,
            {"g": "gabriel"},
            inference=ReceiptEffectInference(),
            entityos_bridge=None,
        ).ingest("g", "run unavailable effect")

        assert result["outcome"]["denied"] is True
        assert result["effect_notice_turn_id"] is not None
        rows = db.db.execute(
            "SELECT role,content,causal_refs,provenance FROM turns ORDER BY ordinal"
        ).fetchall()
        assert [row["role"] for row in rows] == ["user", "assistant", "system"]
        assert rows[1]["content"] == "model proposes bounded status effect"
        assert "Requested action was not executed" in rows[2]["content"]
        assert json.loads(rows[2]["causal_refs"]) == [result["effect_id"]]
        assert json.loads(rows[2]["provenance"])["phase"] == "effect-outcome-reentry"
    finally:
        db.close()
