from clayverse.engine import ClayVerseEngine
from clayverse.store import UnifiedDB


class NoopIntentInference:
    def reason(self, world, observation):
        return {
            "text": "recorded",
            "selection": "request_effect",
            "effect": {
                "capability": "state.noop",
                "target": "deterministic inference route regression",
                "argv": None,
            },
        }


def test_inference_intent_reaches_effect_gate_without_direct_process(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(db, {"g": "gabriel"}, inference=NoopIntentInference(), allow_process=False)
        result = engine.ingest("g", "record a bounded noop")
        assert result["decision"]["selection"] == "request_effect"
        assert result["effect_id"]
        assert result["outcome"]["ok"] is True
        assert result["outcome"]["target"] == "deterministic inference route regression"
        row = db.db.execute("SELECT capability,status FROM effects WHERE effect_id=?", (result["effect_id"],)).fetchone()
        assert row["capability"] == "state.noop"
        assert row["status"] == "VERIFIED"
        ws = db.db.execute("SELECT selected,state FROM workspace_episodes WHERE episode_id=?", (result["workspace"]["episode_id"],)).fetchone()
        assert ws["selected"] == "request_effect"
        assert ws["state"] == "SELECTED"
    finally:
        db.close()
