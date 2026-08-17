import urllib.error

import pytest

from clayverse.mistral_inference import MistralInferenceError, MistralTokenInference


TOKEN = "mistral-final-test-secret-ASCII-123"
FIXED_MODEL = "mistral-small-2603"


class FailingOpener:
    def __init__(self, error):
        self.error = error

    def open(self, request, timeout):
        raise self.error


def test_final_acceptance_rejects_moving_latest_alias():
    with pytest.raises(MistralInferenceError, match="requires a fixed Mistral model identifier"):
        MistralTokenInference(
            api_token=TOKEN,
            model="mistral-small-latest",
            final_acceptance=True,
        )


def test_final_acceptance_admits_current_fixed_model_identifier():
    client = MistralTokenInference(
        api_token=TOKEN,
        model=FIXED_MODEL,
        final_acceptance=True,
    )
    assert client.model == FIXED_MODEL
    assert client.final_acceptance is True
    assert TOKEN not in repr(client)


def test_final_acceptance_flag_is_strict_boolean_contract():
    for value in ("", "true", "yes", "2"):
        with pytest.raises(MistralInferenceError, match="final acceptance mode is invalid"):
            MistralTokenInference(
                api_token=TOKEN,
                model=FIXED_MODEL,
                final_acceptance=value,
            )


def test_explicit_empty_endpoint_never_falls_back_to_default():
    with pytest.raises(MistralInferenceError):
        MistralTokenInference(
            api_token=TOKEN,
            model=FIXED_MODEL,
            endpoint="",
        )


def test_transport_error_does_not_retain_provider_controlled_context():
    provider_error = urllib.error.URLError(f"transport leaked {TOKEN}")
    client = MistralTokenInference(
        api_token=TOKEN,
        model=FIXED_MODEL,
        opener=FailingOpener(provider_error),
    )
    with pytest.raises(MistralInferenceError) as caught:
        client.reason({}, "question")
    assert str(caught.value) == "Mistral inference transport failed"
    assert TOKEN not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
