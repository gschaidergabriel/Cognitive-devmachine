import json
import os
import socket
from types import SimpleNamespace

from fastapi.testclient import TestClient

import clayverse.terminal_gateway as gateway


class _IdentityRouter:
    def __init__(self, db, clerk_map):
        self.clerk_map = clerk_map

    def resolve(self, subject):
        user_id = self.clerk_map.get(subject)
        if user_id is None:
            raise PermissionError("unmapped subject")
        return user_id, f"session:{user_id}"


class _TerminalSessionManager:
    instances = []
    clock = None
    expire_during_attach = False

    def __init__(self, state_root, workspace):
        self.peers = []
        self.attach_fd = None
        self.__class__.instances.append(self)

    def attach_pty(self, user_id):
        server, peer = socket.socketpair()
        fd = server.detach()
        peer.settimeout(2)
        self.peers.append(peer)
        self.attach_fd = fd
        if self.expire_during_attach:
            self.clock[0] = 111.0
        return 123, fd, SimpleNamespace(session_id=f"session:{user_id}")

    def resize(self, fd, rows, cols):
        return None

    def close_attach(self, pid, fd):
        for peer in self.peers:
            try:
                peer.close()
            except OSError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass


class _Verifier:
    def verify(self, token):
        return {"sub": "user_g", "sid": "clerk_s1", "exp": 110}


def _app(monkeypatch, clock, *, expire_during_attach=False):
    monkeypatch.setattr(gateway.time, "time", lambda: clock[0])
    monkeypatch.setattr(gateway, "IdentityRouter", _IdentityRouter)
    monkeypatch.setattr(gateway, "TerminalSessionManager", _TerminalSessionManager)
    _TerminalSessionManager.instances.clear()
    _TerminalSessionManager.clock = clock
    _TerminalSessionManager.expire_during_attach = expire_during_attach
    return gateway.create_terminal_app(
        db=object(),
        clerk_map={"user_g": "gabriel"},
        verifier=_Verifier(),
        state_root="/tmp/clayverse-test-state",
        publishable_key="pk_test_browser_gate",
        frontend_api_url="https://clerk.invalid",
    )


def _authenticate(websocket):
    websocket.send_text(json.dumps({
        "type": "auth",
        "token": "initial",
        "rows": 24,
        "cols": 80,
    }))


def test_expiry_during_pty_attach_fails_before_ready(monkeypatch):
    clock = [100.0]
    app = _app(monkeypatch, clock, expire_during_attach=True)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            _authenticate(websocket)
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "expired" in error["message"]


def test_pty_output_is_rechecked_after_blocking_read(monkeypatch):
    clock = [100.0]
    app = _app(monkeypatch, clock)
    real_read = os.read

    def expiring_read(fd, size):
        manager = _TerminalSessionManager.instances[-1]
        if fd == manager.attach_fd:
            clock[0] = 111.0
        return real_read(fd, size)

    monkeypatch.setattr(gateway.os, "read", expiring_read)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            _authenticate(websocket)
            assert websocket.receive_json()["type"] == "ready"
            manager = _TerminalSessionManager.instances[-1]
            manager.peers[-1].sendall(b"must-not-cross-expired-lease")
            message = websocket.receive()
            assert message.get("text") is not None, message
            error = json.loads(message["text"])
            assert error["type"] == "error"
            assert "expired" in error["message"]
            assert message.get("bytes") is None
