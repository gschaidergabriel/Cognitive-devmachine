import json

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


def _envelope(model: str) -> bytes:
    return json.dumps(
        {
            "id": "cmpl-model-fence",
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


def test_mistral_provider_model_must_equal_requested_model(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-secret")
    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: _Response(_envelope("mistral-other-model")),
    )

    with pytest.raises(InferenceProtocolError, match="does not match requested model"):
        MistralInference(model="mistral-small-2603").reason({}, "hello")


def test_mistral_exact_provider_model_remains_accepted(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "runtime-secret")
    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: _Response(_envelope("mistral-small-2603")),
    )

    decision = MistralInference(model="mistral-small-2603").reason({}, "hello")
    assert decision["text"] == "ok"
    assert decision["effect"] is None
    assert decision["inference_receipt"]["model_requested"] == "mistral-small-2603"
    assert decision["inference_receipt"]["model_returned"] == "mistral-small-2603"
