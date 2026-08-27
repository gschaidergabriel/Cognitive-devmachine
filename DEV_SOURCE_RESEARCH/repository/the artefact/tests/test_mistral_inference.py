import json
from urllib.error import HTTPError
from urllib.request import Request

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


def mistral_envelope(
    decision,
    *,
    model="model-bound-for-test",
    response_id="cmpl-test",
    finish_reason="stop",
):
    return json.dumps(
        {
            "id": response_id,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(decision, separators=(",", ":")),
                    },
                }
            ],
        }
    ).encode()


def test_mistral_requires_runtime_secret_and_explicit_model(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.delenv("CLAYVERSE_MISTRAL_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="CLAYVERSE_MISTRAL_MODEL"):
        MistralInference().reason({}, "hello")

    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", "model-x")
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY"):
        MistralInference().reason({}, "hello")


def test_mistral_request_is_fixed_endpoint_toolless_json_mode_and_secret_is_not_retained(monkeypatch):
    secret = "vault-only-secret-value"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["body_bytes"] = request.data
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(mistral_envelope({"text": "ok", "effect": None}))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    adapter = MistralInference(model="model-bound-for-test", timeout=9)
    out = adapter.reason({"shared": "state"}, "hello")

    assert captured["url"] == "https://api.mistral.ai/v1/chat/completions"
    assert captured["auth"] == f"Bearer {secret}"
    assert captured["timeout"] == 9
    assert captured["body"]["model"] == "model-bound-for-test"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["tools"] == []
    assert captured["body"]["tool_choice"] == "none"
    assert captured["body"]["parallel_tool_calls"] is False
    assert captured["body"]["stream"] is False
    assert captured["body"]["temperature"] == 0
    assert secret.encode() not in captured["body_bytes"]
    assert set(adapter.__dict__) == {"model", "timeout", "_lock"}
    assert secret not in repr(adapter.__dict__)

    assert out["text"] == "ok"
    assert out["selection"] == "respond"
    assert out["effect"] is None
    receipt = out["inference_receipt"]
    assert receipt["provider"] == "mistral"
    assert receipt["model_requested"] == "model-bound-for-test"
    assert receipt["model_returned"] == "model-bound-for-test"
    assert receipt["response_id"] == "cmpl-test"
    assert receipt["finish_reason"] == "stop"
    assert len(receipt["request_sha256"]) == 64
    assert len(receipt["response_sha256"]) == 64
    assert secret not in json.dumps(out, sort_keys=True)


def test_mistral_effect_is_only_schema_validated_intent(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")

    def fake_urlopen(request, timeout):
        return FakeResponse(
            mistral_envelope(
                {
                    "text": "request",
                    "effect": {
                        "capability": "entityos.exec",
                        "target": "test",
                        "argv": ["status"],
                    },
                },
                model="model-x",
            )
        )

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    out = MistralInference(model="model-x").reason({}, "status")
    assert out["selection"] == "request_effect"
    assert out["effect"] == {
        "capability": "entityos.exec",
        "target": "test",
        "argv": ["status"],
    }
    assert out["inference_receipt"]["provider"] == "mistral"


def test_mistral_forbidden_capability_fails_before_effectgate(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")

    def fake_urlopen(request, timeout):
        return FakeResponse(
            mistral_envelope(
                {
                    "text": "bad",
                    "effect": {
                        "capability": "process.exec",
                        "target": "host",
                        "argv": ["id"],
                    },
                },
                model="model-x",
            )
        )

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    with pytest.raises(InferenceProtocolError, match="forbidden capability"):
        MistralInference(model="model-x").reason({}, "run id")


def test_mistral_non_stop_completion_fails_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: FakeResponse(
            mistral_envelope(
                {"text": "partial", "effect": None},
                model="model-x",
                finish_reason="length",
            )
        ),
    )
    with pytest.raises(InferenceProtocolError, match="did not finish cleanly"):
        MistralInference(model="model-x").reason({}, "hello")


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


def test_mistral_missing_response_identity_fails_closed(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "secret")
    raw = json.dumps(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": json.dumps({"text": "ok", "effect": None})},
                }
            ]
        }
    ).encode()
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(raw))
    with pytest.raises(InferenceProtocolError, match="response id"):
        MistralInference(model="model-x").reason({}, "hello")


def test_mistral_redirect_handler_refuses_new_request_with_bearer_token():
    secret = "redirect-sensitive-secret"
    request = Request(
        MistralInference.ENDPOINT,
        data=b"{}",
        headers={"Authorization": f"Bearer {secret}"},
        method="POST",
    )
    handler = adapters._MistralNoRedirectHandler()
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


def test_mistral_runtime_urlopen_installs_no_redirect_handler(monkeypatch):
    captured = {}

    class FakeOpener:
        def open(self, request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            raise HTTPError(request.full_url, 302, "Found", hdrs=None, fp=None)

    def fake_build_opener(*handlers):
        captured["handlers"] = handlers
        return FakeOpener()

    monkeypatch.setattr(adapters, "build_opener", fake_build_opener)
    request = Request(MistralInference.ENDPOINT, data=b"{}", method="POST")
    with pytest.raises(HTTPError) as exc:
        adapters.urlopen(request, timeout=7)
    assert exc.value.code == 302
    assert len(captured["handlers"]) == 1
    assert isinstance(captured["handlers"][0], adapters._MistralNoRedirectHandler)
    assert captured["request"] is request
    assert captured["timeout"] == 7
