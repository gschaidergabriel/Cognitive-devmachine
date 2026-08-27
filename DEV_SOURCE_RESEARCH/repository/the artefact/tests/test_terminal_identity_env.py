from __future__ import annotations

import sys
import time

from clayverse.terminal import PermanentTerminal


def _read_until_exit(terminal: PermanentTerminal, timeout: float = 2.0) -> bytes:
    deadline = time.monotonic() + timeout
    out = bytearray()
    while time.monotonic() < deadline:
        out.extend(terminal.read())
        if not terminal.alive() and terminal.master_fd is None:
            break
        time.sleep(0.01)
    return bytes(out)


def test_child_process_receives_canonical_clayverse_perspective_environment():
    for user in ("gabriel", "andreas"):
        terminal = PermanentTerminal(
            user,
            [
                sys.executable,
                "-u",
                "-c",
                "import os; print(os.environ['CLAYVERSE_USER_ID']+'|'+os.environ['CLAYVERSE_SESSION_ID'], flush=True)",
            ],
        )
        terminal.start()
        output = _read_until_exit(terminal)
        terminal.stop()
        assert f"{user}|terminal-{user}".encode() in output
