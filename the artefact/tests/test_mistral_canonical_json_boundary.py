import json

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


def test_nonfinite_world_fails_before_mistral_transport(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    called = False

    def fake_urlopen(request, timeout):
        nonlocal called
        called = True
        raise AssertionError("transport must not run")

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    with pytest.raises(InferenceProtocolError, match="WORLD is not canonical JSON"):
        MistralInference(model="model-x").reason({"bad": float("nan")}, "hello")
    assert called is False


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_provider_envelope_fails_closed(monkeypatch, constant):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    raw = (
        '{"id":"cmpl-test","model":"model-x","usage":{"bad":'
        + constant
        + '},"choices":[{"finish_reason":"stop","message":{"content":"{\\"text\\":\\"ok\\",\\"effect\\":null}"}}]}'
    ).encode()
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(raw))
    with pytest.raises(InferenceProtocolError, match="envelope is not JSON"):
        MistralInference(model="model-x").reason({}, "hello")


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_decision_json_fails_before_inference_protocol(monkeypatch, constant):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    raw = (
        '{"id":"cmpl-test","model":"model-x","choices":[{"finish_reason":"stop","message":{"content":"{\\"text\\":\\"ok\\",\\"effect\\":null,\\"bad\\":'
        + constant
        + '}"}}]}'
    ).encode()
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(raw))
    with pytest.raises(InferenceProtocolError, match="message content is not JSON"):
        MistralInference(model="model-x").reason({}, "hello")


def test_duplicate_provider_envelope_key_fails_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    raw = (
        '{"id":"cmpl-test","id":"cmpl-test","model":"model-x",'
        '"choices":[{"finish_reason":"stop","message":{"content":"{\\"text\\":\\"ok\\",\\"effect\\":null}"}}]}'
    ).encode()
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(raw))
    with pytest.raises(InferenceProtocolError, match="envelope is not JSON"):
        MistralInference(model="model-x").reason({}, "hello")


def test_duplicate_decision_effect_key_fails_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    decision = (
        '{"text":"safe","effect":null,'
        '"effect":{"capability":"state.noop","target":"probe","argv":null}}'
    )
    raw = json.dumps(
        {
            "id": "cmpl-test",
            "model": "model-x",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": decision},
                }
            ],
        },
        separators=(",", ":"),
    ).encode()
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(raw))
    with pytest.raises(InferenceProtocolError, match="message content is not JSON"):
        MistralInference(model="model-x").reason({}, "hello")
