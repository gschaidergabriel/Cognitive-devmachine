import io
import json
import urllib.error

import pytest

from clayverse.mistral_inference import MistralInferenceError, MistralTokenInference


TOKEN = "mistral-test-secret-ASCII-123"
MODEL = "mistral-small-latest"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit):
        return self.payload[:limit]


class RecordingOpener:
    def __init__(self, payload=None, error=None):
        self.payload = payload or json.dumps(
            {
                "model": MODEL,
                "choices": [{"message": {"content": "bounded answer"}}],
            }
        ).encode()
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error is not None:
            raise self.error
        return FakeResponse(self.payload)


def client(opener=None, **kwargs):
    return MistralTokenInference(
        api_token=TOKEN,
        model=MODEL,
        opener=opener or RecordingOpener(),
        **kwargs,
    )


def test_exact_https_provider_boundary_only():
    accepted = client(endpoint="https://api.mistral.ai/v1/chat/completions/")
    assert accepted.endpoint == "https://api.mistral.ai/v1/chat/completions"
    for endpoint in (
        "http://api.mistral.ai/v1/chat/completions",
        "https://evil.example/v1/chat/completions",
        "https://api.mistral.ai.evil.example/v1/chat/completions",
        "https://user@api.mistral.ai/v1/chat/completions",
        "https://api.mistral.ai:443/v1/chat/completions",
        "https://api.mistral.ai/v1/chat/completions?x=1",
        "https://api.mistral.ai/v1/agents/completions",
    ):
        with pytest.raises(MistralInferenceError):
            client(endpoint=endpoint)


def test_token_must_be_nonempty_visible_ascii():
    for token in ("", " ", "bad\nheader", "bad\x00token", "é"):
        with pytest.raises(MistralInferenceError, match="token is missing or malformed"):
            MistralTokenInference(api_token=token, model=MODEL, opener=RecordingOpener())


def test_model_identifier_is_bounded_to_mistral_family():
    for model in ("", "gpt-5", "glm-5", "mistral bad", "mistral-\nsmall"):
        with pytest.raises(MistralInferenceError, match="model identifier is invalid"):
            MistralTokenInference(api_token=TOKEN, model=model, opener=RecordingOpener())
    assert MistralTokenInference(api_token=TOKEN, model="ministral-14b-latest", opener=RecordingOpener()).model == "ministral-14b-latest"


def test_secret_only_enters_authorization_header_never_payload_or_repr():
    opener = RecordingOpener()
    c = client(opener)
    result = c.reason({"fact": "alpha"}, "question")
    request, timeout = opener.requests[0]
    assert request.full_url == "https://api.mistral.ai/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == f"Bearer {TOKEN}"
    assert TOKEN.encode() not in request.data
    assert TOKEN not in repr(c)
    assert TOKEN not in repr(result)
    assert timeout == 120.0


def test_payload_has_no_tools_and_explicitly_preserves_clayverse_authority():
    opener = RecordingOpener()
    client(opener).reason({"state": {"x": 1}}, "observe")
    request, _ = opener.requests[0]
    body = json.loads(request.data)
    assert body["stream"] is False
    assert "tools" not in body
    assert "tool_choice" not in body
    system = body["messages"][0]["content"]
    assert "UnifiedDB remains authoritative" in system
    assert "no tools" in system
    assert "EffectGate" in system
    assert "EntityOS" in system


def test_response_is_text_only_and_cannot_request_an_effect():
    result = client().reason({"fact": "alpha"}, "question")
    assert result == {
        "text": "bounded answer",
        "selection": "respond",
        "effect": None,
        "provider": "mistral",
        "model": MODEL,
    }


def test_secret_in_context_or_provider_response_fails_closed():
    c = client()
    with pytest.raises(MistralInferenceError, match="credential appeared in inference content"):
        c.reason({"leak": TOKEN}, "question")
    with pytest.raises(MistralInferenceError, match="credential appeared in inference content"):
        c.reason({}, f"question {TOKEN}")
    opener = RecordingOpener(
        json.dumps(
            {"model": MODEL, "choices": [{"message": {"content": f"echo {TOKEN}"}}]}
        ).encode()
    )
    with pytest.raises(MistralInferenceError, match="credential appeared in provider response"):
        client(opener).reason({}, "question")


def test_http_error_does_not_surface_provider_body_or_secret():
    error = urllib.error.HTTPError(
        "https://api.mistral.ai/v1/chat/completions",
        401,
        f"provider body leaked {TOKEN}",
        hdrs=None,
        fp=io.BytesIO(f"body {TOKEN}".encode()),
    )
    with pytest.raises(MistralInferenceError) as caught:
        client(RecordingOpener(error=error)).reason({}, "question")
    assert str(caught.value) == "Mistral inference failed with HTTP status 401"
    assert TOKEN not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_malformed_nonfinite_or_model_mismatch_response_fails_closed():
    cases = [
        (b"not-json", "valid canonical JSON"),
        (b'{"model":"mistral-small-latest","choices":[{"message":{"content":NaN}}]}', "valid canonical JSON"),
        (json.dumps({"model": MODEL, "choices": []}).encode(), "shape is invalid"),
        (json.dumps({"model": MODEL, "choices": [{"message": {"content": ""}}]}).encode(), "content is invalid"),
        (json.dumps({"model": "mistral-large-latest", "choices": [{"message": {"content": "x"}}]}).encode(), "does not match"),
    ]
    for payload, expected in cases:
        with pytest.raises(MistralInferenceError, match=expected):
            client(RecordingOpener(payload=payload)).reason({}, "question")


def test_timeout_and_size_bounds_fail_closed():
    for timeout in (0, 0.01, 601, "bad"):
        with pytest.raises(MistralInferenceError, match="timeout"):
            MistralTokenInference(api_token=TOKEN, model=MODEL, timeout_seconds=timeout, opener=RecordingOpener())
    c = client()
    with pytest.raises(MistralInferenceError, match="observation"):
        c.reason({}, "x" * 100_001)
    with pytest.raises(MistralInferenceError, match="assembled world"):
        c.reason({"x": "y" * 600_001}, "question")


def test_engine_reingests_mistral_text_without_persisting_secret(tmp_path):
    from clayverse.engine import ClayVerseEngine
    from clayverse.store import UnifiedDB

    db = UnifiedDB(tmp_path / "unified.db")
    try:
        inference = client(RecordingOpener())
        engine = ClayVerseEngine(
            db,
            {"clerk-g": "gabriel", "clerk-a": "andreas"},
            inference=inference,
        )
        result = engine.ingest("clerk-g", "FACT: final-test cue")
        assert result["decision"]["provider"] == "mistral"
        assert result["decision"]["effect"] is None
        assert result["effect_id"] is None
        assert result["outcome"] is None
        assistant = db.db.execute(
            "select content,provenance from turns where turn_id=?",
            (result["assistant_turn_id"],),
        ).fetchone()
        assert assistant["content"] == "bounded answer"
        assert TOKEN not in assistant["content"]
        dump = "\n".join(db.db.iterdump())
        assert TOKEN not in dump
    finally:
        db.close()
