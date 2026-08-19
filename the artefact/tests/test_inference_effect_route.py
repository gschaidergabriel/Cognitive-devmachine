import json
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


def test_unavailable_entityos_is_denied_and_causally_reentered(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    inference = EntityOSIntentInference()
    try:
        engine = ClayVerseEngine(db, {"g": "gabriel"}, inference=inference, allow_process=False, entityos_bridge=None)
        result = engine.ingest("g", "perform the requested action if admitted")

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

        # ⭐ UMGESCHRIEBEN 18.08. -- und die neue Fassung ist die STRENGERE.
        #
        # Vorher forderte dieser Test, dass der Ablehnungshinweis IM
        # Assistenzzug steht. Das hiesse: der Assistenzzug wird nachtraeglich
        # veraendert. Genau das verbietet die Regel, die in engine.py ueber
        # diesem Weg steht ("SECURITY / CAUSALITY LAW"): die Modellantwort wird
        # in die UnifiedDB festgeschrieben, BEVOR eine Wirkung das Tor
        # erreichen darf -- damit ein Anbieter keine unmittelbare
        # Handlungsvollmacht bekommt und der genaue Vorschlag beobachtbar
        # bleibt, auch wenn die Wirkung danach abgelehnt wird oder abstuerzt.
        #
        # ⚠️ Ein Assistenzzug, der nachtraeglich einen Behoerdenhinweis
        # eingesetzt bekommt, ist als Beweismittel wertlos: man kann ihm dann
        # nicht mehr ansehen, was das Modell WIRKLICH vorgeschlagen hat.
        # Deshalb wird hier jetzt das Gegenteil geprueft -- der Assistenzzug
        # muss UNBERUEHRT sein -- und der Hinweis in seinem eigenen Systemzug.
        assistant = db.db.execute(
            "SELECT role,content,causal_refs FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        assert assistant["role"] == "assistant"
        assert "Requested action was not executed" not in assistant["content"], (
            "der Assistenzzug haelt fest, was das Modell vorgeschlagen hat, und wird "
            "nicht nachtraeglich veraendert -- sonst ist er als Beweismittel wertlos")
        assert assistant["causal_refs"] == "[]", (
            "er wurde geschrieben, bevor die Wirkung ueberhaupt bestand")

        # Der Hinweis kommt als eigener Systemzug -- und er traegt die Wirkung,
        # damit die Ablehnung an der Kausalkette haengt und nicht nur im Text.
        notice = db.db.execute(
            "SELECT role,content,causal_refs,provenance FROM turns WHERE turn_id=?",
            (result["effect_notice_turn_id"],),
        ).fetchone()
        assert notice is not None, "eine abgelehnte Wirkung muss einen Hinweiszug erzeugen"
        assert notice["role"] == "system"
        assert "Requested action was not executed (entityos_unavailable)." in notice["content"]
        assert result["effect_id"] in notice["causal_refs"]
        assert json.loads(notice["provenance"])["source"] == "effect-gate"

        causal = db.db.execute(
            "SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE causal_id=?",
            (result["causal_id"],),
        ).fetchone()
        assert causal["credit"] == 0.0
        assert causal["reentered"] == 1
        assert causal["outcome_hash"]
    finally:
        db.close()
