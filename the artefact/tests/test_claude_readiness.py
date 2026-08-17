import pytest

from clayverse.readiness import claude_readiness


class FakeInference:
    def __init__(self, available=True):
        self._available = available

    def available(self):
        return self._available


def test_required_bare_inference_fails_closed_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        claude_readiness(FakeInference(True), required=True)


def test_required_bare_inference_fails_closed_without_binary(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with pytest.raises(RuntimeError, match="CLI is required"):
        claude_readiness(FakeInference(False), required=True)


def test_bare_readiness_reports_configuration_without_claiming_runtime_verification(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    status = claude_readiness(FakeInference(True), required=True)
    assert status.as_dict() == {
        "binary_available": True,
        "bare_api_key_configured": True,
        "authenticated_runtime_verified": False,
    }


def test_optional_claude_reports_missing_configuration_without_admitting_verified(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    status = claude_readiness(FakeInference(False), required=False)
    assert status.binary_available is False
    assert status.bare_api_key_configured is False
    assert status.authenticated_runtime_verified is False
