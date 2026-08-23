from __future__ import annotations

import pytest

from clayverse.terminal_hooks import TerminalHookError, _runtime


@pytest.mark.parametrize("session_value", [None, "", "   "])
def test_hook_runtime_requires_explicit_managed_session_binding(
    tmp_path, monkeypatch, session_value
):
    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path))
    monkeypatch.setenv("CLAYVERSE_USER_ID", "gabriel")
    if session_value is None:
        monkeypatch.delenv("CLAYVERSE_SESSION_ID", raising=False)
    else:
        monkeypatch.setenv("CLAYVERSE_SESSION_ID", session_value)

    with pytest.raises(TerminalHookError, match="terminal session identity is missing"):
        _runtime()

    # Identity admission must fail before opening/creating the canonical database.
    assert not (tmp_path / "unified.db").exists()
