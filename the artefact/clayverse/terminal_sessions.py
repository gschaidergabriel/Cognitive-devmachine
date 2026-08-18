from __future__ import annotations

import json
import os
import pty
import shutil
import signal
import struct
import subprocess
import termios
import fcntl
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .identity import CANONICAL_TERMINAL_NAMES
from .terminal_activity import TerminalActivityRegistry

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
    # Both canonical users share ONE Claude Code OAuth login (owner decision:
    # "we are already logged in on the server"). Only this one file is shared --
    # never the surrounding .claude directory -- so sessions/history/project state
    # stay per-user and the two perspectives are not braided together.
    CREDENTIALS_SOURCE = Path("/var/lib/clay/.claude/.credentials.json")
    TMUX_SOCKET_PREFIX = "clayverse"
    TMUX_CONTROL_TIMEOUT_SECONDS = 2.0
    AUTONOMY_PROMPT_MAX_CHARS = 256

    def __init__(
        self,
        state_root: str | Path,
        workspace: str | Path = "/workspace",
        *,
        activity: TerminalActivityRegistry | None = None,
    ):
        self.state_root = Path(state_root)
        self.workspace = Path(workspace)
        # Rendered from UnifiedDB root state at boot (see service.py
            # render_runtime_prompt). The image file is only the static contract
            # half; the identity half comes from canonical state.
        self.runtime_prompt = Path(self.state_root) / "runtime" / "CLAUDE.md"
        self.activity = activity or TerminalActivityRegistry()
        self._attach_lock = threading.RLock()
        self._attach_users: dict[int, str] = {}

    def _require_programs(self) -> None:
        for program in ("tmux", "claude", "python3"):
            if shutil.which(program) is None:
                raise TerminalRuntimeError(f"required program unavailable: {program}")
        if not self.runtime_prompt.is_file():
            # Deliberately no fallback to the image file: a terminal that starts
            # without the canonical identity would be a different entity wearing
            # the same name.
            raise TerminalRuntimeError("rendered runtime contract unavailable -- canonical identity not materialised")
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
        # A tmux client can address sessions inside its connected server. Keep the
        # two authenticated ClayVerse perspectives on disjoint tmux servers so an
        # attached client cannot switch from one canonical user's session to the other.
        return f"{cls.TMUX_SOCKET_PREFIX}-{binding.user_id}"

    @classmethod
    def _tmux_argv(cls, binding: TerminalBinding, *args: str) -> list[str]:
        # The browser is attached to tmux, so tmux itself is part of the effect boundary.
        # Always select the root-owned policy that removes tmux's command keymaps;
        # never allow an invocation to fall back to user/default tmux configuration.
        return [
            "tmux",
            "-L", cls._tmux_socket(binding),
            "-f", str(cls.MANAGED_TMUX),
            *args,
        ]

    def _run_tmux(self, binding: TerminalBinding, *args: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                self._tmux_argv(binding, *args),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.TMUX_CONTROL_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TerminalRuntimeError("tmux control operation unavailable") from exc

    def _assert_tmux_server_policy(self, binding: TerminalBinding) -> None:
        """Fail closed unless the connected tmux server is transport-only.

        tmux only reads `-f` when a server starts. An already-running server can therefore
        ignore the `-f` supplied by a later client. The managed policy writes a versioned
        marker last after removing all default key tables. Verify the marker, both prefix
        options, inert status/mouse/default-shell settings, and the effective global key
        binding list before admitting attachment.
        """
        checks = (
            (
                "managed-policy marker",
                ("show-options", "-sqv", "@clayverse_managed_policy"),
                self.MANAGED_TMUX_POLICY_ID,
            ),
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
        """Diagnostic-only mirror; never a product MCP authority.

        `managed-mcp.json` is the sole runtime server-definition source. This helper is
        retained for bounded tests/inspection and is deliberately not called by ensure().
        """
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

    def _enforce_tmux_policy(self, binding: TerminalBinding) -> None:
        """Reapply the immutable command-surface fence to a running tmux server.

        tmux configuration is loaded when a server starts, not whenever a new session
        or client is created. A persistent per-user server may therefore predate a
        ClayVerse policy upgrade. Source the root-owned policy before every admitted
        attach path.

        `unbind-key -a -T <table>` is not idempotent: once a table has zero bindings,
        tmux (observed on both 3.4 and 3.5a) drops the table object and a later
        `unbind-key -a -T <table>` on the same running server returns nonzero and
        prints "table <name> doesn't exist" even though the table remains correctly
        empty. This is expected on the very first `ensure()` for a session, because
        `new-session -f <policy>` already applied the policy once immediately before
        this reapply runs. A `source-file` returncode alone is therefore not trusted
        here; `-q` quiets the resulting per-line warnings and the unconditional
        `_assert_tmux_server_policy` call that follows this method in every `ensure()`
        caller is the actual, state-based fail-closed gate (marker, prefix, prefix2,
        status, mouse, default-shell, and an empty effective keymap all checked
        directly against the live server).
        """
        self._run_tmux(binding, "source-file", "-q", str(self.MANAGED_TMUX))

    def _link_shared_credentials(self, binding: TerminalBinding) -> None:
        """Symlink ONLY the OAuth credential file into this user's Claude home.

        A missing source is not fatal -- it just leaves this user's Claude Code CLI
        unauthenticated, exactly as before this method existed. Never raises, never
        writes to CREDENTIALS_SOURCE itself (read-only relationship to that mount).
        """
        source = self.CREDENTIALS_SOURCE
        if not source.is_file():
            return
        target_dir = binding.home / ".claude"
        target = target_dir / ".credentials.json"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                if os.readlink(target) == str(source):
                    return
                target.unlink()
            elif target.exists():
                return  # a real (non-symlink) file here is deliberate -- do not clobber it
            target.symlink_to(source)
        except OSError:
            return

    def ensure(self, user_id: str) -> TerminalBinding:
        self._require_programs()
        binding = self.binding(user_id)
        binding.home.mkdir(parents=True, exist_ok=True)
        self._link_shared_credentials(binding)
        self.workspace.mkdir(parents=True, exist_ok=True)
        if self._has_session(binding):
            self._enforce_tmux_policy(binding)
            self._assert_tmux_server_policy(binding)
            return binding

        # /etc/claude-code/managed-mcp.json is an exclusive server set. There is no
        # user/project MCP file in the launch path. User/session identity reaches the
        # managed stdio server only through this sanitized process environment.
        claude_argv = [
            "claude",
            "--settings", str(self.MANAGED_SETTINGS),
            "--setting-sources", "",
            "--tools", "",
            "--allowedTools",
            "mcp__clayverse__session_state",
            "mcp__clayverse__request_effect",
            "mcp__clayverse__request_autonomy_effect",
            "--permission-mode", "dontAsk",
            "--append-system-prompt-file", str(self.runtime_prompt),
        ]
        mcp_env = self._mcp_env(binding)
        effect_env = [
            f"{key}={mcp_env[key]}"
            for key in ("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "CLAYVERSE_ENTITYOS_PATH", "CLAYVERSE_ENTITYOS_SHA256")
            if key in mcp_env
        ]
        env_argv = [
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
        try:
            cp = subprocess.run(
                self._tmux_argv(
                    binding,
                    "new-session", "-d", "-s", binding.tmux_name,
                    "-c", str(self.workspace), *env_argv,
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
        return binding

    def assert_detached_idle_claude(self, user_id: str) -> tuple[TerminalBinding, str]:
        """Attest the only state in which synthetic autonomous terminal input is allowed."""
        binding = self.ensure(user_id)
        activity = self.activity.snapshot(user_id)
        if activity.human_clients != 0 or not activity.autonomy_reserved:
            raise TerminalRuntimeError("autonomy terminal input lacks exclusive activity reservation")

        clients = self._run_tmux(
            binding,
            "list-clients", "-t", binding.tmux_name, "-F", "#{client_name}",
        )
        if clients.returncode != 0:
            raise TerminalRuntimeError("tmux client attestation unavailable")
        if clients.stdout.strip():
            raise TerminalRuntimeError("tmux session has an attached client")

        panes = self._run_tmux(
            binding,
            "list-panes", "-t", binding.tmux_name,
            "-F", "#{pane_id}\t#{pane_dead}\t#{pane_in_mode}\t#{pane_current_command}",
        )
        if panes.returncode != 0:
            raise TerminalRuntimeError("tmux pane attestation unavailable")
        lines = [line for line in panes.stdout.splitlines() if line]
        if len(lines) != 1:
            raise TerminalRuntimeError("autonomy dispatch requires exactly one tmux pane")
        fields = lines[0].split("\t")
        if len(fields) != 4:
            raise TerminalRuntimeError("tmux pane attestation malformed")
        pane_id, dead, in_mode, current_command = fields
        if not pane_id.startswith("%") or dead != "0" or in_mode != "0" or current_command != "claude":
            raise TerminalRuntimeError("tmux pane is not a detached idle managed Claude surface")
        return binding, pane_id

    def dispatch_autonomy_prompt(self, user_id: str, prompt: str) -> None:
        """Inject only a bounded one-shot dispatch token into an exclusively reserved idle pane."""
        if (
            not isinstance(prompt, str)
            or not prompt
            or len(prompt) > self.AUTONOMY_PROMPT_MAX_CHARS
            or any(ord(char) < 0x20 or ord(char) > 0x7E for char in prompt)
        ):
            raise ValueError("invalid autonomy terminal prompt")
        binding, pane_id = self.assert_detached_idle_claude(user_id)
        cp = self._run_tmux(
            binding,
            "send-keys", "-t", pane_id, "-l", prompt,
            ";", "send-keys", "-t", pane_id, "Enter",
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError("tmux autonomy dispatch failed")

    def attach_pty(self, user_id: str) -> tuple[int, int, TerminalBinding]:
        if not self.activity.begin_human(user_id):
            raise TerminalRuntimeError("terminal temporarily reserved for autonomy dispatch")
        registered = False
        try:
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
            with self._attach_lock:
                if pid in self._attach_users:
                    raise TerminalRuntimeError("duplicate PTY attach pid")
                self._attach_users[pid] = user_id
                registered = True
            return pid, fd, binding
        except BaseException:
            if not registered:
                self.activity.end_human(user_id)
            raise

    def resize(self, fd: int, rows: int, cols: int) -> None:
        rows = max(2, min(int(rows), 500))
        cols = max(10, min(int(cols), 1000))
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def close_attach(self, pid: int, fd: int) -> None:
        with self._attach_lock:
            user_id = self._attach_users.pop(pid, None)
        try:
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
        finally:
            if user_id is not None:
                self.activity.end_human(user_id)
