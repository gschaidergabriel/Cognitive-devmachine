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


class EntityOSIntentInference:
    def __init__(self):
        self.world = None

    def reason(self, world, observation):
        self.world = world
        return {
            "text": "attempting requested action",
            "selection": "request_effect",
            "effect": {
                "capability": "entityos.exec",
                "target": "unavailable EntityOS regression",
                "argv": ["status"],
            },
        }


def test_inference_intent_reaches_effect_gate_without_direct_process(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(db, {"g": "gabriel"}, inference=NoopIntentInference(), allow_process=False)
        result = engine.ingest("g", "record a bounded noop", request_id="req-noop-route")
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


def test_unavailable_entityos_is_denied_and_causally_reentered(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    inference = EntityOSIntentInference()
    try:
        engine = ClayVerseEngine(db, {"g": "gabriel"}, inference=inference, allow_process=False, entityos_bridge=None)
        result = engine.ingest("g", "perform the requested action if admitted", request_id="req-entityos-denied")

        assert inference.world["runtime_capabilities"] == ["state.noop"]
        assert result["effect_id"]
        assert result["outcome"] == {
            "ok": False,
            "denied": True,
            "reason": "entityos_unavailable",
            "target": "unavailable EntityOS regression",
            "boundary": "EntityOS",
        }
        assert "Requested action was not executed (entityos_unavailable)." in result["decision"]["text"]

        effect = db.db.execute(
            "SELECT capability,status,outcome FROM effects WHERE effect_id=?",
            (result["effect_id"],),
        ).fetchone()
        assert effect["capability"] == "entityos.exec"
        assert effect["status"] == "DENIED"
        assert db.db.execute("SELECT status FROM effect_requests WHERE request_key='gabriel:req-entityos-denied:effect:0'").fetchone()[0] == "DENIED"

        assistant = db.db.execute(
            "SELECT content,causal_refs FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        assert "Requested action was not executed (entityos_unavailable)." in assistant["content"]
        assert result["effect_id"] in assistant["causal_refs"]

        causal = db.db.execute(
            "SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert causal["credit"] == 0.0
        assert causal["reentered"] == 1
        assert causal["outcome_hash"]
    finally:
        db.close()
