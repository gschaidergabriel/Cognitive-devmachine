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

    def __init__(self, state_root, workspace):
        self.peers = []
        self.__class__.instances.append(self)

    def attach_pty(self, user_id):
        server, peer = socket.socketpair()
        fd = server.detach()
        peer.settimeout(2)
        self.peers.append(peer)
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
    def __init__(self, claims_by_token):
        self.claims_by_token = claims_by_token

    def verify(self, token):
        return dict(self.claims_by_token[token])


def _app(monkeypatch, claims_by_token):
    monkeypatch.setattr(gateway, "IdentityRouter", _IdentityRouter)
    monkeypatch.setattr(gateway, "TerminalSessionManager", _TerminalSessionManager)
    _TerminalSessionManager.instances.clear()
    return gateway.create_terminal_app(
        db=object(),
        clerk_map={"user_g": "gabriel"},
        verifier=_Verifier(claims_by_token),
        state_root="/tmp/clayverse-test-state",
        publishable_key="pk_test_browser_gate",
        frontend_api_url="https://clerk.invalid",
    )


def test_same_clerk_session_can_refresh_and_continue_pty_input(monkeypatch):
    monkeypatch.setattr(gateway.time, "time", lambda: 100.0)
    app = _app(monkeypatch, {
        "initial": {"sub": "user_g", "sid": "clerk_s1", "exp": 110},
        "refresh": {"sub": "user_g", "sid": "clerk_s1", "exp": 120},
    })

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            websocket.send_text(json.dumps({
                "type": "auth",
                "token": "initial",
                "rows": 24,
                "cols": 80,
            }))
            ready = websocket.receive_json()
            assert ready == {
                "type": "ready",
                "user_id": "gabriel",
                "session_id": "session:gabriel",
                "auth_expires_at": 110,
            }

            websocket.send_text(json.dumps({"type": "reauth", "token": "refresh"}))
            assert websocket.receive_json() == {
                "type": "reauthenticated",
                "auth_expires_at": 120,
            }

            websocket.send_bytes(b"hello")
            peer = _TerminalSessionManager.instances[-1].peers[-1]
            assert peer.recv(5) == b"hello"


def test_reauth_rejects_clerk_session_swap(monkeypatch):
    monkeypatch.setattr(gateway.time, "time", lambda: 100.0)
    app = _app(monkeypatch, {
        "initial": {"sub": "user_g", "sid": "clerk_s1", "exp": 110},
        "wrong": {"sub": "user_g", "sid": "clerk_s2", "exp": 120},
    })

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            websocket.send_text(json.dumps({
                "type": "auth",
                "token": "initial",
                "rows": 24,
                "cols": 80,
            }))
            assert websocket.receive_json()["type"] == "ready"
            websocket.send_text(json.dumps({"type": "reauth", "token": "wrong"}))
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "changed session" in error["message"]


def test_unrenewed_clerk_lease_expires_live_websocket(monkeypatch):
    monkeypatch.setattr(gateway.time, "time", lambda: 100.0)
    app = _app(monkeypatch, {
        "short": {"sub": "user_g", "sid": "clerk_s1", "exp": 100.05},
    })

    with TestClient(app) as client:
        with client.websocket_connect("/ws/terminal") as websocket:
            websocket.send_text(json.dumps({
                "type": "auth",
                "token": "short",
                "rows": 24,
                "cols": 80,
            }))
            assert websocket.receive_json()["type"] == "ready"
            error = websocket.receive_json()
            assert error["type"] == "error"
            assert "expired" in error["message"]
