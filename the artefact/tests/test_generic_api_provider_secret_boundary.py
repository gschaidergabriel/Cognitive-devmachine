import json

import pytest

from clayverse import api_providers
from clayverse.api_providers import build_api_inference_from_env
from clayverse.inference_protocol import InferenceProtocolError


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

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


def _envelope(content):
    return {
        "id": "resp-1",
        "model": "mistral-small-latest",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": content},
            }
        ],
    }


@pytest.mark.parametrize("location", ["world", "observation"])
def test_runtime_credential_never_enters_model_visible_context(monkeypatch, location):
    secret = "model-visible-secret-123"
    adapter = _adapter(monkeypatch, secret)
    called = False

    def fake_open(request, timeout):
        nonlocal called
        called = True
        return _Response(_envelope(json.dumps({"text": "ok", "effect": None})))

    monkeypatch.setattr(api_providers, "_urlopen", fake_open)
    world = {"state": secret} if location == "world" else {"state": "bounded"}
    observation = secret if location == "observation" else "hello"

    with pytest.raises(
        InferenceProtocolError,
        match="runtime credential reached model-visible context",
    ):
        adapter.reason(world, observation)
    assert called is False


def test_provider_response_cannot_reflect_runtime_credential(monkeypatch):
    secret = "provider-reflected-secret-123"
    adapter = _adapter(monkeypatch, secret)
    reflected = _envelope(json.dumps({"text": f"echo:{secret}", "effect": None}))
    monkeypatch.setattr(
        api_providers,
        "_urlopen",
        lambda request, timeout: _Response(reflected),
    )

    with pytest.raises(
        InferenceProtocolError,
        match="response contains runtime credential",
    ):
        adapter.reason({}, "hello")


def test_provider_token_must_be_visible_ascii(monkeypatch):
    adapter = _adapter(monkeypatch, "token-with-unicode-ä")
    monkeypatch.setattr(
        api_providers,
        "_urlopen",
        lambda request, timeout: pytest.fail("transport must not run"),
    )
    with pytest.raises(RuntimeError, match="token is required at runtime"):
        adapter.reason({}, "hello")
