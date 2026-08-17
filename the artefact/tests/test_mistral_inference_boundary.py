import json
import urllib.error

import pytest

from clayverse.identity import IdentityRouter
from clayverse.mistral_inference import (
    DEFAULT_MISTRAL_ENDPOINT,
    MistralInferenceError,
    MistralTokenInference,
    MistralTurnRunner,
)
from clayverse.store import StaleGeneration, UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle, TurnLifecycleError


class FakeResponse:
    def __init__(self, raw: bytes):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.raw if limit < 0 else self.raw[:limit]


class CapturingOpener:
    def __init__(self, envelope=None, *, raw=None, error=None):
        self.request = None
        self.timeout = None
        self.error = error
        if raw is not None:
            self.raw = raw
        else:
            self.raw = json.dumps(
                envelope
                or {
                    "model": "mistral-small-latest",
                    "choices": [{"message": {"content": "provider-ok"}}],
                }
            ).encode()

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        if self.error is not None:
            raise self.error
        return FakeResponse(self.raw)


def test_mistral_request_is_exact_toolless_and_token_is_header_only():
    token = "super-secret-mistral-token"
    opener = CapturingOpener()
    client = MistralTokenInference(api_token=token, opener=opener)

    decision = client.reason({"fact": "canonical"}, "hello")

    assert opener.request.full_url == DEFAULT_MISTRAL_ENDPOINT
    assert opener.request.get_method() == "POST"
    assert opener.request.get_header("Authorization") == f"Bearer {token}"
    assert token.encode() not in opener.request.data
    assert token not in repr(client)
    body = json.loads(opener.request.data)
    assert body["stream"] is False
    assert body["model"] == "mistral-small-latest"
    assert "tools" not in body and "tool_choice" not in body
    assert decision == {
        "text": "provider-ok",
        "selection": "respond",
        "effect": None,
        "provider": "mistral",
        "requested_model": "mistral-small-latest",
        "model": "mistral-small-latest",
    }
    assert token not in json.dumps(decision)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://api.mistral.ai/v1/chat/completions",
        "https://evil.example/v1/chat/completions",
        "https://api.mistral.ai:443/v1/chat/completions",
        "https://user@api.mistral.ai/v1/chat/completions",
        "https://api.mistral.ai/v1/chat/completions?x=1",
        "https://api.mistral.ai/v1/models",
    ],
)
def test_mistral_endpoint_is_exact_fail_closed(endpoint):
    with pytest.raises(MistralInferenceError, match="provider boundary"):
        MistralTokenInference(api_token="secret", endpoint=endpoint, opener=CapturingOpener())


@pytest.mark.parametrize("token", ["", "   ", "abc\ndef", "abc\tdef", "abc\x7fdef"])
def test_mistral_token_rejects_empty_or_control_characters(token):
    with pytest.raises(MistralInferenceError, match="token"):
        MistralTokenInference(api_token=token, opener=CapturingOpener())


def test_nonfinite_world_fails_before_network():
    opener = CapturingOpener()
    client = MistralTokenInference(api_token="secret", opener=opener)
    with pytest.raises(MistralInferenceError, match="canonical JSON"):
        client.reason({"bad": float("nan")}, "hello")
    assert opener.request is None


def test_nonfinite_provider_json_is_rejected():
    opener = CapturingOpener(
        raw=b'{"model":"mistral-small-latest","choices":[{"message":{"content":"ok"}}],"usage":{"x":NaN}}'
    )
    client = MistralTokenInference(api_token="secret", opener=opener)
    with pytest.raises(MistralInferenceError, match="canonical JSON"):
        client.reason({}, "hello")


def test_text_chunk_list_is_admitted_but_nontext_or_tool_calls_are_denied():
    text_chunks = CapturingOpener(
        {
            "model": "mistral-small-latest",
            "choices": [
                {"message": {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}}
            ],
        }
    )
    assert MistralTokenInference(api_token="secret", opener=text_chunks).reason({}, "hello")["text"] == "ab"

    nontext = CapturingOpener(
        {
            "model": "mistral-small-latest",
            "choices": [{"message": {"content": [{"type": "image_url", "image_url": "x"}]}}],
        }
    )
    with pytest.raises(MistralInferenceError, match="non-text"):
        MistralTokenInference(api_token="secret", opener=nontext).reason({}, "hello")

    tool_call = CapturingOpener(
        {
            "model": "mistral-small-latest",
            "choices": [{"message": {"content": "x", "tool_calls": [{"id": "forbidden"}]}}],
        }
    )
    with pytest.raises(MistralInferenceError, match="tool calls"):
        MistralTokenInference(api_token="secret", opener=tool_call).reason({}, "hello")


