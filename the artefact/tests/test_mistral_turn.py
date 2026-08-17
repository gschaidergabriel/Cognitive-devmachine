import pytest

from clayverse.mistral_turn import MistralTurnError, MistralTurnRunner
from clayverse.store import StaleGeneration
from clayverse.turn_lifecycle import TurnLifecycleError


class FakeInference:
    def __init__(self, decision=None):
        self.decision = decision or {
            "text": "mistral says hello",
            "selection": "respond",
            "effect": None,
            "inference_receipt": {
                "provider": "mistral",
                "model_requested": "model-x",
                "model_returned": "model-x",
                "response_id": "response-1",
                "finish_reason": "stop",
                "request_sha256": "a" * 64,
                "response_sha256": "b" * 64,
            },
        }

    def reason(self, world, observation):
        return self.decision


class InterleavingInference(FakeInference):
    def __init__(self, lifecycle):
        super().__init__()
        self.lifecycle = lifecycle

    def reason(self, world, observation):
        self.lifecycle._active = {"causal_id": "causal-new", "generation": 7}
        return self.decision


class FakeDB:
    def __init__(self, stale_on_call=None):
        self.calls = 0
        self.stale_on_call = stale_on_call

    def assert_live_generation(self, session_id, generation):
        self.calls += 1
        if self.calls == self.stale_on_call:
            raise StaleGeneration(session_id)
        return True


class FakeLifecycle:
    session_id = "session:gabriel"

    def __init__(self, stale_on_call=None, effect_id=None):
        self.db = FakeDB(stale_on_call)
        self.effect_id = effect_id
        self.begin_call = None
        self.complete_call = None
        self.abort_reason = None
        self.abort_expected_causal_id = None
        self._active = None

    def begin(self, prompt, resources=None, *, source):
        self.begin_call = (prompt, resources, source)
        self._active = {"causal_id": "causal-1", "generation": 7}
        return {
            "user_id": "gabriel",
            "session_id": self.session_id,
            "turn_id": "turn-user",
            "causal_id": "causal-1",
            "generation": 7,
            "context": {"own_recent": [], "durable_memory": []},
        }

    def complete(self, text, *, source, provider_receipt, expected_causal_id=None, expected_generation=None):
        if self._active is None:
            return {"completed": False, "reason": "no_active_turn"}
        if self._active["causal_id"] != expected_causal_id:
            raise TurnLifecycleError("active turn causal identity changed")
        if int(self._active["generation"]) != int(expected_generation):
            raise StaleGeneration("expected_turn_generation")
        self.complete_call = (
            text,
            source,
            provider_receipt,
            expected_causal_id,
            expected_generation,
        )
        self._active = None
        return {
            "completed": True,
            "assistant_turn_id": "turn-assistant",
            "causal_id": "causal-1",
            "effect_id": self.effect_id,
        }

    def active(self):
        return self._active

    def abort(self, reason, *, expected_causal_id=None):
        self.abort_reason = reason
        self.abort_expected_causal_id = expected_causal_id
        if self._active is not None and self._active["causal_id"] != expected_causal_id:
            raise TurnLifecycleError("active turn causal identity changed")
        self._active = None
        return {"aborted": True}


def test_mistral_turn_uses_existing_lifecycle_and_persists_provider_receipt():
    lifecycle = FakeLifecycle()
    result = MistralTurnRunner(FakeInference()).run(lifecycle, "hello", ["repo:x"])

    assert lifecycle.begin_call == ("hello", ["repo:x"], "mistral-api:request")
    assert lifecycle.db.calls == 2
    assert lifecycle.complete_call[0] == "mistral says hello"
    assert lifecycle.complete_call[1] == "mistral-api:response"
    assert lifecycle.complete_call[2]["provider"] == "mistral"
    assert lifecycle.complete_call[3] == "causal-1"
    assert lifecycle.complete_call[4] == 7
    assert result["causal_id"] == "causal-1"
    assert result["generation"] == 7
    assert lifecycle.abort_reason is None


def test_mistral_effect_intent_is_rejected_before_any_effect_path():
    decision = FakeInference().decision | {
        "selection": "request_effect",
        "effect": {"capability": "state.noop", "target": "x", "argv": None},
    }
    lifecycle = FakeLifecycle()

    with pytest.raises(MistralTurnError, match="effect intent is not admitted"):
        MistralTurnRunner(FakeInference(decision)).run(lifecycle, "hello")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"
    assert lifecycle.abort_expected_causal_id == "causal-1"


def test_mistral_response_is_rejected_if_generation_changes_during_network_call():
    lifecycle = FakeLifecycle(stale_on_call=2)

    with pytest.raises(StaleGeneration):
        MistralTurnRunner(FakeInference()).run(lifecycle, "hello")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"


def test_interleaved_newer_turn_rejects_stale_response_without_aborting_newer_turn():
    lifecycle = FakeLifecycle()

    with pytest.raises(TurnLifecycleError, match="causal identity changed"):
        MistralTurnRunner(InterleavingInference(lifecycle)).run(lifecycle, "old prompt")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"
    assert lifecycle.abort_expected_causal_id == "causal-1"
    assert lifecycle.active()["causal_id"] == "causal-new"


def test_mistral_receipt_is_required_for_canonical_provider_provenance():
    decision = FakeInference().decision.copy()
    decision.pop("inference_receipt")
    lifecycle = FakeLifecycle()

    with pytest.raises(MistralTurnError, match="receipt is missing"):
        MistralTurnRunner(FakeInference(decision)).run(lifecycle, "hello")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"


def test_mistral_receipt_rejects_extra_secret_like_metadata():
    decision = FakeInference().decision.copy()
    decision["inference_receipt"] = dict(decision["inference_receipt"])
    decision["inference_receipt"]["authorization"] = "Bearer should-never-persist"
    lifecycle = FakeLifecycle()

    with pytest.raises(MistralTurnError, match="receipt is missing or invalid"):
        MistralTurnRunner(FakeInference(decision)).run(lifecycle, "hello")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"


def test_mistral_receipt_rejects_non_digest_hash_fields():
    decision = FakeInference().decision.copy()
    decision["inference_receipt"] = dict(decision["inference_receipt"])
    decision["inference_receipt"]["response_sha256"] = "not-a-digest"
    lifecycle = FakeLifecycle()

    with pytest.raises(MistralTurnError, match="response_sha256 is invalid"):
        MistralTurnRunner(FakeInference(decision)).run(lifecycle, "hello")

    assert lifecycle.complete_call is None
    assert lifecycle.abort_reason == "mistral_turn_failed_or_stale"


def test_mistral_cognition_turn_cannot_return_with_effect_binding():
    lifecycle = FakeLifecycle(effect_id="unexpected-effect")

    with pytest.raises(MistralTurnError, match="unexpectedly bound an effect"):
        MistralTurnRunner(FakeInference()).run(lifecycle, "hello")
