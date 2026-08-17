import pytest

from clayverse.final_acceptance_mistral_config import validate_final_mistral_runtime_config


def _set_valid(monkeypatch):
    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", "mistral-small-2603")
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-final-secret-ASCII-123")


def test_final_mistral_runtime_config_accepts_fixed_model(monkeypatch):
    _set_valid(monkeypatch)
    assert validate_final_mistral_runtime_config() == "mistral-small-2603"


def test_final_mistral_runtime_config_rejects_latest_alias(monkeypatch):
    _set_valid(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", "mistral-small-latest")
    with pytest.raises(RuntimeError, match="fixed visible-ASCII model identifier"):
        validate_final_mistral_runtime_config()


@pytest.mark.parametrize(
    "model",
    ["", " mistral-small-2603", "mistral small 2603", "mistral-small-2603\n", "mistral-small-é"],
)
def test_final_mistral_runtime_config_rejects_invalid_model(monkeypatch, model):
    _set_valid(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", model)
    with pytest.raises(RuntimeError, match="fixed visible-ASCII model identifier"):
        validate_final_mistral_runtime_config()


@pytest.mark.parametrize(
    "token",
    ["", " leading-space", "trailing-space ", "tab\tinside", "line\nbreak", "é"],
)
def test_final_mistral_runtime_config_rejects_non_header_safe_secret(monkeypatch, token):
    _set_valid(monkeypatch)
    monkeypatch.setenv("MISTRAL_API_KEY", token)
    with pytest.raises(RuntimeError, match="MISTRAL_API_KEY is missing or invalid"):
        validate_final_mistral_runtime_config()


def test_final_mistral_runtime_config_error_never_contains_secret(monkeypatch):
    secret = "secret-with-tab\tSHOULD_NOT_APPEAR"
    monkeypatch.setenv("CLAYVERSE_MISTRAL_MODEL", "mistral-small-2603")
    monkeypatch.setenv("MISTRAL_API_KEY", secret)
    with pytest.raises(RuntimeError) as caught:
        validate_final_mistral_runtime_config()
    assert secret not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
