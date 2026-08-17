import base64
import http.client
import json
import threading

from clayverse.adapters import AuthenticationError
from clayverse.api import ClayVerseAPI


class FakeVerifier:
    def bearer(self, header):
        if not header or not header.startswith("Bearer "):
            raise AuthenticationError("missing bearer token")
        return header.removeprefix("Bearer ")

    def verify(self, token):
        subjects = {
            "token-g": "subject-g",
            "token-a": "subject-a",
            "token-x": "subject-x",
        }
        if token not in subjects:
            raise AuthenticationError("invalid token")
        return {"sub": subjects[token]}


class FakeIdentity:
    def resolve(self, subject):
        mapping = {"subject-g": "gabriel", "subject-a": "andreas"}
        if subject not in mapping:
            raise PermissionError("unmapped Clerk subject")
        user = mapping[subject]
        return user, f"terminal-{user}"


class FakeEngine:
    identity = FakeIdentity()


class FakeTerminal:
    def __init__(self, output=b""):
        self.started = False
        self.output = bytearray(output)
        self.writes = []
        self.exit_status = None

    def start(self):
        self.started = True

    def alive(self):
        return self.started

    def write(self, data):
        if not self.started:
            raise RuntimeError("not running")
        self.writes.append(data)
        return len(data)

    def read(self, max_bytes=65_536):
        data = bytes(self.output[:max_bytes])
        del self.output[:max_bytes]
        return data


class FakeSupervisor:
    def __init__(self):
        self.terminals = {
            "gabriel": FakeTerminal(b"g-ready\r\n"),
            "andreas": FakeTerminal(b"a-ready\r\n"),
        }
        self.lookups = []

    def for_user(self, user_id):
        self.lookups.append(user_id)
        return self.terminals[user_id]


def _request(server, method, path, *, token=None, payload=None):
    headers = {}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload)
    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    data = json.loads(response.read())
    conn.close()
    return response.status, data


def test_browser_terminal_is_bearer_authenticated_and_identity_fenced():
    supervisor = FakeSupervisor()
    api = ClayVerseAPI(FakeEngine(), FakeVerifier(), terminal_supervisor=supervisor)
    server = api.server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, data = _request(server, "POST", "/api/terminal/start", token="token-g")
        assert status == 200
        assert data == {"ok": True, "user_id": "gabriel", "alive": True}
        assert supervisor.lookups == ["gabriel"]

        raw_input = b"hello from browser\n"
        status, data = _request(
            server,
            "POST",
            "/api/terminal/write",
            token="token-g",
            payload={"data_b64": base64.b64encode(raw_input).decode("ascii")},
        )
        assert status == 200
        assert data["written"] == len(raw_input)
        assert supervisor.terminals["gabriel"].writes == [raw_input]
        assert supervisor.terminals["andreas"].writes == []

        status, data = _request(server, "GET", "/api/terminal/read?max_bytes=64", token="token-g")
        assert status == 200
        assert data["user_id"] == "gabriel"
        assert base64.b64decode(data["data_b64"]) == b"g-ready\r\n"

        status, data = _request(server, "POST", "/api/terminal/start", token="token-a")
        assert status == 200
        assert data["user_id"] == "andreas"
        assert supervisor.lookups[-1] == "andreas"

        status, data = _request(server, "POST", "/api/terminal/start", token="token-x")
        assert status == 403
        assert data == {"error": "forbidden"}

        status, data = _request(server, "POST", "/api/terminal/start")
        assert status == 401
        assert data == {"error": "unauthorized"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
