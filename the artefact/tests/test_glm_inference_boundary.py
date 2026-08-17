import io
import json
import urllib.error

import pytest

from clayverse.glm_inference import (
    DEFAULT_GLM_ENDPOINT,
    GLMInferenceError,
    GLMTokenInference,
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit: int) -> bytes:
        return self._raw[:limit]


class _CapturingOpener:
    def __init__(self, payload: dict):
        self.payload = payload
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return _FakeResponse(self.payload)


def test_glm_token_is_header_only_and_model_has_no_effect_authority():
    secret = "glm-secret-token-value"
    opener = _CapturingOpener(
        {
            "model": "glm-5.2",
            "choices": [{"message": {"role": "assistant", "content": "hello"}}],
        }
    )
    inference = GLMTokenInference(
        api_token=secret,
        model="glm-5.2",
        opener=opener,
    )

    decision = inference.reason({"canonical": "state"}, "respond")

    assert decision == {
        "text": "hello",
        "selection": "respond",
        "effect": None,
        "provider": "glm",
        "model": "glm-5.2",
    }
    assert opener.request.full_url == DEFAULT_GLM_ENDPOINT
    assert opener.request.get_header("Authorization") == f"Bearer {secret}"
    assert secret.encode() not in opener.request.data
    body = json.loads(opener.request.data)
    assert body["stream"] is False
    assert "tools" not in body
    assert "tool_choice" not in body
    assert [message["role"] for message in body["messages"]] == ["system", "user"]
    assert "no tools" in body["messages"][0]["content"]
    assert "EntityOS" in body["messages"][0]["content"]
    assert secret not in repr(inference)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://open.bigmodel.cn/api/paas/v4/chat/completions",
        "https://evil.example/api/paas/v4/chat/completions",
        "https://open.bigmodel.cn/api/paas/v4/chat/completions?redirect=evil",
        "https://user@open.bigmodel.cn/api/paas/v4/chat/completions",
        "https://open.bigmodel.cn:443/api/paas/v4/chat/completions",
        "https://open.bigmodel.cn/api/paas/v4/other",
    ],
)
def test_glm_endpoint_fails_closed_outside_exact_provider_boundary(endpoint):
    with pytest.raises(GLMInferenceError, match="outside the admitted provider boundary"):
        GLMTokenInference(api_token="token", endpoint=endpoint)


def test_glm_rejects_non_glm_model_id():
    with pytest.raises(GLMInferenceError, match="model identifier is invalid"):
        GLMTokenInference(api_token="token", model="other-provider-model")


def test_glm_rejects_control_characters_in_token():
    with pytest.raises(GLMInferenceError, match="missing or malformed"):
        GLMTokenInference(api_token="token\nsecond-line")


def test_glm_http_failure_does_not_surface_provider_body():
    class _ErrorOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                500,
                "provider failure",
                hdrs=None,
                fp=io.BytesIO(b"secret-derived-provider-body"),
            )

    inference = GLMTokenInference(api_token="token", opener=_ErrorOpener())
    with pytest.raises(GLMInferenceError) as caught:
        inference.reason({}, "hello")
    assert "secret-derived-provider-body" not in str(caught.value)
    assert "token" not in str(caught.value)


def test_glm_world_boundary_is_bounded_before_network():
    opener = _CapturingOpener(
        {"choices": [{"message": {"content": "unused"}}]}
    )
    inference = GLMTokenInference(api_token="token", opener=opener)
    with pytest.raises(GLMInferenceError, match="assembled world exceeds"):
        inference.reason({"x": "a" * 600_001}, "hello")
    assert opener.request is None
