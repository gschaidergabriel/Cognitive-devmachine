import io
import json
import urllib.error

import pytest

from clayverse.glm_inference import DEFAULT_GLM_ENDPOINT, GLMInferenceError, GLMTokenInference


class _RawResponse:
    def __init__(self, raw: bytes): self._raw = raw
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def read(self, limit: int) -> bytes: return self._raw[:limit]


class _Opener:
    def __init__(self, raw: bytes): self.raw = raw; self.request = None
    def open(self, request, timeout): self.request = request; return _RawResponse(self.raw)


def _ok(model="glm-5.2", text="hello"):
    return json.dumps({"model": model, "choices": [{"message": {"content": text}}]}).encode()


def test_retained_endpoint_token_effect_boundary():
    secret = "glm-secret-token-value"
    opener = _Opener(_ok())
    inference = GLMTokenInference(api_token=secret, opener=opener)
    result = inference.reason({"canonical":"state"}, "respond")
    assert opener.request.full_url == DEFAULT_GLM_ENDPOINT
    assert opener.request.get_header("Authorization") == f"Bearer {secret}"
    assert secret.encode() not in opener.request.data
    body = json.loads(opener.request.data)
    assert "tools" not in body and "tool_choice" not in body
    assert result["effect"] is None and result["provider"] == "glm" and result["model"] == "glm-5.2"


def test_retained_nonfinite_and_model_drift_fences():
    inference = GLMTokenInference(api_token="token", opener=_Opener(_ok()))
    with pytest.raises(GLMInferenceError, match="not canonical JSON"):
        inference.reason({"x": float("nan")}, "hello")
    mismatch = GLMTokenInference(api_token="token", model="glm-5.2", opener=_Opener(_ok(model="glm-4.7")))
    with pytest.raises(GLMInferenceError, match="does not match"):
        mismatch.reason({}, "hello")


def test_bearer_secret_cannot_reenter_world_or_observation_body():
    secret = "glm-secret-token-value"
    opener = _Opener(_ok())
    inference = GLMTokenInference(api_token=secret, opener=opener)
    with pytest.raises(GLMInferenceError, match="credential appeared in inference content"):
        inference.reason({"accidental_secret": secret}, "hello")
    assert opener.request is None
    with pytest.raises(GLMInferenceError, match="credential appeared in inference content"):
        inference.reason({}, f"hello {secret}")
    assert opener.request is None


def test_provider_controlled_invalid_json_is_detached_from_error_object():
    opener = _Opener(b'{"sensitive":"provider-controlled-fragment"')
    inference = GLMTokenInference(api_token="token", opener=opener)
    with pytest.raises(GLMInferenceError, match="not valid canonical JSON") as caught:
        inference.reason({}, "hello")
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


def test_http_error_provider_body_stays_suppressed():
    class _ErrorOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 500, "provider failure", None, io.BytesIO(b"provider-secret-body"))
    inference = GLMTokenInference(api_token="token", opener=_ErrorOpener())
    with pytest.raises(GLMInferenceError) as caught:
        inference.reason({}, "hello")
    assert caught.value.__cause__ is None


def test_provider_response_cannot_emit_bearer_secret():
    secret = "glm-secret-token-value"
    inference = GLMTokenInference(api_token=secret, opener=_Opener(_ok(text=f"oops {secret}")))
    with pytest.raises(GLMInferenceError, match="credential appeared in provider response"):
        inference.reason({}, "hello")
