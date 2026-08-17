import json
from urllib.error import HTTPError

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference
from clayverse.inference_protocol import InferenceProtocolError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


def mistral_envelope(decision):
    return json.dumps({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": json.dumps(decision, separators=(",", ":")),
            }
        }]
    }).encode()


def test_mistral_requires_runtime_secret_and_explicit_model(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("CLAYVERSE_MISTRAL_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="CLAYVERSE_MISTRAL_MODEL"):
        MistralInference().reason({}, "hello")

    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", "model-x")
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        MistralInference().reason({}, "hello")


def test_mistral_request_is_fixed_endpoint_json_mode_and_secret_is_not_retained(monkeypatch):
    secret = "vault-only-secret-value"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(mistral_envelope({"text": "ok", "effect": None}))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    adapter = MistralInference(model="model-bound-for-test", timeout=9)
    out = adapter.reason({"shared": "state"}, "hello")

    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert captured["url"] == "https://api.mistral.ai/v1/chat/completions"
    assert captured["auth"] == f"Bearer {secret}"
    assert captured["timeout"] == 9
    assert captured["body"]["model"] == "model-bound-for-test"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["temperature"] == 0
    assert set(adapter.__dict__) == {"model", "timeout", "_lock"}
    assert secret not in repr(adapter.__dict__)


def test_mistral_effect_is_only_schema_validated_intent(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")

    def fake_urlopen(request, timeout):
        return FakeResponse(mistral_envelope({
            "text": "request",
            "effect": {
                "capability": "entityos.exec",
                "target": "test",
                "argv": ["status"],
            },
        }))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    out = MistralInference(model="model-x").reason({}, "status")
    assert out == {
        "text": "request",
        "selection": "request_effect",
        "effect": {
            "capability": "entityos.exec",
            "target": "test",
            "argv": ["status"],
        },
    }


def test_mistral_forbidden_capability_fails_before_effectgate(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")

    def fake_urlopen(request, timeout):
        return FakeResponse(mistral_envelope({
            "text": "bad",
            "effect": {
                "capability": "process.exec",
                "target": "host",
                "argv": ["id"],
            },
        }))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    with pytest.raises(InferenceProtocolError, match="forbidden capability"):
        MistralInference(model="model-x").reason({}, "run id")


def test_mistral_transport_error_never_echoes_secret(monkeypatch):
    secret = "TOP_SECRET_MISTRAL_TOKEN"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 401, secret, hdrs=None, fp=None)

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError) as exc:
        MistralInference(model="model-x").reason({}, "hello")
    message = str(exc.value)
    assert "status=401" in message
    assert secret not in message


def test_mistral_malformed_or_oversized_response_fails_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")

    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(b"not-json"))
    with pytest.raises(InferenceProtocolError, match="envelope is not JSON"):
        MistralInference(model="model-x").reason({}, "hello")

    oversized = b"x" * (MistralInference.MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(oversized))
    with pytest.raises(InferenceProtocolError, match="exceeds bound"):
        MistralInference(model="model-x").reason({}, "hello")
