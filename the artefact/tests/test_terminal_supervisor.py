from __future__ import annotations

import sys
import time

import pytest

from clayverse.terminal import PermanentTerminal, TerminalSupervisor


def _read_until(terminal: PermanentTerminal, needle: bytes, timeout: float = 2.0) -> bytes:
    deadline = time.monotonic() + timeout
    out = bytearray()
    while time.monotonic() < deadline:
        out.extend(terminal.read())
        if needle in out:
            return bytes(out)
        time.sleep(0.01)
    return bytes(out)


def test_permanent_terminal_round_trip_and_reap():
    terminal = PermanentTerminal(
        "gabriel",
        [
            sys.executable,
            "-u",
            "-c",
            "import os; data=os.read(0,4096); os.write(1,b'ACK:'+data)",
        ],
    )
    try:
        terminal.start()
        assert terminal.alive()
        assert terminal.write(b"hello\n") > 0
        output = _read_until(terminal, b"ACK:hello")
        assert b"ACK:hello" in output
    finally:
        terminal.stop()
    assert not terminal.alive()
    assert terminal.pid is None
    assert terminal.master_fd is None


def test_terminal_io_is_bounded_and_stopped_terminal_fails_closed():
    terminal = PermanentTerminal("andreas", [sys.executable, "-c", "import time; time.sleep(10)"])
    with pytest.raises(ValueError):
        terminal.write(b"")
    with pytest.raises(ValueError):
        terminal.write(b"x" * 65_537)
    with pytest.raises(ValueError):
        terminal.read(max_bytes=0)
    with pytest.raises(RuntimeError, match="not running"):
        terminal.write("hello")
    assert terminal.read() == b""


def test_terminal_supervisor_binds_only_the_two_owner_perspectives():
    supervisor = TerminalSupervisor(command=f"{sys.executable} -c 'import time; time.sleep(10)'")
    assert supervisor.for_user("gabriel").user_id == "gabriel"
    assert supervisor.for_user("andreas").user_id == "andreas"
    with pytest.raises(PermissionError, match="unknown terminal user"):
        supervisor.for_user("mallory")


def test_unexpected_child_exit_is_reaped_without_stale_terminal_identity():
    terminal = PermanentTerminal("gabriel", [sys.executable, "-c", "raise SystemExit(7)"])
    terminal.start()
    deadline = time.monotonic() + 2.0
    while terminal.alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert not terminal.alive()
    assert terminal.pid is None
    assert terminal.master_fd is None
