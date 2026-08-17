from __future__ import annotations

import json
import os
import socket
import stat
import struct
import threading
from pathlib import Path

from .engine import ClayVerseEngine


class ProviderTerminalBrokerError(RuntimeError):
    pass


_ACTIVE_BROKER: "ProviderTerminalBroker | None" = None
_ACTIVE_BROKER_LOCK = threading.RLock()


def install_active_provider_terminal_broker(broker: "ProviderTerminalBroker") -> None:
    global _ACTIVE_BROKER
    if not isinstance(broker, ProviderTerminalBroker):
        raise TypeError("active provider terminal broker type invalid")
    with _ACTIVE_BROKER_LOCK:
        if _ACTIVE_BROKER is not None and _ACTIVE_BROKER is not broker:
            raise ProviderTerminalBrokerError("a different provider terminal broker is already active")
        _ACTIVE_BROKER = broker


def active_provider_terminal_broker() -> "ProviderTerminalBroker":
    with _ACTIVE_BROKER_LOCK:
        broker = _ACTIVE_BROKER
    if broker is None:
        raise ProviderTerminalBrokerError("provider terminal broker is not active")
    return broker


def clear_active_provider_terminal_broker(broker: "ProviderTerminalBroker") -> None:
    global _ACTIVE_BROKER
    with _ACTIVE_BROKER_LOCK:
        if _ACTIVE_BROKER is broker:
            _ACTIVE_BROKER = None


