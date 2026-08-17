import json

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class _FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


def _envelope(*, model: str = "model-x") -> bytes:
    return json.dumps(
        {
            "id": "cmpl-secret-fence",
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": json.dumps({"text": "ok", "effect": None}),
                    },
                }
            ],
        }
    ).encode()


def test_mistral_secret_in_world_or_observation_fails_before_network(monkeypatch):
    secret = "vault-only-secret-value"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    calls = []

    def should_not_open(request, timeout):
        calls.append((request, timeout))
        raise AssertionError("network boundary must not be reached")

    monkeypatch.setattr(adapters, "urlopen", should_not_open)
    inference = MistralInference(model="model-x")

    with pytest.raises(InferenceProtocolError, match="credential appeared in inference content"):
        inference.reason({"accidental_secret": secret}, "hello")
    with pytest.raises(InferenceProtocolError, match="credential appeared in inference content"):
        inference.reason({"safe": True}, f"hello {secret}")

    assert calls == []


def test_mistral_world_must_be_canonical_json_before_network(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "vault-only-secret-value")
    calls = []

    def should_not_open(request, timeout):
        calls.append((request, timeout))
        raise AssertionError("network boundary must not be reached")

    monkeypatch.setattr(adapters, "urlopen", should_not_open)
    with pytest.raises(InferenceProtocolError, match="WORLD is not canonical JSON"):
        MistralInference(model="model-x").reason({"nonfinite": float("nan")}, "hello")

    assert calls == []


def test_mistral_response_model_must_match_requested_model(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "vault-only-secret-value")
    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: _FakeResponse(_envelope(model="model-y")),
    )

    with pytest.raises(InferenceProtocolError, match="does not match requested model"):
        MistralInference(model="model-x").reason({"safe": True}, "hello")
