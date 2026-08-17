import io
import json
import urllib.error

import pytest

from clayverse import adapters
from clayverse.adapters import MistralAPIInference
from clayverse.engine import ClayVerseEngine
from clayverse.inference_protocol import InferenceProtocolError


class _FakeResponse:
    def __init__(self, payload: bytes, status: int = 200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, amount=-1):
        if amount is None or amount < 0:
            return self.payload
        return self.payload[:amount]


def _envelope(content, *, model="mistral-large-current-id", response_id="cmpl-test"):
    return json.dumps(
        {
            "id": response_id,
            "model": model,
            "choices": [{"message": {"role": "assistant", "content": json.dumps(content)}}],
        }
    ).encode()


def test_mistral_requires_runtime_secret_before_network(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be attempted without secret")

    monkeypatch.setattr(adapters.urllib.request, "urlopen", forbidden)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY is required"):
        MistralAPIInference(model="mistral-large-latest").reason({}, "hello")
    assert called is False


def test_mistral_json_decision_is_bounded_and_secret_is_header_only(monkeypatch):
    secret = "mistral-secret-never-persist"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _FakeResponse(_envelope({"text": "hello", "effect": None}))

    monkeypatch.setattr(adapters.urllib.request, "urlopen", fake_urlopen)
    adapter = MistralAPIInference(model="mistral-large-latest", timeout=17, max_tokens=512)
    decision = adapter.reason({"canonical": "world"}, "hello")

    assert decision == {"text": "hello", "selection": "respond", "effect": None}
    request = captured["request"]
    assert request.full_url == "https://api.mistral.ai/v1/chat/completions"
    assert request.get_header("Authorization") == f"Bearer {secret}"
    assert captured["timeout"] == 17
    body = json.loads(request.data)
    assert body["model"] == "mistral-large-latest"
    assert body["response_format"] == {"type": "json_object"}
    assert body["temperature"] == 0
    assert body["max_tokens"] == 512
    assert secret not in request.data.decode()
    assert "Return JSON only" in body["messages"][1]["content"]

    provenance = adapter.provenance()
    encoded = json.dumps(provenance, sort_keys=True)
    assert provenance["provider"] == "mistral"
    assert provenance["requested_model"] == "mistral-large-latest"
    assert provenance["response_model"] == "mistral-large-current-id"
    assert provenance["response_id"] == "cmpl-test"
    assert secret not in encoded
    assert "api_key" not in encoded.lower()


def test_mistral_forbidden_effect_is_rejected_before_engine(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    bad = {
        "text": "trying",
        "effect": {"capability": "process.exec", "target": "host", "argv": ["sh"]},
    }
    monkeypatch.setattr(
        adapters.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(_envelope(bad)),
    )
    with pytest.raises(InferenceProtocolError, match="forbidden capability"):
        MistralAPIInference(model="mistral-large-latest").reason({}, "do it")


def test_mistral_http_failure_never_echoes_secret_or_body(monkeypatch):
    secret = "super-secret-token"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)

    def fail(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=io.BytesIO(("provider-body-" + secret).encode()),
        )

    monkeypatch.setattr(adapters.urllib.request, "urlopen", fail)
    with pytest.raises(RuntimeError) as excinfo:
        MistralAPIInference(model="mistral-large-latest").reason({}, "hello")
    message = str(excinfo.value)
    assert "status=401" in message
    assert "body_sha256=" in message
    assert secret not in message
    assert "provider-body" not in message


def test_mistral_response_envelope_is_bounded(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    payload = b"x" * (MistralAPIInference.MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(
        adapters.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(payload),
    )
    with pytest.raises(RuntimeError, match="exceeds bounded envelope"):
        MistralAPIInference(model="mistral-large-latest").reason({}, "hello")


def test_engine_sanitizes_inference_provenance_keys():
    class _Inference:
        def provenance(self):
            return {
                "provider": "mistral",
                "requested_model": "mistral-large-latest",
                "token": "must-not-persist",
                "authorization": "must-not-persist",
                "secret": "must-not-persist",
                "nested": {"unsafe": "not-admitted"},
            }

    engine = ClayVerseEngine.__new__(ClayVerseEngine)
    engine.inference = _Inference()
    provenance = engine._inference_provenance()
    assert provenance == {
        "source": "inference-adapter",
        "provider": "mistral",
        "requested_model": "mistral-large-latest",
    }
