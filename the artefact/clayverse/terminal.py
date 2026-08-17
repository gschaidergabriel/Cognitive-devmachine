from __future__ import annotations

import errno
import os
import pty
import shlex
import signal
import time
from dataclasses import dataclass


class TerminalError(RuntimeError):
    pass


@dataclass
class PermanentTerminal:
    user_id: str
    argv: list[str]
    pid: int | None = None
    master_fd: int | None = None
    exit_status: int | None = None

    def start(self) -> None:
        if self.alive():
            return
        if self.master_fd is not None:
            raise TerminalError("terminal output must be drained before restart")
        if not self.argv or not self.argv[0]:
            raise TerminalError("terminal argv is empty")
        pid, fd = pty.fork()
        if pid == 0:
            os.execvp(self.argv[0], self.argv)
        os.set_blocking(fd, False)
        self.pid = pid
        self.master_fd = fd
        self.exit_status = None

    def alive(self) -> bool:
        if self.pid is None:
            return False
        try:
            waited, status = os.waitpid(self.pid, os.WNOHANG)
        except ChildProcessError:
            self.pid = None
            return False
        if waited == 0:
            return True
        self.pid = None
        self.exit_status = status
        # Do not close master_fd here. A PTY may still contain final buffered
        # output after the child has exited; read() owns draining that buffer.
        return False

    def write(self, data: bytes | str, *, max_bytes: int = 65_536) -> int:
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not isinstance(data, bytes):
            raise TypeError("terminal input must be bytes or str")
        if not data or len(data) > max_bytes:
            raise ValueError("terminal input size out of bounds")
        if not self.alive() or self.master_fd is None:
            raise TerminalError("terminal is not running")
        return os.write(self.master_fd, data)

    def read(self, *, max_bytes: int = 65_536) -> bytes:
        if max_bytes <= 0 or max_bytes > 1_048_576:
            raise ValueError("terminal read size out of bounds")
        fd = self.master_fd
        if fd is None:
            return b""
        try:
            data = os.read(fd, max_bytes)
        except BlockingIOError:
            self.alive()
            return b""
        except OSError as exc:
            # Linux PTY masters commonly report EIO after the slave exits and
            # all buffered bytes have already been consumed.
            if exc.errno == errno.EIO:
                self.alive()
                self._close_master()
                return b""
            raise
        if not data:
            self.alive()
            self._close_master()
        return data

    def stop(self, *, grace_seconds: float = 1.0) -> None:
        pid = self.pid
        if pid is None:
            self._close_master()
            return
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            self.alive()
            self._close_master()
            return

        deadline = time.monotonic() + max(0.0, grace_seconds)
        while time.monotonic() < deadline:
            try:
                waited, status = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                waited, status = pid, self.exit_status or 0
            if waited:
                self.pid = None
                self.exit_status = status
                self._close_master()
                return
            time.sleep(0.01)

        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            _, status = os.waitpid(pid, 0)
            self.exit_status = status
        except ChildProcessError:
            pass
        self.pid = None
        self._close_master()

    def _close_master(self) -> None:
        fd = self.master_fd
        self.master_fd = None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


class TerminalSupervisor:
    """Two authenticated user perspectives; never two ClayVerse entities."""

    USERS = ("gabriel", "andreas")

    def __init__(self, command: str = "claude"):
        argv = shlex.split(command)
        if not argv:
            raise TerminalError("terminal command is empty")
        self.terminals = {user: PermanentTerminal(user, list(argv)) for user in self.USERS}

    def for_user(self, user_id: str) -> PermanentTerminal:
        try:
            return self.terminals[user_id]
        except KeyError as exc:
            raise PermissionError("unknown terminal user") from exc

    def start_all(self) -> None:
        started: list[PermanentTerminal] = []
        try:
            for terminal in self.terminals.values():
                terminal.start()
                started.append(terminal)
        except Exception:
            for terminal in reversed(started):
                terminal.stop()
            raise

    def stop_all(self) -> None:
        for terminal in self.terminals.values():
            terminal.stop()
