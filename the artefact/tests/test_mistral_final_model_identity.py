import pytest

from clayverse.mistral_inference import MistralInferenceError, MistralTokenInference


TOKEN = "mistral-test-secret-ASCII-123"


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
