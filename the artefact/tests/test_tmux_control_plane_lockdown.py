from __future__ import annotations

from pathlib import Path

from clayverse.terminal_sessions import TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_managed_tmux_policy_removes_interactive_control_plane():
    policy = (ROOT / "policy" / "tmux.conf").read_text(encoding="utf-8")
    assert "set-option -g prefix None" in policy
    assert "set-option -g prefix2 None" in policy
    assert "unbind-key -a" in policy
    assert "set-option -g mouse off" in policy
    assert "set-option -g default-command /opt/clayverse/runtime/deny-shell" in policy


def test_terminal_manager_never_uses_user_tmux_configuration():
    assert TerminalSessionManager.MANAGED_TMUX == Path("/etc/clayverse/tmux.conf")
    manager = TerminalSessionManager("/tmp/state", "/tmp/workspace")
    binding = manager.binding("gabriel")
    argv = manager._tmux_argv(binding, "attach-session", "-t", binding.tmux_name)
    assert argv[:3] == ["tmux", "-f", "/etc/clayverse/tmux.conf"]
    assert "~/.tmux.conf" not in " ".join(argv)


def test_container_installs_managed_tmux_policy_read_only():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chown=root:root policy/tmux.conf /etc/clayverse/tmux.conf" in dockerfile
    assert "chmod 0444 /etc/clayverse/tmux.conf" in dockerfile
    assert "mkdir -p /etc/claude-code /etc/clayverse" in dockerfile
