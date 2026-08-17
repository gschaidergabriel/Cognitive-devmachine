import urllib.error

import pytest

from clayverse.mistral_inference import MistralInferenceError, MistralTokenInference


TOKEN = "mistral-test-secret-ASCII-123"


class FailingOpener:
    def __init__(self, error):
        self.error = error

    def open(self, request, timeout):
        raise self.error


def test_final_acceptance_rejects_latest_alias():
    with pytest.raises(
        MistralInferenceError,
        match="final acceptance requires a fixed Mistral model identifier",
    ):
        MistralTokenInference(
            api_token=TOKEN,
            model="mistral-small-latest",
            final_acceptance=True,
        )


def test_final_acceptance_accepts_fixed_model_identifier():
    inference = MistralTokenInference(
        api_token=TOKEN,
        model="mistral-small-2603",
        final_acceptance=True,
    )
    assert inference.model == "mistral-small-2603"
    assert inference.final_acceptance is True
    assert TOKEN not in repr(inference)


def test_development_mode_may_keep_latest_alias():
    inference = MistralTokenInference(
        api_token=TOKEN,
        model="mistral-small-latest",
        final_acceptance=False,
    )
    assert inference.model == "mistral-small-latest"
    assert inference.final_acceptance is False


def test_final_acceptance_env_must_be_explicit_boolean(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_FINAL_ACCEPTANCE", "maybe")
    with pytest.raises(MistralInferenceError, match="final acceptance mode is invalid"):
        MistralTokenInference(api_token=TOKEN, model="mistral-small-2603")


def test_final_acceptance_env_rejects_latest_alias(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_FINAL_ACCEPTANCE", "1")
    with pytest.raises(
        MistralInferenceError,
        match="final acceptance requires a fixed Mistral model identifier",
    ):
        MistralTokenInference(api_token=TOKEN, model="mistral-small-latest")


def test_explicit_empty_endpoint_never_falls_back_to_default():
    with pytest.raises(MistralInferenceError):
        MistralTokenInference(
            api_token=TOKEN,
            model="mistral-small-2603",
            endpoint="",
        )


def test_transport_error_does_not_retain_provider_controlled_context():
    provider_error = urllib.error.URLError(f"transport leaked {TOKEN}")
    inference = MistralTokenInference(
        api_token=TOKEN,
        model="mistral-small-2603",
        opener=FailingOpener(provider_error),
    )
    with pytest.raises(MistralInferenceError) as caught:
        inference.reason({}, "question")
    assert str(caught.value) == "Mistral inference transport failed"
    assert TOKEN not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
