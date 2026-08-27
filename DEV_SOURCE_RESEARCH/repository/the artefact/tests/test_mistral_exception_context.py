import io
from urllib.error import HTTPError, URLError

import pytest

import clayverse.adapters as adapters
from clayverse.adapters import MistralInference


def test_mistral_http_error_severs_provider_exception_context(monkeypatch):
    secret = "provider-secret-must-not-be-reachable"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)

    def fail(request, timeout):
        raise HTTPError(
            request.full_url,
            401,
            f"provider-message-{secret}",
            hdrs=None,
            fp=io.BytesIO(f"provider-body-{secret}".encode()),
        )

    monkeypatch.setattr(adapters, "urlopen", fail)
    with pytest.raises(RuntimeError) as caught:
        MistralInference(model="model-x").reason({}, "hello")

    assert str(caught.value) == "Mistral inference HTTP failure status=401"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in str(caught.value)


def test_mistral_transport_error_severs_provider_exception_context(monkeypatch):
    secret = "transport-secret-must-not-be-reachable"
    monkeypatch.setenv("MISTRAL_API_KEY", secret)

    def fail(request, timeout):
        raise URLError(RuntimeError(secret))

    monkeypatch.setattr(adapters, "urlopen", fail)
    with pytest.raises(RuntimeError) as caught:
        MistralInference(model="model-x").reason({}, "hello")

    assert str(caught.value) == "Mistral inference transport failure type=URLError"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert secret not in str(caught.value)
