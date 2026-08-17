from __future__ import annotations

import json
import os
import pty
import shlex
import shutil
import signal
import struct
import subprocess
import termios
import fcntl
import time
from dataclasses import dataclass
from pathlib import Path

from .identity import CANONICAL_TERMINAL_NAMES

CANONICAL_TERMINALS = CANONICAL_TERMINAL_NAMES


class TerminalRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class TerminalBinding:
    user_id: str
    session_id: str
    tmux_name: str
    home: Path
    mcp_config: Path


class TerminalSessionManager:
    """Own exactly two durable, tmux-isolated perspectives into one ClayVerse entity."""

    CANONICAL_USERS = tuple(CANONICAL_TERMINALS)
    MANAGED_SETTINGS = Path("/etc/claude-code/managed-settings.json")
    MANAGED_MCP = Path("/etc/claude-code/managed-mcp.json")
    MANAGED_TMUX = Path("/etc/clayverse/managed-tmux.conf")
    MANAGED_TMUX_POLICY_ID = "clayverse-browser-transport-v3"
    DIRECT_SHELL_GUARD = Path("/opt/clayverse/runtime/deny-shell")
    TMUX_SOCKET_PREFIX = "clayverse"
    TMUX_CONTROL_TIMEOUT_SECONDS = 2.0
    _IDEMPOTENT_MISSING_KEY_TABLES = frozenset({"prefix", "root", "copy-mode", "copy-mode-vi"})

    def __init__(self, state_root: str | Path, workspace: str | Path = "/workspace"):
        self.state_root = Path(state_root)
        self.workspace = Path(workspace)
        self.runtime_prompt = Path("/opt/clayverse/runtime/CLAUDE.md")

    def _require_programs(self) -> None:
        for program in ("tmux", "claude", "python3"):
            if shutil.which(program) is None:
                raise TerminalRuntimeError(f"required program unavailable: {program}")
        if not self.runtime_prompt.is_file():
            raise TerminalRuntimeError("runtime Claude contract unavailable")
        if not self.MANAGED_SETTINGS.is_file():
            raise TerminalRuntimeError("managed Claude lifecycle settings unavailable")
        if not self.MANAGED_MCP.is_file():
            raise TerminalRuntimeError("exclusive managed ClayVerse MCP unavailable")
        if not self.MANAGED_TMUX.is_file() or self.MANAGED_TMUX.stat().st_mode & 0o222:
            raise TerminalRuntimeError("managed tmux command-surface policy unavailable or writable")
        if not self.DIRECT_SHELL_GUARD.is_file() or not os.access(self.DIRECT_SHELL_GUARD, os.X_OK):
            raise TerminalRuntimeError("direct-shell guard unavailable")

    def binding(self, user_id: str) -> TerminalBinding:
        if user_id not in CANONICAL_TERMINALS:
            raise PermissionError("unknown terminal identity")
        session_id = f"session:{user_id}"
        home = self.state_root / "users" / user_id / "home"
        return TerminalBinding(
            user_id=user_id,
            session_id=session_id,
            tmux_name=CANONICAL_TERMINALS[user_id],
            home=home,
            mcp_config=home / "clayverse-mcp.json",
        )

    @classmethod
    def _tmux_socket(cls, binding: TerminalBinding) -> str:
        return f"{cls.TMUX_SOCKET_PREFIX}-{binding.user_id}"

    @classmethod
    def _tmux_argv(cls, binding: TerminalBinding, *args: str) -> list[str]:
        return [
            "tmux",
            "-L", cls._tmux_socket(binding),
            "-f", str(cls.MANAGED_TMUX),
            *args,
        ]

    def _assert_tmux_server_policy(self, binding: TerminalBinding) -> None:
        """Fail closed unless the connected tmux server is transport-only."""
        checks = (
            ("managed-policy marker", ("show-options", "-sqv", "@clayverse_managed_policy"), self.MANAGED_TMUX_POLICY_ID),
            ("prefix", ("show-options", "-gqv", "prefix"), "None"),
            ("prefix2", ("show-options", "-gqv", "prefix2"), "None"),
            ("status", ("show-options", "-gqv", "status"), "off"),
            ("mouse", ("show-options", "-gqv", "mouse"), "off"),
            ("default-shell", ("show-options", "-gqv", "default-shell"), str(self.DIRECT_SHELL_GUARD)),
            ("keymap", ("list-keys",), ""),
        )
        for label, args, expected in checks:
            try:
                cp = subprocess.run(
                    self._tmux_argv(binding, *args),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise TerminalRuntimeError(f"tmux server policy attestation unavailable: {label}") from exc
            if cp.returncode != 0 or cp.stdout.strip() != expected:
                raise TerminalRuntimeError(f"tmux server policy attestation failed: {label}")

    def _mcp_env(self, binding: TerminalBinding) -> dict[str, str]:
        enable_entityos = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        env = {
            "PYTHONPATH": "/opt/clayverse",
            "CLAYVERSE_STATE_ROOT": str(self.state_root),
            "CLAYVERSE_USER_ID": binding.user_id,
            "CLAYVERSE_SESSION_ID": binding.session_id,
            "CLAYVERSE_ENABLE_ENTITYOS_EXEC": "1" if enable_entityos else "0",
        }
        if enable_entityos:
            for key in ("CLAYVERSE_ENTITYOS_PATH", "CLAYVERSE_ENTITYOS_SHA256"):
                value = os.environ.get(key, "").strip()
                if value:
                    env[key] = value
        return env

    def _write_mcp_config(self, binding: TerminalBinding) -> None:
        """Diagnostic-only mirror; never a product MCP authority."""
        binding.home.mkdir(parents=True, exist_ok=True)
        payload = {
            "mcpServers": {
                "clayverse": {
                    "type": "stdio",
                    "command": "/usr/local/bin/python",
                    "args": ["-m", "clayverse.mcp_server"],
                    "env": self._mcp_env(binding),
                }
            }
        }
        tmp = binding.mcp_config.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, binding.mcp_config)

    def _has_session(self, binding: TerminalBinding) -> bool:
        try:
            cp = subprocess.run(
                self._tmux_argv(binding, "has-session", "-t", binding.tmux_name),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TerminalRuntimeError(
                f"tmux session liveness probe unavailable for {binding.tmux_name}"
            ) from exc
        return cp.returncode == 0

    @classmethod
    def _tmux_policy_reapply_errors_are_idempotent(cls, stderr: str) -> bool:
        """Accept only tmux's exact diagnostics for already-removed default key tables."""
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        if not lines:
            return False
        expected = {
            f"table {table} doesn't exist"
            for table in cls._IDEMPOTENT_MISSING_KEY_TABLES
        }
        return all(line in expected for line in lines)

    def _enforce_tmux_policy(self, binding: TerminalBinding) -> None:
        """Reapply the immutable command-surface fence to a running tmux server."""
        try:
            cp = subprocess.run(
                self._tmux_argv(binding, "source-file", str(self.MANAGED_TMUX)),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TerminalRuntimeError(
                f"tmux policy enforcement unavailable for {binding.tmux_name}"
            ) from exc
        if cp.returncode != 0 and not self._tmux_policy_reapply_errors_are_idempotent(cp.stderr):
            raise TerminalRuntimeError(
                f"failed to enforce tmux policy for {binding.tmux_name}: {cp.stderr[-1000:]}"
            )

    def _launch_argv(self, binding: TerminalBinding) -> list[str]:
        claude_argv = [
            "claude",
            "--settings", str(self.MANAGED_SETTINGS),
            "--setting-sources", "",
            "--tools", "",
            "--allowedTools",
            "mcp__clayverse__session_state",
            "mcp__clayverse__request_effect",
            "--permission-mode", "dontAsk",
            "--append-system-prompt-file", str(self.runtime_prompt),
        ]
        mcp_env = self._mcp_env(binding)
        effect_env = [
            f"{key}={mcp_env[key]}"
            for key in ("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "CLAYVERSE_ENTITYOS_PATH", "CLAYVERSE_ENTITYOS_SHA256")
            if key in mcp_env
        ]
        return [
            "env",
            "-i",
            f"HOME={binding.home}",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "TERM=xterm-256color",
            "LANG=C.UTF-8",
            "PYTHONPATH=/opt/clayverse",
            f"CLAYVERSE_STATE_ROOT={self.state_root}",
            f"CLAYVERSE_USER_ID={binding.user_id}",
            f"CLAYVERSE_SESSION_ID={binding.session_id}",
            *effect_env,
            "DISABLE_UPDATES=1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1",
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1",
            f"CLAUDE_CODE_SHELL_PREFIX={self.DIRECT_SHELL_GUARD}",
            *claude_argv,
        ]

    def _attest_existing_session(self, binding: TerminalBinding) -> bool:
        """Require exactly one live pane with the exact managed Claude launch contract."""
        try:
            cp = subprocess.run(
                self._tmux_argv(
                    binding,
                    "list-panes", "-s", "-t", binding.tmux_name,
                    "-F", "#{pane_dead}\t#{pane_current_command}\t#{pane_start_command}",
                ),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if cp.returncode != 0:
            return False
        lines = [line for line in cp.stdout.splitlines() if line]
        if len(lines) != 1:
            return False
        fields = lines[0].split("\t", 2)
        if len(fields) != 3:
            return False
        pane_dead, current_command, start_command = fields
        if pane_dead != "0" or current_command != "claude":
            return False
        try:
            start_argv = shlex.split(start_command)
        except ValueError:
            return False
        return start_argv == self._launch_argv(binding)

    def is_managed_session(self, binding: TerminalBinding) -> bool:
        """Read-only liveness + transport-policy + process-contract predicate."""
        try:
            if not self._has_session(binding):
                return False
            self._assert_tmux_server_policy(binding)
            return self._attest_existing_session(binding)
        except (OSError, subprocess.TimeoutExpired, TerminalRuntimeError):
            return False

    def ensure(self, user_id: str) -> TerminalBinding:
        self._require_programs()
        binding = self.binding(user_id)
        binding.home.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        if self._has_session(binding):
            self._enforce_tmux_policy(binding)
            self._assert_tmux_server_policy(binding)
            if not self._attest_existing_session(binding):
                raise TerminalRuntimeError(f"existing {binding.tmux_name} is not the managed Claude session")
            return binding

        launch_argv = self._launch_argv(binding)
        try:
            cp = subprocess.run(
                self._tmux_argv(
                    binding,
                    "new-session", "-d", "-s", binding.tmux_name,
                    "-c", str(self.workspace), *launch_argv,
                ),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TerminalRuntimeError(
                f"tmux session creation unavailable for {binding.tmux_name}"
            ) from exc
        if cp.returncode != 0:
            raise TerminalRuntimeError(f"failed to create {binding.tmux_name}: {cp.stderr[-1000:]}")
        self._enforce_tmux_policy(binding)
        self._assert_tmux_server_policy(binding)
        if not self._attest_existing_session(binding):
            raise TerminalRuntimeError(f"created {binding.tmux_name} failed managed Claude attestation")
        return binding

    def attach_pty(self, user_id: str) -> tuple[int, int, TerminalBinding]:
        binding = self.ensure(user_id)
        pid, fd = pty.fork()
        if pid == 0:
            env = {
                "HOME": str(binding.home),
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "LANG": "C.UTF-8",
            }
            os.execvpe(
                "tmux",
                self._tmux_argv(binding, "attach-session", "-t", binding.tmux_name),
                env,
            )
        return pid, fd, binding

    @staticmethod
    def resize(fd: int, rows: int, cols: int) -> None:
        rows = max(2, min(int(rows), 500))
        cols = max(10, min(int(cols), 1000))
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    @staticmethod
    def close_attach(pid: int, fd: int) -> None:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.kill(pid, signal.SIGHUP)
        except ProcessLookupError:
            return

        deadline = time.monotonic() + 0.5
        while True:
            try:
                waited, _ = os.waitpid(pid, os.WNOHANG)
            except ChildProcessError:
                return
            if waited == pid:
                return
            if time.monotonic() >= deadline:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass
                return
            time.sleep(0.01)
