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

    def __init__(self, state_root, workspace):
        self.peers = []
        self.resize_calls = []
        self.__class__.instances.append(self)

    def attach_pty(self, user_id):
        server, peer = socket.socketpair()
        fd = server.detach()
        peer.settimeout(2)
        self.peers.append(peer)
        self.clock[0] = 111.0
        return 123, fd, SimpleNamespace(session_id=f"session:{user_id}")

    def resize(self, fd, rows, cols):
        self.resize_calls.append((fd, rows, cols))

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


def test_expiry_during_blocking_attach_cannot_mutate_terminal_size(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(gateway.time, "time", lambda: clock[0])
    monkeypatch.setattr(gateway, "IdentityRouter", _IdentityRouter)
    monkeypatch.setattr(gateway, "TerminalSessionManager", _TerminalSessionManager)
    _TerminalSessionManager.instances.clear()
    _TerminalSessionManager.clock = clock

    app = gateway.create_terminal_app(
        db=object(),
        clerk_map={"user_g": "gabriel"},
        verifier=_Verifier(),
        state_root="/tmp/clayverse-test-state",
        publishable_key="pk_test_browser_gate",
        frontend_api_url="https://clerk.invalid",
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            websocket.send_text(json.dumps({
                "type": "auth",
                "token": "initial",
                "rows": 24,
                "cols": 80,
            }))
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "expired" in error["message"]

    manager = _TerminalSessionManager.instances[-1]
    assert manager.resize_calls == []
