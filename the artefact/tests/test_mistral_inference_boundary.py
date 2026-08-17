import io
import json
import urllib.error

import pytest

from clayverse.mistral_inference import (
    DEFAULT_MISTRAL_ENDPOINT,
    DEFAULT_MISTRAL_MODEL,
    MistralInferenceError,
    MistralTokenInference,
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


class _RawResponse:
    def __init__(self, raw: bytes):
        self._raw = raw

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


def test_mistral_token_is_header_only_and_model_has_no_effect_authority():
    secret = "mistral-secret-token-value"
    opener = _CapturingOpener(
        {
            "model": DEFAULT_MISTRAL_MODEL,
            "choices": [{"message": {"role": "assistant", "content": "hello"}}],
        }
    )
    inference = MistralTokenInference(api_token=secret, opener=opener)

    decision = inference.reason({"canonical": "state"}, "respond")

    assert decision == {
        "text": "hello",
        "selection": "respond",
        "effect": None,
        "provider": "mistral",
        "model": DEFAULT_MISTRAL_MODEL,
    }
    assert opener.request.full_url == DEFAULT_MISTRAL_ENDPOINT
    assert opener.request.get_header("Authorization") == f"Bearer {secret}"
    assert secret.encode() not in opener.request.data
    body = json.loads(opener.request.data)
    assert body["model"] == DEFAULT_MISTRAL_MODEL
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
        "http://api.mistral.ai/v1/chat/completions",
        "https://evil.example/v1/chat/completions",
        "https://api.mistral.ai/v1/chat/completions?redirect=evil",
        "https://user@api.mistral.ai/v1/chat/completions",
        "https://api.mistral.ai:443/v1/chat/completions",
        "https://api.mistral.ai/v1/other",
    ],
)
def test_mistral_endpoint_fails_closed_outside_exact_provider_boundary(endpoint):
    with pytest.raises(
        MistralInferenceError, match="outside the admitted provider boundary"
    ):
        MistralTokenInference(api_token="token", endpoint=endpoint)


def test_mistral_rejects_non_mistral_model_id():
    with pytest.raises(MistralInferenceError, match="model identifier is invalid"):
        MistralTokenInference(api_token="token", model="other-provider-model")


@pytest.mark.parametrize("token", ["token\nsecond-line", "token-☃"])
def test_mistral_rejects_non_header_safe_token(token):
    with pytest.raises(MistralInferenceError, match="missing or malformed"):
        MistralTokenInference(api_token=token)


def test_mistral_http_failure_suppresses_provider_body_and_exception_chain():
    class _ErrorOpener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(
                request.full_url,
                500,
                "provider failure",
                hdrs=None,
                fp=io.BytesIO(b"secret-derived-provider-body"),
            )

    inference = MistralTokenInference(api_token="token", opener=_ErrorOpener())
    with pytest.raises(MistralInferenceError) as caught:
        inference.reason({}, "hello")
    assert "secret-derived-provider-body" not in str(caught.value)
    assert "token" not in str(caught.value)
    assert caught.value.__cause__ is None


def test_mistral_world_boundary_is_bounded_before_network():
    opener = _CapturingOpener(
        {
            "model": DEFAULT_MISTRAL_MODEL,
            "choices": [{"message": {"content": "unused"}}],
        }
    )
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(MistralInferenceError, match="assembled world exceeds"):
        inference.reason({"x": "a" * 600_001}, "hello")
    assert opener.request is None


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_mistral_rejects_non_finite_world_before_network(non_finite):
    opener = _CapturingOpener(
        {
            "model": DEFAULT_MISTRAL_MODEL,
            "choices": [{"message": {"content": "unused"}}],
        }
    )
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(MistralInferenceError, match="not canonical JSON"):
        inference.reason({"value": non_finite}, "hello")
    assert opener.request is None


def test_mistral_observation_boundary_is_bounded_before_network():
    opener = _CapturingOpener(
        {
            "model": DEFAULT_MISTRAL_MODEL,
            "choices": [{"message": {"content": "unused"}}],
        }
    )
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(MistralInferenceError, match="observation is outside"):
        inference.reason({}, "x" * 100_001)
    assert opener.request is None


def test_mistral_rejects_different_provider_response_model():
    opener = _CapturingOpener(
        {
            "model": "mistral-small-2506",
            "choices": [{"message": {"content": "hello"}}],
        }
    )
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(MistralInferenceError, match="does not match requested model"):
        inference.reason({}, "hello")


def test_mistral_rejects_missing_provider_response_model():
    opener = _CapturingOpener({"choices": [{"message": {"content": "hello"}}]})
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(
        MistralInferenceError, match="model identifier is missing or invalid"
    ):
        inference.reason({}, "hello")


def test_mistral_rejects_non_finite_provider_json():
    class _RawOpener:
        def open(self, request, timeout):
            return _RawResponse(
                b'{"model":"mistral-small-2603","usage":{"total_tokens":NaN},"choices":[{"message":{"content":"hello"}}]}'
            )

    inference = MistralTokenInference(api_token="token", opener=_RawOpener())
    with pytest.raises(MistralInferenceError, match="not valid canonical JSON"):
        inference.reason({}, "hello")


def test_mistral_rejects_non_text_response_content():
    opener = _CapturingOpener(
        {
            "model": DEFAULT_MISTRAL_MODEL,
            "choices": [{"message": {"content": [{"type": "text", "text": "hello"}]}}],
        }
    )
    inference = MistralTokenInference(api_token="token", opener=opener)
    with pytest.raises(MistralInferenceError, match="response content is invalid"):
        inference.reason({}, "hello")
