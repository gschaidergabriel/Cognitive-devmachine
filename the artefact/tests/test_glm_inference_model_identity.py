import json

import pytest

from clayverse.glm_inference import GLMInferenceError, GLMTokenInference


class _Response:
    def __init__(self, model):
        self.raw = json.dumps(
            {"model": model, "choices": [{"message": {"content": "hello"}}]}
        ).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.raw[:limit]


class _Opener:
    def __init__(self, model):
        self.model = model

    def open(self, request, timeout):
        return _Response(self.model)


def test_provider_response_model_must_match_requested_model():
    inference = GLMTokenInference(
        api_token="token",
        model="glm-5.2",
        opener=_Opener("glm-4.7"),
    )
    with pytest.raises(GLMInferenceError, match="does not match requested model"):
        inference.reason({}, "hello")


def test_provider_response_exact_requested_model_is_accepted():
    inference = GLMTokenInference(
        api_token="token",
        model="glm-5.2",
        opener=_Opener("glm-5.2"),
    )
    assert inference.reason({}, "hello")["model"] == "glm-5.2"