class ProviderTerminalBroker:
    """Secret-holding Stage-2 bridge from one trusted tmux pane into ClayVerseEngine.

    The provider credential remains in the service process. The tmux-side client gets
    only a Unix-domain socket path. Every connection is authenticated with Linux
    SO_PEERCRED against the exact pane PID registered by the root-owned terminal
    manager; sharing the container UID alone is not sufficient.
    """

    MAX_REQUEST_BYTES = 128 * 1024
    MAX_RESPONSE_BYTES = 512 * 1024
    _PEERCRED_SIZE = struct.calcsize("3i")

    def __init__(
        self,
        socket_path: str | Path,
        *,
        engine: ClayVerseEngine,
        clerk_map: dict[str, str],
    ):
        self.socket_path = Path(socket_path)
        if not self.socket_path.is_absolute():
            raise ValueError("provider broker socket path must be absolute")
        inverse = {user_id: subject for subject, user_id in clerk_map.items()}
        if set(inverse) != {"gabriel", "andreas"} or len(inverse) != len(clerk_map):
            raise ValueError("provider broker requires one Clerk subject per canonical user")
        self.engine = engine
        self._subject_for_user = inverse
        self._allowed_peers: dict[int, tuple[str, str]] = {}
        self._peer_lock = threading.RLock()
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()

    def register_peer(self, *, user_id: str, session_id: str, pid: int) -> None:
        if user_id not in self._subject_for_user or session_id != f"session:{user_id}":
            raise PermissionError("provider terminal peer identity mismatch")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1:
            raise ValueError("provider terminal peer PID is invalid")
        with self._peer_lock:
            for existing_pid, identity in list(self._allowed_peers.items()):
                if identity[0] == user_id:
                    del self._allowed_peers[existing_pid]
            self._allowed_peers[pid] = (user_id, session_id)

    def unregister_peer(self, pid: int) -> None:
        with self._peer_lock:
            self._allowed_peers.pop(int(pid), None)

    def _peer_identity(self, conn: socket.socket) -> tuple[str, str]:
        if not hasattr(socket, "SO_PEERCRED"):
            raise ProviderTerminalBrokerError("SO_PEERCRED unavailable")
        raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, self._PEERCRED_SIZE)
        pid, uid, _gid = struct.unpack("3i", raw)
        if uid != os.geteuid():
            raise PermissionError("provider terminal peer UID mismatch")
        with self._peer_lock:
            identity = self._allowed_peers.get(pid)
        if identity is None:
            raise PermissionError("provider terminal peer PID is not admitted")
        return identity

    @staticmethod
    def _read_frame(conn: socket.socket, max_bytes: int) -> bytes:
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = conn.recv(min(65536, max_bytes + 1 - size))
            if not chunk:
                raise ProviderTerminalBrokerError("provider terminal request ended before frame")
            chunks.append(chunk)
            size += len(chunk)
            if size > max_bytes:
                raise ProviderTerminalBrokerError("provider terminal request exceeds bound")
            if b"\n" in chunk:
                data = b"".join(chunks)
                frame, trailing = data.split(b"\n", 1)
                if trailing:
                    raise ProviderTerminalBrokerError("provider terminal accepts one request per connection")
                return frame

    @staticmethod
    def _request(frame: bytes) -> tuple[str, list[str]]:
        try:
            payload = json.loads(frame.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderTerminalBrokerError("provider terminal request is invalid JSON") from exc
        if not isinstance(payload, dict) or set(payload) != {"prompt", "resources"}:
            raise ProviderTerminalBrokerError("provider terminal request shape invalid")
        prompt = payload["prompt"]
        resources = payload["resources"]
        if (
            not isinstance(prompt, str)
            or not prompt
            or len(prompt) > 100_000
            or "\x00" in prompt
            or not isinstance(resources, list)
            or len(resources) > 50
            or any(not isinstance(item, str) or not item or len(item) > 2048 for item in resources)
        ):
            raise ProviderTerminalBrokerError("provider terminal request fields invalid")
        return prompt, resources

    @staticmethod
    def _terminal_result(result: dict) -> dict:
        decision = result.get("decision") if isinstance(result, dict) else None
        if not isinstance(decision, dict):
            raise ProviderTerminalBrokerError("ClayVerse engine result missing decision")
        return {
            "ok": True,
            "user_id": result.get("user_id"),
            "session_id": result.get("session_id"),
            "turn_id": result.get("turn_id"),
            "assistant_turn_id": result.get("assistant_turn_id"),
            "causal_id": result.get("causal_id"),
            "effect_id": result.get("effect_id"),
            "text": str(decision.get("text", "")),
            "outcome": result.get("outcome"),
        }

    @staticmethod
    def _assert_no_provider_secret(encoded: bytes) -> None:
        for name in ("MISTRAL_API_KEY", "CLAYVERSE_LLM_API_TOKEN"):
            value = os.environ.get(name, "")
            if value and value.encode("utf-8") in encoded:
                raise ProviderTerminalBrokerError("provider credential reached terminal response")

    def _handle(self, conn: socket.socket) -> None:
        user_id, session_id = self._peer_identity(conn)
        frame = self._read_frame(conn, self.MAX_REQUEST_BYTES)
        prompt, resources = self._request(frame)
        result = self.engine.ingest(self._subject_for_user[user_id], prompt, resources=resources)
        if result.get("session_id") != session_id or result.get("user_id") != user_id:
            raise ProviderTerminalBrokerError("ClayVerse engine returned different canonical identity")
        payload = self._terminal_result(result)
        encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        if len(encoded) > self.MAX_RESPONSE_BYTES:
            raise ProviderTerminalBrokerError("provider terminal response exceeds bound")
        self._assert_no_provider_secret(encoded)
        conn.sendall(encoded)

    def _serve(self) -> None:
        server = self._server
        if server is None:
            return
        while not self._stopping.is_set():
            try:
                conn, _ = server.accept()
            except OSError:
                if self._stopping.is_set():
                    return
                raise
            with conn:
                try:
                    self._handle(conn)
                except Exception as exc:
                    failure = {"ok": False, "error_type": type(exc).__name__}
                    encoded = (json.dumps(failure, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                    try:
                        conn.sendall(encoded)
                    except OSError:
                        pass

    def start(self) -> None:
        if self._server is not None:
            raise ProviderTerminalBrokerError("provider broker already started")
        if not hasattr(socket, "SO_PEERCRED"):
            raise ProviderTerminalBrokerError("SO_PEERCRED unavailable")
        self.socket_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.socket_path.parent.is_symlink() or not self.socket_path.parent.is_dir():
            raise ProviderTerminalBrokerError("provider broker directory invalid")
        try:
            current = os.lstat(self.socket_path)
        except FileNotFoundError:
            current = None
        if current is not None:
            if not stat.S_ISSOCK(current.st_mode):
                raise ProviderTerminalBrokerError("provider broker path occupied by non-socket")
            self.socket_path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(self.socket_path))
            os.chmod(self.socket_path, 0o600)
            server.listen(8)
        except Exception:
            server.close()
            try:
                self.socket_path.unlink()
            except FileNotFoundError:
                pass
            raise
        self._server = server
        self._stopping.clear()
        self._thread = threading.Thread(target=self._serve, name="clayverse-provider-terminal-broker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        server, self._server = self._server, None
        if server is not None:
            try:
                server.close()
            except OSError:
                pass
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
