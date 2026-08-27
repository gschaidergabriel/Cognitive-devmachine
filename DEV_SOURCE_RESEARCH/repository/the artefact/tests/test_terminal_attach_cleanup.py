from __future__ import annotations

import os
import pty
import signal
from pathlib import Path

import pytest

from clayverse.terminal_sessions import TerminalSessionManager


ROOT = Path(__file__).resolve().parents[1]


def test_close_attach_reaps_transient_pty_child():
    pid, fd = pty.fork()
    if pid == 0:
        signal.pause()
        os._exit(0)

    try:
        TerminalSessionManager.close_attach(pid, fd)
        # A child already reaped by close_attach is no longer waitable by its parent.
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
    finally:
        # Emergency cleanup only if the assertion/path above regresses.
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass


def test_websocket_cleanup_does_not_block_event_loop():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "await asyncio.to_thread(terminals.close_attach, attach_pid, attach_fd)" in source
    assert "\n                terminals.close_attach(attach_pid, attach_fd)" not in source
