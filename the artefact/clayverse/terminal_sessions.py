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
from dataclasses import dataclass
from pathlib import Path

CANONICAL_TERMINALS = {
    "gabriel": "clayverse-gabriel",
    "andreas": "clayverse-andreas",
}


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
    """Own exactly two durable tmux perspectives into one ClayVerse entity.

    Browser PTYs attach/detach from tmux. Disconnecting a browser therefore cannot
    terminate the underlying interactive Claude Code CLI session. Claude starts from
    an empty allowlisted environment, no built-in tools, strict ClayVerse MCP and
    fixed lifecycle hooks that bind every prompt/response to UnifiedDB.
    """

    CANONICAL_USERS = tuple(CANONICAL_TERMINALS)
    MANAGED_SETTINGS = Path("/etc/claude-code/managed-settings.json")

    def __init__(self, state_root: str | Path, workspace: str | Path = "/workspace"):
        self.state_root = Path(state_root)
        self.workspace = Path(workspace)
        self.runtime_prompt = Path("/opt/clayverse/runtime/CLAUDE.md")
        self.tmux_socket = "clayverse"

    def _require_programs(self) -> None:
        for program in ("tmux", "claude", "python3"):
            if shutil.which(program) is None:
                raise TerminalRuntimeError(f"required program unavailable: {program}")
        if not self.runtime_prompt.is_file():
            raise TerminalRuntimeError("runtime Claude contract unavailable")
        if not self.MANAGED_SETTINGS.is_file():
            raise TerminalRuntimeError("managed Claude lifecycle settings unavailable")

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

    def _mcp_env(self, binding: TerminalBinding) -> dict[str, str]:
        enable_entityos = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        env = {
            "PYTHONPATH": "/opt/clayverse",
            "CLAYVERSE_STATE_ROOT": str(self.state_root),
            "CLAYVERSE_USER_ID": binding.user_id,
            "CLAYVERSE_SESSION_ID": binding.session_id,
            "CLAYVERSE_ENABLE_ENTITYOS_EXEC": "1" if enable_entityos else "0",
        }
        # Artifact identity is not capability authority. Do not disclose executable
        # path/digest into the generated MCP config while the separate execution gate
        # is closed. mcp_server independently rechecks the gate before constructing a
        # bridge, so stale/generated configuration cannot widen authority either.
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
                    "command": "python3",
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
        cp = subprocess.run(
            ["tmux", "-L", self.tmux_socket, "has-session", "-t", binding.tmux_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return cp.returncode == 0

    def ensure(self, user_id: str) -> TerminalBinding:
        self._require_programs()
        binding = self.binding(user_id)
        self._write_mcp_config(binding)
        self.workspace.mkdir(parents=True, exist_ok=True)
        if self._has_session(binding):
            return binding

        # Built-in Claude tools are absent. Explicit MCP remains available even with
        # --tools ""; strict MCP prevents user/project MCP injection. Filesystem setting
        # sources are disabled so project/user hooks cannot compete with the fixed hooks.
        claude_argv = [
            "claude",
            "--strict-mcp-config",
            "--mcp-config", str(binding.mcp_config),
            "--settings", str(self.MANAGED_SETTINGS),
            "--setting-sources", "",
            "--tools", "",
            "--allowedTools", "mcp__clayverse__*",
            "--permission-mode", "dontAsk",
            "--append-system-prompt-file", str(self.runtime_prompt),
        ]
        # Start Claude from an empty environment. Subscription/OAuth state lives in the
        # durable per-user HOME. Arbitrary container secrets (especially Clerk signing
        # material) never become an accidental alternate authentication/tool channel.
        # Claude's own transcript and auto-memory stores are disabled so UnifiedDB is
        # the sole durable conversation/memory authority after ClayVerse compression.
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
            "DISABLE_AUTOUPDATER=1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY=1",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS=1",
            *claude_argv,
        ]
        command = shlex.join(env_argv)
        cp = subprocess.run(
            [
                "tmux", "-L", self.tmux_socket,
                "new-session", "-d", "-s", binding.tmux_name,
                "-c", str(self.workspace), command,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if cp.returncode != 0:
            raise TerminalRuntimeError(f"failed to create {binding.tmux_name}: {cp.stderr[-1000:]}")
        return binding

    def attach_pty(self, user_id: str) -> tuple[int, int, TerminalBinding]:
        binding = self.ensure(user_id)
        pid, fd = pty.fork()
        if pid == 0:
            # The attach client cannot create a new command channel; it only connects to
            # the already-running, sanitized tmux session.
            env = {
                "HOME": str(binding.home),
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "LANG": "C.UTF-8",
            }
            os.execvpe(
                "tmux",
                ["tmux", "-L", self.tmux_socket, "attach-session", "-t", binding.tmux_name],
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
            pass
