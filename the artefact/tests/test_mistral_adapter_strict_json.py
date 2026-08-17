import json

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


def _envelope(*, model="mistral-small-2603", content=None, usage_fragment=b""):
    if content is None:
        content = json.dumps({"text": "ok", "effect": None})
    prefix = (
        b'{"id":"cmpl-test","model":"'
        + model.encode()
        + b'","choices":[{"finish_reason":"stop","message":{"content":'
        + json.dumps(content).encode()
        + b'}}]'
    )
    if usage_fragment:
        prefix += b',"usage":' + usage_fragment
    return prefix + b"}"


def _inference(monkeypatch, payload):
    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-secret")
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: _Response(payload))
    return MistralInference(model="mistral-small-2603")


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_mistral_rejects_non_finite_world_before_network(monkeypatch, non_finite):
    called = {"value": False}

    def _unexpected(request, timeout):
        called["value"] = True
        raise AssertionError("network must not be reached")

    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-secret")
    monkeypatch.setattr(adapters, "urlopen", _unexpected)
    inference = MistralInference(model="mistral-small-2603")

    with pytest.raises(InferenceProtocolError, match="WORLD is not canonical JSON"):
        inference.reason({"value": non_finite}, "hello")
    assert called["value"] is False


@pytest.mark.parametrize("constant", [b"NaN", b"Infinity", b"-Infinity"])
def test_mistral_rejects_non_finite_provider_envelope(monkeypatch, constant):
    inference = _inference(monkeypatch, _envelope(usage_fragment=b'{"total_tokens":' + constant + b"}"))
    with pytest.raises(InferenceProtocolError, match="response envelope is not JSON"):
        inference.reason({}, "hello")


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_mistral_rejects_non_finite_message_json(monkeypatch, constant):
    content = '{"text":"ok","effect":null,"extra":' + constant + "}"
    inference = _inference(monkeypatch, _envelope(content=content))
    with pytest.raises(InferenceProtocolError, match="message content is not JSON"):
        inference.reason({}, "hello")
