import signal
import sys

from clayverse import service


class FakeDB:
    def __init__(self):
        self.checkpoints = []
        self.closed = False

    def checkpoint(self, label):
        self.checkpoints.append(label)
        return f"cp-{label}", f"hash-{label}"

    def close(self):
        self.closed = True


class FakeInference:
    def available(self):
        return True


class FakeTerminalSupervisor:
    def __init__(self):
        self.stopped = False

    def stop_all(self):
        self.stopped = True


class FakeServer:
    def __init__(self, handlers):
        self.handlers = handlers
        self.timeout = None
        self.closed = False
        self.handle_calls = 0

    def handle_request(self):
        self.handle_calls += 1
        self.handlers[signal.SIGTERM]()

    def server_close(self):
        self.closed = True


class FakeAPI:
    def __init__(self, server):
        self._server = server
        self.server_calls = []

    def server(self, host, port):
        self.server_calls.append((host, port))
        return self._server


def test_service_uses_clayverse_api_serial_server(monkeypatch, tmp_path):
    db = FakeDB()
    handlers = {}
    fake_server = FakeServer(handlers)
    fake_api = FakeAPI(fake_server)
    terminals = FakeTerminalSupervisor()
    api_kwargs = {}

    monkeypatch.setattr(service, "UnifiedDB", lambda _path: db)
    monkeypatch.setattr(service, "IdentityRouter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(service, "ClayGraphProjection", lambda *_args, **_kwargs: type("G", (), {"rebuild": lambda self: None})())
    monkeypatch.setattr(service.ClerkConfig, "from_env", lambda: object())
    monkeypatch.setattr(service, "ClerkTokenVerifier", lambda _cfg: object())
    monkeypatch.setattr(service, "ClaudeCodeInference", lambda: FakeInference())
    monkeypatch.setattr(service, "ClayVerseEngine", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(service, "TerminalSupervisor", lambda: terminals)

    def make_api(*_args, **kwargs):
        api_kwargs.update(kwargs)
        return fake_api

    monkeypatch.setattr(service, "ClayVerseAPI", make_api)
    monkeypatch.setattr(service.signal, "signal", lambda sig, fn: handlers.__setitem__(sig, fn))
    monkeypatch.setattr(sys, "argv", ["clayverse.service"])

    monkeypatch.setenv("CLAYVERSE_STATE_ROOT", str(tmp_path / "state"))
    monkeypatch.setenv("CLAYVERSE_CLERK_MAP_JSON", '{"subject-g":"gabriel","subject-a":"andreas"}')
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_test_example")
    monkeypatch.setenv("CLERK_FRONTEND_API_URL", "https://clerk.example")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "43210")

    assert service.main() == 0
    assert fake_api.server_calls == [("127.0.0.1", 43210)]
    assert api_kwargs["terminal_supervisor"] is terminals
    assert fake_server.handle_calls == 1
    assert fake_server.timeout == 1.0
    assert fake_server.closed is True
    assert terminals.stopped is True
    assert db.checkpoints == ["boot", "shutdown"]
    assert db.closed is True
