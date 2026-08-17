import hashlib
import json

import pytest

from clayverse.glm_client import GLMConfigError, GLMInferenceClient, GLMInferenceError


def _response(*, text="answer", model="glm-5.2", request_id="req-1", tool_calls=None):
    message = {"role": "assistant", "content": text}
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return json.dumps(
        {
            "id": "completion-1",
            "request_id": request_id,
            "model": model,
            "choices": [{"index": 0, "message": message}],
        }
    ).encode()


def test_glm_client_uses_pinned_official_bearer_endpoint_and_preserves_causal_identity():
    seen = {}

    def transport(request, timeout, max_bytes):
        seen["request"] = request
        seen["timeout"] = timeout
        seen["max_bytes"] = max_bytes
        return 200, _response()

    token = "secret.token.value"
    client = GLMInferenceClient(token=token, model="glm-5.2", transport=transport)
    result = client.infer(
        context={"durable_memory": [{"content": "known"}]},
        observation="continue the task",
        turn_id="turn-1",
        causal_id="causal-1",
        generation=7,
    )

    request = seen["request"]
    assert request.full_url == "https://api.z.ai/api/paas/v4/chat/completions"
    assert request.get_header("Authorization") == f"Bearer {token}"
    assert request.get_header("Content-type") == "application/json"
    assert seen["timeout"] == 120.0
    assert seen["max_bytes"] == 2_000_000

    payload = json.loads(request.data)
    assert payload["model"] == "glm-5.2"
    assert payload["stream"] is False
    assert "tools" not in payload
    assert token.encode() not in request.data
    assert "no terminal, filesystem, tool, EntityOS, EffectGate or external-effect authority" in payload["messages"][0]["content"]
    assert "known" in payload["messages"][1]["content"]
    assert "continue the task" in payload["messages"][1]["content"]

    assert result.text == "answer"
    assert result.turn_id == "turn-1"
    assert result.causal_id == "causal-1"
    assert result.generation == 7
    assert result.requested_model == "glm-5.2"
    assert result.provider_model == "glm-5.2"
    assert result.provider_request_id == "req-1"


def test_glm_endpoint_profile_is_pinned_not_arbitrary_token_exfiltration_url():
    with pytest.raises(GLMConfigError, match="pinned official endpoint"):
        GLMInferenceClient(token="secret", model="glm-5.2", endpoint="https://attacker.invalid/v1")

    cn = GLMInferenceClient(token="secret", model="glm-5.2", endpoint="cn", transport=lambda *_: (200, _response()))
    assert cn.url == "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def test_glm_client_requires_explicit_model_and_token_from_environment(monkeypatch):
    monkeypatch.delenv("GLM_API_TOKEN", raising=False)
    monkeypatch.delenv("GLM_MODEL", raising=False)
    with pytest.raises(GLMConfigError):
        GLMInferenceClient.from_env(transport=lambda *_: (200, _response()))

    monkeypatch.setenv("GLM_API_TOKEN", "secret")
    with pytest.raises(GLMConfigError):
        GLMInferenceClient.from_env(transport=lambda *_: (200, _response()))

    monkeypatch.setenv("GLM_MODEL", "glm-5.2")
    client = GLMInferenceClient.from_env(transport=lambda *_: (200, _response()))
    assert client.model == "glm-5.2"
    assert client.endpoint_profile == "global"


def test_glm_tool_calls_fail_closed_and_never_become_effect_authority():
    client = GLMInferenceClient(
        token="secret",
        model="glm-5.2",
        transport=lambda *_: (200, _response(tool_calls=[{"type": "function", "function": {"name": "shell"}}])),
    )
    with pytest.raises(GLMInferenceError, match="tool calls are forbidden"):
        client.infer(context={}, observation="x", turn_id="t", causal_id="c", generation=1)


def test_glm_http_failure_redacts_provider_body_and_token():
    token = "TOP_SECRET_TOKEN"
    body = f'{{"error":"{token}: provider diagnostic"}}'.encode()
    client = GLMInferenceClient(token=token, model="glm-5.2", transport=lambda *_: (401, body))

    with pytest.raises(GLMInferenceError) as excinfo:
        client.infer(context={}, observation="x", turn_id="t", causal_id="c", generation=1)

    message = str(excinfo.value)
    assert token not in message
    assert "provider diagnostic" not in message
    assert hashlib.sha256(body).hexdigest() in message
    assert "status=401" in message


def test_glm_response_and_identity_envelopes_are_bounded_fail_closed():
    oversized = b"x" * 2_000_001
    client = GLMInferenceClient(token="secret", model="glm-5.2", transport=lambda *_: (200, oversized))
    with pytest.raises(GLMInferenceError, match="response exceeds bounded envelope"):
        client.infer(context={}, observation="x", turn_id="t", causal_id="c", generation=1)

    malformed_status = GLMInferenceClient(token="secret", model="glm-5.2", transport=lambda *_: (True, _response()))
    with pytest.raises(GLMInferenceError, match="invalid GLM HTTP status"):
        malformed_status.infer(context={}, observation="x", turn_id="t", causal_id="c", generation=1)

    valid = GLMInferenceClient(token="secret", model="glm-5.2", transport=lambda *_: (200, _response()))
    with pytest.raises(GLMInferenceError, match="invalid generation"):
        valid.infer(context={}, observation="x", turn_id="t", causal_id="c", generation=True)
    with pytest.raises(GLMInferenceError, match="invalid turn_id"):
        valid.infer(context={}, observation="x", turn_id="", causal_id="c", generation=1)
