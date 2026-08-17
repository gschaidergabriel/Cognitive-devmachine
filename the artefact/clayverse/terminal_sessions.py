from __future__ import annotations

import fcntl
import json
import os
import pty
import shutil
import signal
import struct
import subprocess
import termios
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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
    TERMINAL_PROVIDER_MARKER = "@clayverse_terminal_provider"
    TMUX_CONTROL_TIMEOUT_SECONDS = 2.0

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
        return TerminalBinding(
            user_id=user_id,
            session_id=f"session:{user_id}",
            tmux_name=CANONICAL_TERMINALS[user_id],
            home=self.state_root / "users" / user_id / "home",
            mcp_config=self.state_root / "users" / user_id / "home" / "clayverse-mcp.json",
        )

    @classmethod
    def _tmux_socket(cls, binding: TerminalBinding) -> str:
        return f"{cls.TMUX_SOCKET_PREFIX}-{binding.user_id}"

    @classmethod
    def _tmux_argv(cls, binding: TerminalBinding, *args: str) -> list[str]:
        return ["tmux", "-L", cls._tmux_socket(binding), "-f", str(cls.MANAGED_TMUX), *args]

    @staticmethod
    def _tmux_control_env() -> dict[str, str]:
        return {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "TERM": "xterm-256color",
            "LANG": "C.UTF-8",
        }

    def _run_tmux(self, binding: TerminalBinding, *args: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                self._tmux_argv(binding, *args),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
                env=self._tmux_control_env(),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TerminalRuntimeError("tmux control operation unavailable") from exc

    def _assert_tmux_server_policy(self, binding: TerminalBinding) -> None:
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
            cp = self._run_tmux(binding, *args)
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
        cp = self._run_tmux(binding, "has-session", "-t", binding.tmux_name)
        return cp.returncode == 0

    def _enforce_tmux_policy(self, binding: TerminalBinding) -> None:
        cp = self._run_tmux(binding, "source-file", str(self.MANAGED_TMUX))
        if cp.returncode != 0:
            raise TerminalRuntimeError(f"failed to enforce tmux policy for {binding.tmux_name}: {cp.stderr[-1000:]}")

    def _provider_marker(self, binding: TerminalBinding) -> str:
        cp = self._run_tmux(
            binding,
            "show-options", "-qv", "-t", binding.tmux_name, self.TERMINAL_PROVIDER_MARKER,
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError("tmux terminal-provider marker unavailable")
        return cp.stdout.strip()

    def _set_provider_marker(self, binding: TerminalBinding, provider: str) -> None:
        cp = self._run_tmux(
            binding,
            "set-option", "-t", binding.tmux_name, self.TERMINAL_PROVIDER_MARKER, provider,
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError("failed to bind tmux terminal-provider marker")

    def _new_claude_session(self, binding: TerminalBinding) -> None:
        claude_argv = [
            "claude", "--settings", str(self.MANAGED_SETTINGS), "--setting-sources", "",
            "--tools", "", "--allowedTools", "mcp__clayverse__session_state",
            "mcp__clayverse__request_effect", "--permission-mode", "dontAsk",
            "--append-system-prompt-file", str(self.runtime_prompt),
        ]
        mcp_env = self._mcp_env(binding)
        effect_env = [
            f"{key}={mcp_env[key]}"
            for key in ("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "CLAYVERSE_ENTITYOS_PATH", "CLAYVERSE_ENTITYOS_SHA256")
            if key in mcp_env
        ]
        env_argv = [
            "env", "-i", f"HOME={binding.home}", "PATH=/usr/local/bin:/usr/bin:/bin",
            "TERM=xterm-256color", "LANG=C.UTF-8", "PYTHONPATH=/opt/clayverse",
            f"CLAYVERSE_STATE_ROOT={self.state_root}", f"CLAYVERSE_USER_ID={binding.user_id}",
            f"CLAYVERSE_SESSION_ID={binding.session_id}", *effect_env, "DISABLE_UPDATES=1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1", "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1", "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1",
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1", f"CLAUDE_CODE_SHELL_PREFIX={self.DIRECT_SHELL_GUARD}",
            *claude_argv,
        ]
        cp = self._run_tmux(
            binding, "new-session", "-d", "-s", binding.tmux_name,
            "-c", str(self.workspace), *env_argv,
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError(f"failed to create {binding.tmux_name}: {cp.stderr[-1000:]}")
        self._set_provider_marker(binding, "claude")

    def ensure(self, user_id: str) -> TerminalBinding:
        self._require_programs()
        binding = self.binding(user_id)
        binding.home.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        if not self._has_session(binding):
            self._new_claude_session(binding)
        else:
            marker = self._provider_marker(binding)
            if marker and marker != "claude":
                raise TerminalRuntimeError("existing tmux session belongs to a different terminal provider")
        self._enforce_tmux_policy(binding)
        self._assert_tmux_server_policy(binding)
        return binding

    def _pane_pid(self, binding: TerminalBinding, target: str) -> int:
        cp = self._run_tmux(binding, "display-message", "-p", "-t", target, "#{pane_pid}")
        if cp.returncode != 0:
            raise TerminalRuntimeError("provider pane identity unavailable")
        try:
            pid = int(cp.stdout.strip())
        except ValueError as exc:
            raise TerminalRuntimeError("provider pane PID invalid") from exc
        if pid <= 1:
            raise TerminalRuntimeError("provider pane PID invalid")
        return pid

    def _assert_single_provider_pane(self, binding: TerminalBinding, expected_pid: int) -> None:
        cp = self._run_tmux(binding, "list-panes", "-s", "-t", binding.tmux_name, "-F", "#{pane_pid}")
        if cp.returncode != 0:
            raise TerminalRuntimeError("provider tmux topology unavailable")
        try:
            pids = [int(line) for line in cp.stdout.splitlines() if line.strip()]
        except ValueError as exc:
            raise TerminalRuntimeError("provider tmux topology invalid") from exc
        if pids != [expected_pid]:
            raise TerminalRuntimeError("API provider tmux session must contain exactly one admitted pane")

    def ensure_api_provider(
        self,
        user_id: str,
        broker_socket: str | Path,
        register_peer: Callable[..., None],
    ) -> tuple[TerminalBinding, str, int]:
        self._require_programs()
        binding = self.binding(user_id)
        binding.home.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        socket_path = Path(broker_socket)
        raw_socket = str(socket_path)
        if not socket_path.is_absolute() or any(ch in raw_socket for ch in ("\x00", "\n", "\r")):
            raise TerminalRuntimeError("provider broker socket path invalid")

        if not self._has_session(binding):
            provider_env = [
                "env", "-i", f"HOME={binding.home}", "PATH=/usr/local/bin:/usr/bin:/bin",
                "TERM=xterm-256color", "LANG=C.UTF-8", "PYTHONPATH=/opt/clayverse",
                f"CLAYVERSE_PROVIDER_BROKER_SOCKET={socket_path}",
                "python3", "-m", "clayverse.provider_terminal",
            ]
            cp = self._run_tmux(
                binding, "new-session", "-d", "-s", binding.tmux_name,
                "-c", str(self.workspace), *provider_env,
            )
            if cp.returncode != 0:
                raise TerminalRuntimeError(f"failed to create API provider terminal: {cp.stderr[-1000:]}")
            self._set_provider_marker(binding, "api")
        elif self._provider_marker(binding) != "api":
            raise TerminalRuntimeError("existing tmux session is not the admitted API provider perspective")

        self._enforce_tmux_policy(binding)
        self._assert_tmux_server_policy(binding)
        pane_pid = self._pane_pid(binding, binding.tmux_name)
        self._assert_single_provider_pane(binding, pane_pid)
        register_peer(user_id=binding.user_id, session_id=binding.session_id, pid=pane_pid)
        return binding, binding.tmux_name, pane_pid

    def _attach_binding(self, binding: TerminalBinding) -> tuple[int, int, TerminalBinding]:
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

    def attach_pty(self, user_id: str) -> tuple[int, int, TerminalBinding]:
        provider = os.environ.get("CLAYVERSE_TERMINAL_PROVIDER", "claude").strip().lower()
        if provider == "claude":
            return self._attach_binding(self.ensure(user_id))
        if provider == "api":
            from .provider_terminal_broker import active_provider_terminal_broker
            broker = active_provider_terminal_broker()
            binding, _target, _pane_pid = self.ensure_api_provider(
                user_id,
                broker.socket_path,
                broker.register_peer,
            )
            return self._attach_binding(binding)
        raise TerminalRuntimeError("CLAYVERSE_TERMINAL_PROVIDER must be claude or api")

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