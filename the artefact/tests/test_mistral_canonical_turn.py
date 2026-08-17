import json

import pytest

from clayverse.identity import IdentityRouter
from clayverse.mistral_turn import MistralCanonicalTurn, MistralCanonicalTurnError
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


TOKEN = "mistral-test-secret-ASCII-123"
MODEL = "mistral-small-latest"


class FakeMistral:
    def __init__(self, text="bounded answer", *, effect=None, provider="mistral", model=MODEL):
        self.text = text
        self.effect = effect
        self.provider = provider
        self.model = model
        self.calls = []

    def reason(self, world, observation):
        self.calls.append((world, observation))
        return {
            "text": self.text,
            "selection": "respond",
            "effect": self.effect,
            "provider": self.provider,
            "model": self.model,
        }


def make_db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def test_mistral_no_effect_reingests_one_assistant_turn_into_same_causal_episode(tmp_path):
    db = make_db(tmp_path)
    try:
        result = MistralCanonicalTurn(db, "gabriel", FakeMistral()).run("FACT: cue")
        assert result["provider"] == "mistral"
        assert result["text"] == "bounded answer"
        assert result["effect"] is None
        assert result["response_reingested"] is True
        assert db.db.execute("SELECT 1 FROM active_turns WHERE session_id=?", (result["session_id"],)).fetchone() is None

        provider = db.db.execute("SELECT * FROM provider_responses WHERE causal_id=?", (result["causal_id"],)).fetchone()
        assert provider is not None
        assert provider["response_turn_id"] == result["assistant_turn_id"]
        assert provider["provider"] == "mistral"
        assert provider["model"] == MODEL
        assert int(provider["generation"]) == result["generation"]

        assistant = db.db.execute("SELECT * FROM turns WHERE turn_id=?", (result["assistant_turn_id"],)).fetchone()
        provenance = json.loads(assistant["provenance"])
        assert assistant["role"] == "assistant"
        assert assistant["content"] == "bounded answer"
        assert provenance["source"] == "mistral-runtime:provider-response"
        assert provenance["causal_id"] == result["causal_id"]
        assert provenance["operational_authority"] is False

        causal = db.db.execute("SELECT * FROM causal_episodes WHERE causal_id=?", (result["causal_id"],)).fetchone()
        assert causal is not None
        assert causal["observation_turn_id"] == result["turn_id"]
        assert causal["effect_id"] is None
    finally:
        db.close()


def test_effect_is_denied_until_mistral_response_has_reentered_then_uses_same_causal_id(tmp_path):
    db = make_db(tmp_path)
    try:
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        begin = lifecycle.begin("test", input_source="mistral-runtime:input")
        with pytest.raises(TurnLifecycleError, match="re-ingested before any effect"):
            lifecycle.request_effect("state.noop", "safe")

        reingested = lifecycle.reingest_provider_response("answer", provider="mistral", model=MODEL)
        effect = lifecycle.request_effect("state.noop", "safe")
        completed = lifecycle.complete_reingested_provider_response()

        assert reingested["causal_id"] == begin["causal_id"]
        assert effect["causal_id"] == begin["causal_id"]
        assert completed["causal_id"] == begin["causal_id"]
        assert completed["assistant_turn_id"] == reingested["response_turn_id"]
        effect_row = db.db.execute("SELECT ts FROM effects WHERE effect_id=?", (effect["effect_id"],)).fetchone()
        provider_row = db.db.execute("SELECT ts FROM provider_responses WHERE causal_id=?", (begin["causal_id"],)).fetchone()
        assert provider_row["ts"] <= effect_row["ts"]
    finally:
        db.close()


def test_exact_duplicate_reingest_is_idempotent_but_different_response_is_denied(tmp_path):
    db = make_db(tmp_path)
    try:
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        lifecycle.begin("test", input_source="mistral-runtime:input")
        first = lifecycle.reingest_provider_response("answer", provider="mistral", model=MODEL)
        same = lifecycle.reingest_provider_response("answer", provider="mistral", model=MODEL)
        assert same["response_turn_id"] == first["response_turn_id"]
        with pytest.raises(TurnLifecycleError, match="different provider response"):
            lifecycle.reingest_provider_response("different", provider="mistral", model=MODEL)
        lifecycle.complete_reingested_provider_response()
    finally:
        db.close()


def test_stale_global_generation_rejects_provider_reingest(tmp_path):
    db = make_db(tmp_path)
    try:
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        lifecycle.begin("test", input_source="mistral-runtime:input")
        db.advance_entity_generation()
        with pytest.raises(StaleGeneration):
            lifecycle.reingest_provider_response("answer", provider="mistral", model=MODEL)
    finally:
        db.close()


def test_model_output_cannot_supply_effect_authority_and_failed_turn_is_aborted(tmp_path):
    db = make_db(tmp_path)
    try:
        runtime = MistralCanonicalTurn(
            db,
            "gabriel",
            FakeMistral(effect={"capability": "state.noop", "target": "model-controlled"}),
        )
        with pytest.raises(MistralCanonicalTurnError, match="attempted to carry effect authority"):
            runtime.run("test")
        assert db.db.execute("SELECT 1 FROM active_turns WHERE session_id='session:gabriel'").fetchone() is None
        system = db.db.execute("SELECT content,provenance FROM turns WHERE role='system' ORDER BY ordinal DESC LIMIT 1").fetchone()
        assert system["content"].startswith("TURN_ABORTED:")
        assert json.loads(system["provenance"])["source"] == "mistral-runtime:failure"
    finally:
        db.close()


def test_trusted_noop_happens_only_after_response_reingest_and_secret_is_not_persisted(tmp_path):
    db = make_db(tmp_path)
    try:
        runtime = MistralCanonicalTurn(db, "andreas", FakeMistral(text="safe answer"))
        result = runtime.run(
            "question without credential",
            effect={"capability": "state.noop", "target": "mistral-final-test"},
        )
        assert result["effect"]["verified"] is True
        assert result["effect"]["causal_id"] == result["causal_id"]
        dump = "\n".join(db.db.iterdump())
        assert TOKEN not in dump
        assert "safe answer" in dump
        assert "mistral-runtime:provider-response" in dump
    finally:
        db.close()


def test_claude_default_lifecycle_does_not_require_provider_response(tmp_path):
    db = make_db(tmp_path)
    try:
        lifecycle = TurnLifecycle(db, "gabriel", "session:gabriel")
        begin = lifecycle.begin("ordinary Claude hook semantics")
        effect = lifecycle.request_effect("state.noop", "safe")
        completed = lifecycle.complete("assistant")
        assert effect["causal_id"] == begin["causal_id"]
        assert completed["causal_id"] == begin["causal_id"]
        assert db.db.execute("SELECT COUNT(*) FROM provider_responses").fetchone()[0] == 0
    finally:
        db.close()
