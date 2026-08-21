from __future__ import annotations

from types import SimpleNamespace

import pytest

from clayverse.autonomy_dispatch import DISPATCH_PREFIX
from clayverse.terminal_sessions import TerminalBinding, TerminalSessionManager


def _manager(tmp_path, monkeypatch):
    manager = TerminalSessionManager(tmp_path / "state", tmp_path / "workspace")
    binding = TerminalBinding(
        user_id="gabriel",
        session_id="session:gabriel",
        tmux_name="clayverse-gabriel",
        home=tmp_path / "home",
        mcp_config=tmp_path / "home" / "clayverse-mcp.json",
    )
    calls = []
    monkeypatch.setattr(
        manager,
        "assert_detached_idle_claude",
        lambda user_id: (binding, "%0"),
    )

    def fake_tmux(bound, *args):
        calls.append((bound, args))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "_run_tmux", fake_tmux)
    return manager, calls


def test_terminal_autonomy_transport_accepts_only_exact_dispatch_token(tmp_path, monkeypatch):
    manager, calls = _manager(tmp_path, monkeypatch)
    token = f"{DISPATCH_PREFIX}{'a' * 32}"

    manager.dispatch_autonomy_prompt("gabriel", token)

    assert len(calls) == 1
    _binding, args = calls[0]
    assert args == (
        "send-keys", "-t", "%0", "-l", token,
        ";", "send-keys", "-t", "%0", "Enter",
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "ordinary printable text",
        f"{DISPATCH_PREFIX}not-a-valid-nonce",
        f"{DISPATCH_PREFIX}{'A' * 32}",
        f"{DISPATCH_PREFIX}{'a' * 31}",
        f"{DISPATCH_PREFIX}{'a' * 33}",
        f"prefix-before-{DISPATCH_PREFIX}{'a' * 32}",
    ],
)
def test_terminal_autonomy_transport_rejects_non_tokens_before_tmux(tmp_path, monkeypatch, prompt):
    manager, calls = _manager(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="invalid autonomy terminal prompt"):
        manager.dispatch_autonomy_prompt("gabriel", prompt)

    assert calls == []