def test_http_error_never_surfaces_provider_body_or_token():
    token = "secret-provider-token"
    error = urllib.error.HTTPError(
        DEFAULT_MISTRAL_ENDPOINT,
        401,
        f"provider echoed {token}",
        {},
        None,
    )
    client = MistralTokenInference(api_token=token, opener=CapturingOpener(error=error))
    with pytest.raises(MistralInferenceError) as caught:
        client.reason({}, "hello")
    assert token not in str(caught.value)
    assert "provider echoed" not in str(caught.value)


def _lifecycle(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    router = IdentityRouter(db, {"mistral-subject": "gabriel"})
    user_id, session_id = router.resolve("mistral-subject")
    return db, TurnLifecycle(db, user_id, session_id)


class StubInference:
    def __init__(self, text="mistral answer", *, before_return=None, failure=None):
        self.text = text
        self.before_return = before_return
        self.failure = failure

    def reason(self, world, observation):
        assert isinstance(world, dict)
        assert observation
        if self.before_return is not None:
            self.before_return()
        if self.failure is not None:
            raise self.failure
        return {
            "text": self.text,
            "selection": "respond",
            "effect": None,
            "provider": "mistral",
            "requested_model": "mistral-small-latest",
            "model": "mistral-small-2607",
        }


def test_mistral_turn_runner_reingests_on_same_causal_turn_with_provider_provenance(tmp_path):
    db, lifecycle = _lifecycle(tmp_path)
    try:
        result = MistralTurnRunner(lifecycle, StubInference()).run("FACT: source-bound")
        rows = db.all_turns("session:gabriel")
        assert [row["role"] for row in rows] == ["user", "assistant"]
        user_provenance = json.loads(rows[0]["provenance"])
        assistant_provenance = json.loads(rows[1]["provenance"])
        assert user_provenance["source"] == "mistral-api:ingress"
        assert assistant_provenance["source"] == "mistral-api:completion"
        assert assistant_provenance["inference_provider"] == "mistral"
        assert assistant_provenance["requested_model"] == "mistral-small-latest"
        assert assistant_provenance["response_model"] == "mistral-small-2607"
        assert user_provenance["causal_id"] == result["causal_id"] == assistant_provenance["causal_id"]
        assert result["effect"] is None
        assert db.db.execute("SELECT count(*) FROM active_turns").fetchone()[0] == 0
        causal = db.db.execute("SELECT * FROM causal_episodes WHERE causal_id=?", (result["causal_id"],)).fetchone()
        assert causal is not None and causal["observation_turn_id"] == result["turn_id"] and causal["effect_id"] is None
    finally:
        db.close()


def test_stale_generation_during_network_inference_cannot_persist_assistant_output(tmp_path):
    db, lifecycle = _lifecycle(tmp_path)
    try:
        inference = StubInference(before_return=db.advance_entity_generation)
        with pytest.raises(StaleGeneration):
            MistralTurnRunner(lifecycle, inference).run("generation fence")
        rows = db.all_turns("session:gabriel")
        assert [row["role"] for row in rows] == ["user"]
        assert db.db.execute("SELECT count(*) FROM active_turns").fetchone()[0] == 1
    finally:
        db.close()


def test_live_mistral_failure_terminalizes_without_pretending_claude_failure(tmp_path):
    db, lifecycle = _lifecycle(tmp_path)
    try:
        inference = StubInference(failure=MistralInferenceError("synthetic transport failure"))
        with pytest.raises(MistralInferenceError):
            MistralTurnRunner(lifecycle, inference).run("failure path")
        rows = db.all_turns("session:gabriel")
        assert [row["role"] for row in rows] == ["user", "system"]
        provenance = json.loads(rows[-1]["provenance"])
        assert provenance["source"] == "mistral-api:failure"
        assert db.db.execute("SELECT count(*) FROM active_turns").fetchone()[0] == 0
    finally:
        db.close()


def test_complete_inference_rejects_unadmitted_provider(tmp_path):
    db, lifecycle = _lifecycle(tmp_path)
    try:
        lifecycle.begin("x", ingress_source="mistral-api:ingress")
        with pytest.raises(TurnLifecycleError, match="unadmitted"):
            lifecycle.complete_inference(
                "no",
                provider="unknown",
                requested_model="x",
                response_model="x",
            )
    finally:
        db.close()
