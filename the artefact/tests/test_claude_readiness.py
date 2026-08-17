import pytest

import clayverse.readiness as readiness


class FakeInference:
    def __init__(self, available=True):
        self._available = available

    def available(self):
        return self._available


def _programs(monkeypatch, *, tmux=True):
    monkeypatch.setattr(readiness.shutil, "which", lambda name: f"/usr/bin/{name}" if (name != "tmux" or tmux) else None)
    monkeypatch.setattr(readiness, "_command_ok", lambda argv, timeout=5: True)


def test_interactive_readiness_does_not_require_anthropic_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _programs(monkeypatch)
    status = readiness.claude_readiness(FakeInference(True), required=True)
    assert status.as_dict() == {
        "binary_available": True,
        "tmux_available": True,
        "interactive_cli_version_ok": True,
        "authenticated_runtime_verified": False,
    }


def test_required_interactive_cli_fails_closed_without_binary(monkeypatch):
    _programs(monkeypatch)
    with pytest.raises(RuntimeError, match="CLI is required"):
        readiness.claude_readiness(FakeInference(False), required=True)


def test_required_interactive_cli_fails_closed_without_tmux(monkeypatch):
    _programs(monkeypatch, tmux=False)
    with pytest.raises(RuntimeError, match="tmux"):
        readiness.claude_readiness(FakeInference(True), required=True)


def test_required_interactive_cli_fails_closed_when_version_probe_fails(monkeypatch):
    _programs(monkeypatch)
    monkeypatch.setattr(readiness, "_command_ok", lambda argv, timeout=5: False)
    with pytest.raises(RuntimeError, match="version probe"):
        readiness.claude_readiness(FakeInference(True), required=True)


def test_optional_readiness_never_claims_authenticated_runtime(monkeypatch):
    monkeypatch.setattr(readiness.shutil, "which", lambda name: None)
    status = readiness.claude_readiness(FakeInference(False), required=False)
    assert status.binary_available is False
    assert status.tmux_available is False
    assert status.interactive_cli_version_ok is False
    assert status.authenticated_runtime_verified is False
