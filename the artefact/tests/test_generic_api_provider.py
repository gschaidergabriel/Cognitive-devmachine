import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from clayverse import api_providers
from clayverse.api_providers import (
    ChatCompletionsProviderConfig,
    GenericChatCompletionsInference,
    build_api_inference_from_env,
)
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


def _provider(monkeypatch, *, effect=None, finish_reason="stop"):
    secret = "mistral-secret-never-persist"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-small-latest")

    captured = {}

    def fake_open(request, timeout):
        captured["authorization"] = request.get_header("Authorization")
        captured["body"] = json.loads(request.data)
        return _Response(
            {
                "id": "resp-1",
                "model": "mistral-small-latest",
                "choices": [
                    {
                        "finish_reason": finish_reason,
                        "message": {
                            "content": json.dumps(
                                {"text": "provider-ok", "effect": effect}
                            )
                        },
                    }
                ],
            }
        )

    monkeypatch.setattr(api_providers, "_urlopen", fake_open)
    return secret, captured, build_api_inference_from_env()


def test_mistral_profile_runs_same_fail_closed_decision_protocol(monkeypatch):
    secret, captured, adapter = _provider(monkeypatch)
    decision = adapter.reason({"state": "bounded"}, "hello")

    assert decision["text"] == "provider-ok"
    assert decision["effect"] is None
    assert decision["inference_receipt"]["provider"] == "mistral"
    assert decision["inference_receipt"]["protocol"] == "chat-completions-json-v1"
    assert captured["authorization"] == f"Bearer {secret}"
    assert captured["body"]["model"] == "mistral-small-latest"
    assert secret not in json.dumps(decision, sort_keys=True)
    assert secret not in repr(adapter.__dict__)


def test_provider_can_only_propose_entityos_effect(monkeypatch):
    _, _, adapter = _provider(
        monkeypatch,
        effect={"capability": "entityos.exec", "target": "terminal", "argv": ["/bin/true"]},
    )
    decision = adapter.reason({"state": "bounded"}, "run the admitted probe")
    assert decision["selection"] == "request_effect"
    assert decision["effect"]["capability"] == "entityos.exec"


def test_forbidden_provider_effect_fails_closed(monkeypatch):
    _, _, adapter = _provider(
        monkeypatch,
        effect={"capability": "process.exec", "target": "host", "argv": ["id"]},
    )
    with pytest.raises(InferenceProtocolError, match="forbidden capability"):
        adapter.reason({"state": "bounded"}, "bad proposal")


def test_openai_compatible_profile_uses_dedicated_generic_secret(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "openai-compatible")
    monkeypatch.setenv("CLAYVERSE_LLM_API_NAME", "example-provider")
    monkeypatch.setenv("CLAYVERSE_LLM_API_ENDPOINT", "https://llm.example.test/v1/chat/completions")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "model-1")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "generic-secret")
    adapter = build_api_inference_from_env()
    assert adapter.config.provider == "example-provider"
    assert adapter.config.token_env == "CLAYVERSE_LLM_API_TOKEN"
    assert adapter.available() is True


def test_generic_endpoint_rejects_credential_or_query_smuggling():
    for endpoint in (
        "http://llm.example.test/v1/chat/completions",
        "https://user:pass@llm.example.test/v1/chat/completions",
        "https://llm.example.test/v1/chat/completions?token=x",
        "https://llm.example.test/v1/chat/completions#fragment",
    ):
        with pytest.raises(ValueError):
            ChatCompletionsProviderConfig(
                provider="example",
                endpoint=endpoint,
                model="model-1",
                token_env="CLAYVERSE_LLM_API_TOKEN",
            )


def test_arbitrary_environment_secret_names_are_not_allowed():
    with pytest.raises(ValueError, match="unapproved"):
        ChatCompletionsProviderConfig(
            provider="example",
            endpoint="https://llm.example.test/v1/chat/completions",
            model="model-1",
            token_env="AWS_SECRET_ACCESS_KEY",
        )


def test_non_stop_completion_fails_closed(monkeypatch):
    _, _, adapter = _provider(monkeypatch, finish_reason="length")
    with pytest.raises(InferenceProtocolError, match="did not finish cleanly"):
        adapter.reason({}, "hello")


def test_http_failure_does_not_echo_provider_secret(monkeypatch):
    secret = "TOP_SECRET_PROVIDER_TOKEN"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-small-latest")
    adapter = build_api_inference_from_env()

    def fake_open(request, timeout):
        raise HTTPError(request.full_url, 401, secret, hdrs=None, fp=None)

    monkeypatch.setattr(api_providers, "_urlopen", fake_open)
    with pytest.raises(RuntimeError) as exc:
        adapter.reason({}, "hello")
    assert "status=401" in str(exc.value)
    assert secret not in str(exc.value)


def test_malformed_and_oversized_provider_responses_fail_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    monkeypatch.setenv("CLAYVERSE_LLM_API_PROFILE", "mistral")
    monkeypatch.setenv("CLAYVERSE_LLM_API_MODEL", "mistral-small-latest")
    adapter = build_api_inference_from_env()

    monkeypatch.setattr(api_providers, "_urlopen", lambda request, timeout: _Response(b"not-json", raw=True))
    with pytest.raises(InferenceProtocolError, match="envelope is not JSON"):
        adapter.reason({}, "hello")

    oversized = b"x" * (GenericChatCompletionsInference.MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(api_providers, "_urlopen", lambda request, timeout: _Response(oversized, raw=True))
    with pytest.raises(InferenceProtocolError, match="exceeds bound"):
        adapter.reason({}, "hello")


def test_redirect_handler_refuses_bearer_token_forwarding():
    secret = "redirect-sensitive-secret"
    request = Request(
        "https://llm.example.test/v1/chat/completions",
        data=b"{}",
        headers={"Authorization": f"Bearer {secret}"},
        method="POST",
    )
    handler = api_providers._NoRedirectHandler()
    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://attacker.invalid/collect",
    )
    assert redirected is None
    assert request.get_header("Authorization") == f"Bearer {secret}"
