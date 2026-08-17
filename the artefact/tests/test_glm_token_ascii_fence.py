import pytest

from clayverse.glm_inference import GLMInferenceError, GLMTokenInference


def test_glm_rejects_non_ascii_bearer_token_before_network():
    with pytest.raises(GLMInferenceError, match="missing or malformed"):
        GLMTokenInference(api_token="token-☃")
