import json
from urllib.error import HTTPError

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import GLMInference
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


def glm_envelope(decision, *, tool_calls=None):
    message = {
        "role": "assistant",
        "content": json.dumps(decision, separators=(",", ":")),
    }
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return json.dumps({"choices": [{"message": message}]}).encode()


def test_glm_requires_runtime_secret_and_explicit_model(monkeypatch):
    monkeypatch.delenv("GLM_API_TOKEN", raising=False)
    monkeypatch.delenv("CLAYVERSE_GLM_MODEL", raising=False)
    with pytest.raises(RuntimeError, match="CLAYVERSE_GLM_MODEL"):
        GLMInference().reason({}, "hello")

    monkeypatch.setenv("CLAYVERSE_GLM_MODEL", "model-x")
    with pytest.raises(RuntimeError, match="GLM_API_TOKEN"):
        GLMInference().reason({}, "hello")


def test_glm_request_is_fixed_endpoint_json_mode_toolless_and_secret_not_retained(monkeypatch):
    secret = "vault-only-secret-value"
    monkeypatch.setenv("GLM_API_TOKEN", secret)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["body_bytes"] = request.data
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse(glm_envelope({"text": "ok", "effect": None}))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    adapter = GLMInference(model="glm-bound-for-test", timeout=9)
    out = adapter.reason({"shared": "state"}, "hello")

    assert out == {"text": "ok", "selection": "respond", "effect": None}
    assert captured["url"] == "https://api.z.ai/api/paas/v4/chat/completions"
    assert captured["auth"] == f"Bearer {secret}"
    assert captured["timeout"] == 9
    assert captured["body"]["model"] == "glm-bound-for-test"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["stream"] is False
    assert captured["body"]["do_sample"] is False
    assert "tools" not in captured["body"]
    assert secret.encode() not in captured["body_bytes"]
    assert set(adapter.__dict__) == {"model", "timeout", "_lock"}
    assert secret not in repr(adapter.__dict__)


def test_glm_effect_is_only_schema_validated_intent(monkeypatch):
    monkeypatch.setenv("GLM_API_TOKEN", "secret")

    def fake_urlopen(request, timeout):
        return FakeResponse(glm_envelope({
            "text": "request",
            "effect": {
                "capability": "entityos.exec",
                "target": "test",
                "argv": ["status"],
            },
        }))

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    out = GLMInference(model="model-x").reason({}, "status")
    assert out == {
        "text": "request",
        "selection": "request_effect",
        "effect": {
            "capability": "entityos.exec",
            "target": "test",
            "argv": ["status"],
        },
    }


def test_glm_forbidden_capability_and_provider_tool_calls_fail_closed(monkeypatch):
    monkeypatch.setenv("GLM_API_TOKEN", "secret")

    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: FakeResponse(glm_envelope({
            "text": "bad",
            "effect": {"capability": "process.exec", "target": "host", "argv": ["id"]},
        })),
    )
    with pytest.raises(InferenceProtocolError, match="forbidden capability"):
        GLMInference(model="model-x").reason({}, "run id")

    monkeypatch.setattr(
        adapters,
        "urlopen",
        lambda request, timeout: FakeResponse(glm_envelope(
            {"text": "tool", "effect": None},
            tool_calls=[{"type": "function", "function": {"name": "shell"}}],
        )),
    )
    with pytest.raises(InferenceProtocolError, match="tool calls are forbidden"):
        GLMInference(model="model-x").reason({}, "tool")


def test_glm_transport_error_never_echoes_secret(monkeypatch):
    secret = "TOP_SECRET_GLM_TOKEN"
    monkeypatch.setenv("GLM_API_TOKEN", secret)

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 401, secret, hdrs=None, fp=None)

    monkeypatch.setattr(adapters, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError) as exc:
        GLMInference(model="model-x").reason({}, "hello")
    message = str(exc.value)
    assert "status=401" in message
    assert secret not in message


def test_glm_malformed_oversized_and_noncanonical_world_fail_closed(monkeypatch):
    monkeypatch.setenv("GLM_API_TOKEN", "secret")

    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(b"not-json"))
    with pytest.raises(InferenceProtocolError, match="envelope is not JSON"):
        GLMInference(model="model-x").reason({}, "hello")

    oversized = b"x" * (GLMInference.MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(adapters, "urlopen", lambda request, timeout: FakeResponse(oversized))
    with pytest.raises(InferenceProtocolError, match="exceeds bound"):
        GLMInference(model="model-x").reason({}, "hello")

    with pytest.raises(InferenceProtocolError, match="world is not canonical JSON"):
        GLMInference(model="model-x").reason({"opaque": object()}, "hello")
