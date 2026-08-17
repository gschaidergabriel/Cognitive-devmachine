from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clayverse import terminal_gateway


@dataclass
class _Binding:
    user_id: str


class _Manager:
    def binding(self, user_id: str):
        return _Binding(user_id=user_id)

    def _tmux_argv(self, binding: _Binding, *args: str):
        return ["tmux", "-L", f"clayverse-{binding.user_id}", *args]


class _Completed:
    def __init__(self, returncode: int):
        self.returncode = returncode


def test_terminal_readiness_requires_both_canonical_managed_sessions(monkeypatch):
    calls = []

    def all_live(argv, **kwargs):
        calls.append((argv, kwargs))
        return _Completed(0)

    monkeypatch.setattr(terminal_gateway.subprocess, "run", all_live)
    assert terminal_gateway._terminal_sessions_ready(_Manager()) is True
    assert [call[0][2] for call in calls] == ["clayverse-gabriel", "clayverse-andreas"]
    assert all(call[1]["timeout"] == 2 for call in calls)
    assert all(call[1]["check"] is False for call in calls)

    def andreas_dead(argv, **kwargs):
        return _Completed(1 if argv[2] == "clayverse-andreas" else 0)

    monkeypatch.setattr(terminal_gateway.subprocess, "run", andreas_dead)
    assert terminal_gateway._terminal_sessions_ready(_Manager()) is False


def test_readyz_runs_combined_state_and_terminal_probe_off_event_loop():
    root = Path(__file__).parents[1]
    source = (root / "clayverse" / "terminal_gateway.py").read_text()
    assert "def _runtime_ready(db: UnifiedDB, terminals: TerminalSessionManager)" in source
    assert "return state_ready and _terminal_sessions_ready(terminals)" in source
    assert "ready = await asyncio.to_thread(_runtime_ready, db, terminals)" in source
