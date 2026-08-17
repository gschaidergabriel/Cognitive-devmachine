import json

import pytest

from clayverse import api_providers
from clayverse.api_providers import build_api_inference_from_env
from clayverse.inference_protocol import InferenceProtocolError


class _Response:
    def __init__(self, payload, *, raw=False):
        self.payload = payload if raw else json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit):
        return self.payload[:limit]


def _adapter(monkeypatch, secret="bounded-provider-token-123"):
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-small-latest")
    return build_api_inference_from_env()


def _envelope(*, model="mistral-small-latest", content=None):
    return {
        "id": "resp-1",
        "model": model,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": content
                    if content is not None
                    else json.dumps({"text": "provider-ok", "effect": None})
                },
            }
        ],
    }


def test_provider_envelope_rejects_duplicate_json_members(monkeypatch):
    adapter = _adapter(monkeypatch)
    raw = (
        b'{"id":"resp-1","id":"resp-2","model":"mistral-small-latest",'
        b'"choices":[{"finish_reason":"stop","message":{"content":"{\\"text\\":\\"ok\\",\\"effect\\":null}"}}]}'
    )
    monkeypatch.setattr(api_providers, "_urlopen", lambda request, timeout: _Response(raw, raw=True))
    with pytest.raises(InferenceProtocolError, match="canonical JSON"):
        adapter.reason({}, "hello")


def test_provider_decision_rejects_duplicate_json_members(monkeypatch):
    adapter = _adapter(monkeypatch)
    content = (
        '{"text":"ok","effect":null,'
        '"effect":{"capability":"state.noop","target":"probe","argv":null}}'
    )
    monkeypatch.setattr(
        api_providers,
        "_urlopen",
        lambda request, timeout: _Response(_envelope(content=content)),
    )
    with pytest.raises(InferenceProtocolError, match="canonical JSON"):
        adapter.reason({}, "hello")


def test_provider_response_model_must_match_requested_model(monkeypatch):
    adapter = _adapter(monkeypatch)
    monkeypatch.setattr(
        api_providers,
        "_urlopen",
        lambda request, timeout: _Response(_envelope(model="unexpected-model")),
    )
    with pytest.raises(InferenceProtocolError, match="does not match requested model"):
        adapter.reason({}, "hello")


def test_nonfinite_world_fails_before_network(monkeypatch):
    adapter = _adapter(monkeypatch)
    called = False

    def fake_open(request, timeout):
        nonlocal called
        called = True
        return _Response(_envelope())

    monkeypatch.setattr(api_providers, "_urlopen", fake_open)
    with pytest.raises(InferenceProtocolError, match="WORLD is not canonical JSON"):
        adapter.reason({"bad": float("nan")}, "hello")
    assert called is False


@pytest.mark.parametrize("location", ["world", "observation"])
def test_runtime_credential_never_enters_model_visible_context(monkeypatch, location):
    secret = "model-visible-secret-123"
    adapter = _adapter(monkeypatch, secret)
    called = False

    def fake_open(request, timeout):
        nonlocal called
        called = True
        return _Response(_envelope())

    monkeypatch.setattr(api_providers, "_urlopen", fake_open)
    world = {"state": secret} if location == "world" else {"state": "bounded"}
    observation = secret if location == "observation" else "hello"
    with pytest.raises(InferenceProtocolError, match="runtime credential reached model-visible context"):
        adapter.reason(world, observation)
    assert called is False


def test_provider_response_cannot_reflect_runtime_credential(monkeypatch):
    secret = "provider-reflected-secret-123"
    adapter = _adapter(monkeypatch, secret)
    reflected = _envelope(
        content=json.dumps({"text": f"echo:{secret}", "effect": None})
    )
    monkeypatch.setattr(
        api_providers,
        "_urlopen",
        lambda request, timeout: _Response(reflected),
    )
    with pytest.raises(InferenceProtocolError, match="response contains runtime credential"):
        adapter.reason({}, "hello")
