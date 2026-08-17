import json

from clayverse.engine import ClayVerseEngine
from clayverse.mistral_inference import DEFAULT_MISTRAL_MODEL, MistralTokenInference
from clayverse.store import UnifiedDB


class _Response:
    def __init__(self):
        self.raw = json.dumps(
            {
                "model": DEFAULT_MISTRAL_MODEL,
                "choices": [{"message": {"content": "mistral canonical response"}}],
            }
        ).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.raw[:limit]


class _Opener:
    def open(self, request, timeout):
        return _Response()


def test_mistral_response_reenters_unifieddb_with_provider_generation_binding(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        inference = MistralTokenInference(api_token="token", opener=_Opener())
        engine = ClayVerseEngine(db, {"mistral-user": "gabriel"}, inference=inference)
        result = engine.ingest("mistral-user", "use canonical context")

        assert result["effect_id"] is None
        assert result["decision"]["provider"] == "mistral"
        assistant = db.db.execute(
            "SELECT content,causal_refs,provenance FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        provenance = json.loads(assistant["provenance"])
        assert assistant["content"] == "mistral canonical response"
        assert json.loads(assistant["causal_refs"]) == []
        assert provenance["source"] == "inference-adapter"
        assert provenance["provider"] == "mistral"
        assert provenance["model"] == DEFAULT_MISTRAL_MODEL
        assert provenance["entity_generation"] == db.entity_generation()
    finally:
        db.close()


class _EffectIntentInference:
    def reason(self, world, observation):
        return {
            "text": "provider response before effect",
            "selection": "request_effect",
            "effect": {
                "capability": "state.noop",
                "target": "reingest-order-regression",
                "argv": None,
            },
            "provider": "test-provider",
            "model": "test-model",
        }


def test_provider_response_is_persisted_before_effectgate_execution(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        engine = ClayVerseEngine(
            db,
            {"mistral-user": "gabriel"},
            inference=_EffectIntentInference(),
        )
        original_execute = engine.effects.execute
        observed = {"pre_effect_reingested": False}

        def guarded_execute(request, episode_id):
            assistant = db.db.execute(
                "SELECT content,provenance FROM turns WHERE session_id=? AND role='assistant' ORDER BY ordinal DESC LIMIT 1",
                (request.session_id,),
            ).fetchone()
            assert assistant is not None
            assert assistant["content"] == "provider response before effect"
            provenance = json.loads(assistant["provenance"])
            assert provenance["provider"] == "test-provider"
            assert provenance["model"] == "test-model"
            assert provenance["entity_generation"] == request.requested_generation
            observed["pre_effect_reingested"] = True
            return original_execute(request, episode_id)

        engine.effects.execute = guarded_execute
        result = engine.ingest("mistral-user", "run safe bounded noop")

        assert observed["pre_effect_reingested"] is True
        assert result["outcome"]["ok"] is True
        assistant = db.db.execute(
            "SELECT causal_refs FROM turns WHERE turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        assert json.loads(assistant["causal_refs"]) == [result["effect_id"]]
    finally:
        db.close()
